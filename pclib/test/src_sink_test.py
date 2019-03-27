#=========================================================================
# src_sink_test
#=========================================================================
# Tests for test sources and test sinks.
#
# Author : Yanghui Ou
#   Date : Mar 11, 2019

import pytest

from pymtl import *
from pymtl.dsl.test.sim_utils import simple_sim_pass
from test_srcs  import TestSrcCL, TestSrcRTL
from test_sinks import TestSinkCL, TestSinkRTL

#-------------------------------------------------------------------------
# TestHarnessCL
#-------------------------------------------------------------------------

class TestHarnessCL( ComponentLevel6 ):

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

class TestHarnessRTL( ComponentLevel6 ):

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

  th.elaborate()
  th.apply( simple_sim_pass )

  # Run simluation

  print ""
  ncycles = 0
  print "{}:{}".format( ncycles, th.line_trace() )
  while not th.done() and ncycles < max_cycles:
    th.tick()
    ncycles += 1
    print "{}:{}".format( ncycles, th.line_trace() )

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
