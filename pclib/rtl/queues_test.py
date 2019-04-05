#=========================================================================
# Tests for CL queues
#=========================================================================
#
# Author: Yanghui Ou
#   Date: Mar 24, 2019

import pytest

from pymtl                    import *
from pymtl.dsl.test.sim_utils import simple_sim_pass
from pclib.test.test_srcs     import TestSrcRTL
from pclib.test.test_sinks    import TestSinkRTL
from pclib.test               import TestVectorSimulator
from pymtl.passes.PassGroups  import SimpleCLSim
from queues import NormalQueueRTL

#-------------------------------------------------------------------------
# TestVectorSimulator test
#-------------------------------------------------------------------------

def run_tv_test( dut, test_vectors ):

  # Define input/output functions

  def tv_in( dut, tv ):
    dut.enq.en  = tv[0]
    dut.enq.msg = tv[2]
    dut.deq.en  = tv[3]

  def tv_out( dut, tv ):
    if tv[1] != '?': assert dut.enq.rdy == tv[1]
    if tv[4] != '?': assert dut.deq.rdy == tv[4]
    if tv[5] != '?': assert dut.deq.msg == tv[5]

  # Run the test

  sim = TestVectorSimulator( dut, test_vectors, tv_in, tv_out )
  sim.run_test()

def test_pipe_Bits():

  B1  = mk_bits(1)
  B32 = mk_bits(32)
  run_tv_test( NormalQueueRTL( Bits32, 2 ), [
    #  enq.en  enq.rdy enq.msg   deq.en  deq.rdy deq.msg
    [  B1(1),  B1(1),  B32(123), B1(0),  B1(0),    '?'    ],
    [  B1(1),  B1(1),  B32(345), B1(0),  B1(1),  B32(123) ],
    [  B1(0),  B1(0),  B32(567), B1(0),  B1(1),  B32(123) ],
    [  B1(0),  B1(0),  B32(567), B1(1),  B1(1),  B32(123) ],
    [  B1(0),  B1(1),  B32(567), B1(1),  B1(1),  B32(345) ],
    [  B1(1),  B1(1),  B32(567), B1(0),  B1(0),    '?'    ],
    [  B1(1),  B1(1),  B32(0  ), B1(1),  B1(1),  B32(567) ],
    [  B1(1),  B1(1),  B32(1  ), B1(1),  B1(1),  B32(0  ) ],
    [  B1(1),  B1(1),  B32(2  ), B1(1),  B1(1),  B32(1  ) ],
    [  B1(0),  B1(1),  B32(2  ), B1(1),  B1(1),  B32(2  ) ],
] )

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, MsgType, qsize, src_msgs, sink_msgs, src_initial, 
                 src_interval, sink_initial, sink_interval, 
                 arrival_time=None ):

    s.src  = TestSrcRTL ( MsgType, src_msgs,  src_initial,  src_interval )
    s.dut  = NormalQueueRTL( MsgType, qsize )
    s.sink = TestSinkRTL( MsgType, sink_msgs, sink_initial, sink_interval, 
                          arrival_time )
    
    s.connect( s.src.send,    s.dut.enq       )
    s.connect( s.dut.deq.msg, s.sink.recv.msg )

    @s.update
    def up_deq_send():
      if s.dut.deq.rdy and s.sink.recv.rdy:
        s.dut.deq.en   = Bits1( 1 )
        s.sink.recv.en = Bits1( 1 )
      else:
        s.dut.deq.en   = Bits1( 0 )
        s.sink.recv.en = Bits1( 0 )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{} ({}) {}".format( 
      s.src.line_trace(), s.dut.line_trace(), s.sink.line_trace() )

#-------------------------------------------------------------------------
# run_sim 
#-------------------------------------------------------------------------

def run_sim( th, max_cycles=100 ):

  # Create a simulator
  # th.elaborate()
  # th.apply( simple_sim_pass )
  th.apply( SimpleCLSim )
  th.sim_reset()

  print ""
  ncycles = 0
  print "{:2}:{}".format( ncycles, th.line_trace() )
  while not th.done() and ncycles < max_cycles:
    th.tick()
    ncycles += 1
    print "{:2}:{}".format( ncycles, th.line_trace() )
  
  # Check timeout

  assert ncycles < max_cycles

  th.tick()
  th.tick()
  th.tick()

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

test_msgs = [ Bits16( 4 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ) ]

arrival_pipe   = [ 2, 3, 4, 5 ]

def test_normal2_simple():
  th = TestHarness( Bits16, 2, test_msgs, test_msgs, 0, 0, 0, 0,
                    arrival_pipe )
  run_sim( th )
