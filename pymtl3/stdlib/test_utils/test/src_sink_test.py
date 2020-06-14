"""
========================================================================
src_sink_test
========================================================================
Tests for test sources and test sinks.

Author : Yanghui Ou
  Date : Mar 11, 2019
"""
import pytest

from pymtl3 import *

from ..test_helpers import run_sim
from ..test_sinks import PyMTLTestSinkError, TestSinkCL, TestSinkRTL
from ..test_srcs import TestSrcCL, TestSrcRTL

#-------------------------------------------------------------------------
# TestHarnessSimple
#-------------------------------------------------------------------------
# Test a single pair of test src/sink.

class TestHarnessSimple( Component ):

  def construct( s, MsgType, SrcType, SinkType, src_msgs, sink_msgs ):

    s.src  = SrcType ( MsgType, src_msgs  )
    s.sink = SinkType( MsgType, sink_msgs )

    connect( s.src.send, s.sink.recv  )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{} > {}".format( s.src.line_trace(), s.sink.line_trace() )

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

def test_cl_no_delay():
  msgs  = [ Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ) ]
  th = TestHarnessSimple( Bits16, TestSrcCL, TestSinkCL, msgs, msgs )
  run_sim( th )

# int_msgs = [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ]
bit_msgs = [ Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ),
             Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ),
             Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ) ]

arrival0 = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 ]
arrival1 = [ 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21 ]
arrival2 = [ 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33 ]
arrival3 = [ 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33 ]
arrival4 = [ 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60 ]

@pytest.mark.parametrize(
  ('Type', 'msgs', 'src_init',  'src_intv',
   'sink_init', 'sink_intv', 'arrival_time' ),
  [
    ( Bits16, bit_msgs,  0,  0, 0, 0, arrival0 ),
    # ( int,    int_msgs, 10,  0, 0, 0, arrival1 ),
    ( Bits16, bit_msgs, 10,  1, 0, 0, arrival2 ),
    ( Bits16, bit_msgs, 10,  0, 0, 1, arrival3 ),
    ( Bits16, bit_msgs,  3,  4, 5, 3, arrival4 )
  ]
)
def test_src_sink_cl( Type, msgs, src_init,  src_intv,
                      sink_init, sink_intv, arrival_time ):
  th = TestHarnessSimple( Type, TestSrcCL, TestSinkCL, msgs, msgs )
  th.set_param( "top.src.construct",
    initial_delay  = src_init,
    interval_delay = src_intv,
  )
  th.set_param( "top.sink.construct",
    initial_delay  = sink_init,
    interval_delay = sink_intv,
    arrival_time   = arrival_time,
  )
  run_sim( th )

@pytest.mark.parametrize(
  ('Type', 'msgs', 'src_init',  'src_intv',
   'sink_init', 'sink_intv', 'arrival_time' ),
  [
    ( Bits16, bit_msgs,  0,  0, 0, 0, arrival0 ),
    # ( int,    int_msgs, 10,  0, 0, 0, arrival1 ),
    ( Bits16, bit_msgs, 10,  1, 0, 0, arrival2 ),
    ( Bits16, bit_msgs, 10,  0, 0, 1, arrival3 ),
    ( Bits16, bit_msgs,  3,  4, 5, 3, arrival4 )
  ]
)
def test_src_sink_rtl( Type, msgs, src_init,  src_intv,
                       sink_init, sink_intv, arrival_time ):
  th = TestHarnessSimple( Type, TestSrcRTL, TestSinkRTL, msgs, msgs )
  th.set_param( "top.src.construct",
    initial_delay  = src_init,
    interval_delay = src_intv,
  )
  th.set_param( "top.sink.construct",
    initial_delay  = sink_init,
    interval_delay = sink_intv,
    arrival_time   = arrival_time,
  )
  run_sim( th )

#-------------------------------------------------------------------------
# Adaptive composition test
#-------------------------------------------------------------------------
# This test attempts to mix-and-match different levels of test srcs and
# sinks for all possible combinations -- cl/cl, rtl/cl, cl/rtl, rtl/rtl.
# It also creates multiple src/sink pairs to stress the management of
# multiple instances of the same adapter class

class TestHarness( Component ):

  def construct( s, src_level, sink_level, MsgType, src_msgs, sink_msgs,
                 src_init, src_intv,
                 sink_init, sink_interval, arrival_time=None ):
    s.num_pairs = 2

    if src_level == 'cl':
      s.srcs = [ TestSrcCL ( MsgType, src_msgs, src_init, src_intv )
                  for i in range(s.num_pairs) ]
    elif src_level == 'rtl':
      s.srcs = [ TestSrcRTL( MsgType, src_msgs, src_init, src_intv )
                  for i in range(s.num_pairs) ]
    else:
      raise

    if sink_level == 'cl':
      s.sinks = [ TestSinkCL( MsgType, sink_msgs, sink_init, sink_interval, arrival_time )
                  for i in range(s.num_pairs) ]
    elif sink_level == 'rtl':
      s.sinks = [ TestSinkRTL( MsgType, sink_msgs, sink_init, sink_interval, arrival_time )
                  for i in range(s.num_pairs) ]
    else:
      raise

    # Connections
    for i in range(s.num_pairs):
      connect( s.srcs[i].send, s.sinks[i].recv )

  def done( s ):
    for i in range(s.num_pairs):
      if not s.srcs[i].done() or not s.sinks[i].done():
        return False
    return True

  def line_trace( s ):
    return "{} >>> {}".format( "|".join( [ x.line_trace() for x in s.srcs ] ),
                               "|".join( [ x.line_trace() for x in s.sinks ] ) )

test_case_table = []
for src in ['cl', 'rtl']:
  for sink in ['cl', 'rtl']:
    test_case_table += [
      ( src, sink, bit_msgs,  0,  0, 0, 0, arrival0 ),
      # ( src, sink, int_msgs, 10,  0, 0, 0, arrival1 ),
      ( src, sink, bit_msgs, 10,  1, 0, 0, arrival2 ),
      ( src, sink, bit_msgs, 10,  0, 0, 1, arrival3 ),
      ( src, sink, bit_msgs,  3,  4, 5, 3, arrival4 ),
    ]

@pytest.mark.parametrize(
  ('src_level', 'sink_level', 'msgs',
   'src_init',  'src_intv', 'sink_init', 'sink_intv', 'arrival_time' ),
  test_case_table,
)
def test_adaptive( src_level, sink_level, msgs, src_init,  src_intv,
                        sink_init, sink_intv, arrival_time ):
  th = TestHarness( src_level, sink_level, Bits16, msgs, msgs,
                    src_init,  src_intv, sink_init,
                    sink_intv, arrival_time )
  run_sim( th )

#-------------------------------------------------------------------------
# Error message test
#-------------------------------------------------------------------------

def test_error_more_msg():
  try:
    th = TestHarnessSimple(
      Bits16, TestSrcCL, TestSinkCL,
      src_msgs  = [ b16(0xface), b16(0xface) ],
      sink_msgs = [ b16(0xface) ],
    )
    run_sim( th )
  except PyMTLTestSinkError as e:
    return
  raise Exception( 'Failed to detect error!' )

def test_error_wrong_msg():
  try:
    th = TestHarnessSimple(
      Bits16, TestSrcCL, TestSinkCL,
      src_msgs  = [ b16(0xface), b16(0xface) ],
      sink_msgs = [ b16(0xface), b16(0xdead) ],
    )
    run_sim( th )
  except PyMTLTestSinkError as e:
    return
  raise Exception( 'Fail to detect error!' )

def test_error_late_msg():
  try:
    th = TestHarnessSimple(
      Bits16, TestSrcCL, TestSinkCL,
      src_msgs  = [ b16(0xface), b16(0xface) ],
      sink_msgs = [ b16(0xface), b16(0xdead) ],
    )
    th.set_param( 'top.src.construct', initial_delay=5 )
    th.set_param( 'top.sink.construct', arrival_time=[1,2] )
    run_sim( th )
  except PyMTLTestSinkError as e:
    return
  raise Exception( 'Fail to detect error!')

#-------------------------------------------------------------------------
# Customized compare function test
#-------------------------------------------------------------------------

def test_customized_cmp():
  th = TestHarnessSimple(
    Bits4, TestSrcCL, TestSinkCL,
    src_msgs  = [ b4(0b1110), b4(0b1111) ],
    sink_msgs = [ b4(0b0010), b4(0b0011) ],
  )
  th.set_param( 'top.sink.construct', cmp_fn=lambda a, b: a[0:2] == b[0:2] )
  run_sim( th )
