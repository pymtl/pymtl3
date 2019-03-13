#=========================================================================
# src_sink_test 
#=========================================================================
# Tests for test sources and test sinks.
#
# Author : Yanghui Ou
#   Date : Mar 11, 2019

import pytest

from pymtl import *
from pymtl.dsl.ComponentLevel6 import method_port, ComponentLevel6
from pymtl.dsl.test.sim_utils import simple_sim_pass
from test_srcs  import TestSrcCL, TestSrcRTL
from test_sinks import TestSinkCL, TestSinkRTL

#-------------------------------------------------------------------------
# TestHarnessCL
#-------------------------------------------------------------------------

class TestHarnessCL( ComponentLevel6 ):
  
  def construct( s, src_msgs, sink_msgs, src_initial,  src_interval, 
                                         sink_initial, sink_interval  ):
   
    s.src     = TestSrcCL ( src_msgs,  src_initial,  src_interval  )
    s.sink    = TestSinkCL( sink_msgs, sink_initial, sink_interval )

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
  
  def construct( s, MsgType, src_msgs, sink_msgs, 
                    src_initial,  src_interval, 
                    sink_initial, sink_interval  ):
   
    s.src     = TestSrcRTL ( MsgType, src_msgs,  
                             src_initial,  src_interval  )
    s.sink    = TestSinkRTL( MsgType, sink_msgs, 
                             sink_initial, sink_interval )

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
  th = TestHarnessCL( msgs, msgs, 0, 0, 0, 0 )
  run_sim( th )

int_msgs = [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ]
bit_msgs = [ Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ),
             Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ),
             Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ) ]

@pytest.mark.parametrize(
  ('msgs', 'src_init_delay',  'src_inter_delay', 
          'sink_init_delay', 'sink_inter_delay' ),
  [
    ( bit_msgs,  0,  0, 0, 0 ),
    ( int_msgs, 10,  0, 0, 0 ),
    ( bit_msgs, 10,  1, 0, 0 ),
    ( bit_msgs, 10,  0, 0, 1 ),
    ( bit_msgs,  3,  4, 5, 3 )
  ]
)
def test_src_sink_cl( msgs, src_init_delay,  src_inter_delay, 
                        sink_init_delay, sink_inter_delay ):
  th = TestHarnessCL( msgs, msgs, src_init_delay,  src_inter_delay, 
                                sink_init_delay, sink_inter_delay )
  run_sim( th )

@pytest.mark.parametrize(
  ('msgs', 'src_init_delay',  'src_inter_delay', 
          'sink_init_delay', 'sink_inter_delay' ),
  [
    ( bit_msgs,  0,  0, 0, 0 ),
    ( int_msgs, 10,  0, 0, 0 ),
    ( bit_msgs, 10,  1, 0, 0 ),
    ( bit_msgs, 10,  0, 0, 1 ),
    ( bit_msgs,  3,  4, 5, 3 )
  ]
)
def test_src_sink_rtl( msgs, src_init_delay,  src_inter_delay, 
                        sink_init_delay, sink_inter_delay ):
  th = TestHarnessRTL( Bits16, msgs, msgs, src_init_delay,  src_inter_delay, 
                                sink_init_delay, sink_inter_delay )
  run_sim( th )