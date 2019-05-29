"""
========================================================================
src_sink_test
========================================================================
Tests for test sources and test sinks.

Author : Yanghui Ou
  Date : Mar 11, 2019
"""
from __future__ import absolute_import, division, print_function

import pytest

from pymtl3 import *

from .test_sinks import TestSinkCL, TestSinkRTL
from .test_srcs import TestSrcCL, TestSrcRTL

#-------------------------------------------------------------------------
# TestHarnessCL
#-------------------------------------------------------------------------

class TestHarnessCL( Component ):

  def construct( s, src_msgs, sink_msgs, src_initial,  src_interval,
                 sink_initial, sink_interval, arrival_time=None ):

    s.src  = TestSrcCL ( src_msgs,  src_initial,  src_interval  )
    s.sink = TestSinkCL( sink_msgs, sink_initial, sink_interval,
                            arrival_time )

    # Connections
    s.connect( s.src.send, s.sink.recv  )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{} -> {}".format(
      s.src.line_trace(), s.sink.line_trace() )

#-------------------------------------------------------------------------
# TestHarnessRTL
#-------------------------------------------------------------------------

class TestHarnessRTL( Component ):

  def construct( s, MsgType, src_msgs, sink_msgs, src_initial,
                 src_interval, sink_initial, sink_interval,
                 arrival_time=None  ):

    s.src     = TestSrcRTL ( MsgType, src_msgs,
                             src_initial,  src_interval  )
    s.sink    = TestSinkRTL( MsgType, sink_msgs,
                             sink_initial, sink_interval, arrival_time )

    # Connections
    s.connect( s.src.send, s.sink.recv  )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{} -> {}".format(
      s.src.line_trace(), s.sink.line_trace() )

#-------------------------------------------------------------------------
# run_sim
#-------------------------------------------------------------------------

def run_sim( th, max_cycles=100 ):

  # Create a simulator

  th.apply( SimpleSim )

  # Run simluation

  print("")
  ncycles = 0
  print("{:2}:{}".format( ncycles, th.line_trace() ))
  while not th.done() and ncycles < max_cycles:
    th.tick()
    ncycles += 1
    print("{:2}:{}".format( ncycles, th.line_trace() ))

  # Check timeout

  assert ncycles < max_cycles

  th.tick()
  th.tick()
  th.tick()

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

def test_cl_no_delay():
  msgs  = [ Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ) ]
  th = TestHarnessCL( msgs, msgs, 0, 0, 0, 0, [ 1, 2, 3, 4 ] )
  run_sim( th )

int_msgs = [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ]
bit_msgs = [ Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ),
             Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ),
             Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ) ]

arrival0 = [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 ]
arrival1 = [ 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21 ]
arrival2 = [ 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33 ]
arrival3 = [ 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33 ]
arrival4 = [ 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60 ]

@pytest.mark.parametrize(
  ('msgs', 'src_init_delay',  'src_inter_delay',
   'sink_init_delay', 'sink_inter_delay', 'arrival_time' ),
  [
    ( bit_msgs,  0,  0, 0, 0, arrival0 ),
    ( int_msgs, 10,  0, 0, 0, arrival1 ),
    ( bit_msgs, 10,  1, 0, 0, arrival2 ),
    ( bit_msgs, 10,  0, 0, 1, arrival3 ),
    ( bit_msgs,  3,  4, 5, 3, arrival4 )
  ]
)
def test_src_sink_cl( msgs, src_init_delay,  src_inter_delay,
                      sink_init_delay, sink_inter_delay, arrival_time ):
  th = TestHarnessCL( msgs, msgs, src_init_delay,  src_inter_delay,
                      sink_init_delay, sink_inter_delay, arrival_time )
  run_sim( th )

@pytest.mark.parametrize(
  ('msgs', 'src_init_delay',  'src_inter_delay',
          'sink_init_delay', 'sink_inter_delay', 'arrival_time' ),
  [
    ( bit_msgs,  0,  0, 0, 0, arrival0 ),
    ( int_msgs, 10,  0, 0, 0, arrival1 ),
    ( bit_msgs, 10,  1, 0, 0, arrival2 ),
    ( bit_msgs, 10,  0, 0, 1, arrival3 ),
    ( bit_msgs,  3,  4, 5, 3, arrival4 )
  ]
)
def test_src_sink_rtl( msgs, src_init_delay,  src_inter_delay,
                        sink_init_delay, sink_inter_delay, arrival_time ):
  th = TestHarnessRTL( Bits16, msgs, msgs, src_init_delay,  src_inter_delay,
                       sink_init_delay, sink_inter_delay, arrival_time )
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
                 src_initial, src_interval,
                 sink_initial, sink_interval, arrival_time=None ):
    s.num_pairs = 2

    if src_level == 'cl':
      s.srcs = [ TestSrcCL ( src_msgs, src_initial, src_interval )
                  for i in range(s.num_pairs) ]
    elif src_level == 'rtl':
      s.srcs = [ TestSrcRTL( MsgType, src_msgs, src_initial, src_interval )
                  for i in range(s.num_pairs) ]
    else:
      raise

    if sink_level == 'cl':
      s.sinks = [ TestSinkCL( sink_msgs, sink_initial, sink_interval, arrival_time )
                  for i in range(s.num_pairs) ]
    elif sink_level == 'rtl':
      s.sinks = [ TestSinkRTL( MsgType, sink_msgs, sink_initial, sink_interval, arrival_time )
                  for i in range(s.num_pairs) ]
    else:
      raise

    # Connections
    for i in range(s.num_pairs):
      s.connect( s.srcs[i].send, s.sinks[i].recv )

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
      ( src, sink, int_msgs, 10,  0, 0, 0, arrival1 ),
      ( src, sink, bit_msgs, 10,  1, 0, 0, arrival2 ),
      ( src, sink, bit_msgs, 10,  0, 0, 1, arrival3 ),
      ( src, sink, bit_msgs,  3,  4, 5, 3, arrival4 ),
    ]

@pytest.mark.parametrize(
  ('src_level', 'sink_level', 'msgs',
   'src_init_delay',  'src_inter_delay', 'sink_init_delay', 'sink_inter_delay', 'arrival_time' ),
  test_case_table,
)
def test_adaptive( src_level, sink_level, msgs, src_init_delay,  src_inter_delay,
                        sink_init_delay, sink_inter_delay, arrival_time ):
  th = TestHarness( src_level, sink_level, Bits16, msgs, msgs,
                    src_init_delay,  src_inter_delay, sink_init_delay,
                    sink_inter_delay, arrival_time )
  run_sim( th )
