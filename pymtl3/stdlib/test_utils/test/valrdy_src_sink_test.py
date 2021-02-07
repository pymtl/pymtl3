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
from ..valrdy_test_sinks import PyMTLTestSinkError, TestSinkRTL
from ..valrdy_test_srcs import TestSrcRTL

#-------------------------------------------------------------------------
# TestHarnessSimple
#-------------------------------------------------------------------------
# Test a single pair of test src/sink.

class TestHarnessSimple( Component ):

  def construct( s, MsgType, SrcType, SinkType, src_msgs, sink_msgs ):

    s.src  = SrcType ( MsgType, src_msgs  )
    s.sink = SinkType( MsgType, sink_msgs )

    s.src.out //= s.sink.in_

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{} > {}".format( s.src.line_trace(), s.sink.line_trace() )

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------
bit_msgs = [ Bits16( 10 ), Bits16( 11 ), Bits16( 12 ), Bits16( 13 ),
             Bits16( 10 ), Bits16( 11 ), Bits16( 12 ), Bits16( 13 ),
             Bits16( 10 ), Bits16( 11 ), Bits16( 12 ), Bits16( 13 ) ]

arrival0 = [ 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 ]
arrival1 = [ 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23 ]
arrival2 = [ 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34 ]
arrival3 = [ 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34 ]
arrival4 = [ 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59, 64 ]

@pytest.mark.parametrize(
  ('Type', 'msgs', 'src_init',  'src_intv', 'sink_init', 'sink_intv', 'arrival_time' ),
  [
    ( Bits16, bit_msgs,  0,  0, 0, 0, arrival0 ),
    ( Bits16, bit_msgs, 10,  0, 0, 0, arrival1 ),
    ( Bits16, bit_msgs, 10,  1, 0, 0, arrival2 ),
    ( Bits16, bit_msgs, 10,  0, 0, 1, arrival3 ),
    ( Bits16, bit_msgs,  0,  4, 7, 2, arrival4 ),
    ( Bits16, bit_msgs,  7,  2, 0, 4, arrival4 )
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
# Error message test
#-------------------------------------------------------------------------

def test_error_more_msg( cmdline_opts ):
  try:
    th = TestHarnessSimple(
      Bits16, TestSrcRTL, TestSinkRTL,
      src_msgs  = [ b16(0xface), b16(0xface) ],
      sink_msgs = [ b16(0xface) ],
    )
    run_sim( th, { **cmdline_opts, **{'max_cycles':100} } )
  except AssertionError as e:
    print(e)
    return
  raise Exception( 'Failed to detect error!' )

def test_error_wrong_msg():
  try:
    th = TestHarnessSimple(
      Bits16, TestSrcRTL, TestSinkRTL,
      src_msgs  = [ b16(0xface), b16(0xface) ],
      sink_msgs = [ b16(0xface), b16(0xdead) ],
    )
    run_sim( th )
  except PyMTLTestSinkError as e:
    print(e)
    return
  raise Exception( 'Fail to detect error!' )

def test_error_late_msg():
  try:
    th = TestHarnessSimple(
      Bits16, TestSrcRTL, TestSinkRTL,
      src_msgs  = [ b16(0xface), b16(0xface) ],
      sink_msgs = [ b16(0xface), b16(0xdead) ],
    )
    th.set_param( 'top.src.construct', initial_delay=5 )
    th.set_param( 'top.sink.construct', arrival_time=[1,2] )
    run_sim( th )
  except PyMTLTestSinkError as e:
    print(e)
    return
  raise Exception( 'Fail to detect error!')

#-------------------------------------------------------------------------
# Customized compare function test
#-------------------------------------------------------------------------

def test_customized_cmp():
  th = TestHarnessSimple(
    Bits4, TestSrcRTL, TestSinkRTL,
    src_msgs  = [ b4(0b1110), b4(0b1111) ],
    sink_msgs = [ b4(0b0010), b4(0b0011) ],
  )
  th.set_param( 'top.sink.construct', cmp_fn=lambda a, b: a[0:2] == b[0:2] )
  run_sim( th )
