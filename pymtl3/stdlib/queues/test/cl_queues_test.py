"""
========================================================================
Tests for CL queues
========================================================================

Author: Yanghui Ou
  Date: Mar 20, 2019
"""
import pytest

from pymtl3 import *
from pymtl3.stdlib.test_utils import TestSinkCL, TestSrcCL, run_sim

from ..cl_queues import BypassQueueCL, NormalQueueCL, PipeQueueCL

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, MsgType, DutType, src_msgs, sink_msgs ):

    s.src     = TestSrcCL ( MsgType, src_msgs )
    s.dut     = DutType()
    s.sink    = TestSinkCL( MsgType, sink_msgs )

    connect( s.src.send, s.dut.enq )

    @update_once
    def up_deq_send():
      if s.dut.deq.rdy() and s.sink.recv.rdy():
        s.sink.recv( s.dut.deq() )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{} ({}) {}".format(
      s.src.line_trace(), s.dut.line_trace(), s.sink.line_trace() )

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

test_msgs = [ Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ) ]

arrival_pipe   = [ 2, 3, 4, 5 ]
arrival_bypass = [ 1, 2, 3, 4 ]
arrival_normal = [ 2, 4, 6, 8 ]

def test_pipe_simple():
  th = TestHarness( Bits16, PipeQueueCL, test_msgs, test_msgs )
  th.set_param( "top.dut.construct", num_entries=1 )
  th.set_param( "top.sink.construct", arrival_time=arrival_pipe )
  run_sim( th )

def test_bypass_simple():
  th = TestHarness( Bits16, BypassQueueCL, test_msgs, test_msgs )
  th.set_param( "top.dut.construct", num_entries=1 )
  th.set_param( "top.sink.construct", arrival_time=arrival_bypass )
  run_sim( th )

def test_normal_simple():
  th = TestHarness( Bits16, NormalQueueCL, test_msgs, test_msgs )
  th.set_param( "top.dut.construct", num_entries=1 )
  th.set_param( "top.sink.construct", arrival_time=arrival_normal )
  run_sim( th )

def test_normal2_simple():
  th = TestHarness( Bits16, NormalQueueCL, test_msgs, test_msgs )
  th.set_param( "top.dut.construct", num_entries=2 )
  th.set_param( "top.sink.construct", arrival_time=arrival_pipe )
  run_sim( th )

@pytest.mark.parametrize(
  ( 'QType', 'qsize', 'src_init', 'src_intv',
    'sink_init', 'sink_intv', 'arrival_time' ),
  [
    ( PipeQueueCL,   2, 1, 1, 0, 0, [ 3, 5,  7,  9 ] ),
    ( BypassQueueCL, 1, 0, 4, 3, 1, [ 3, 6, 11, 16 ] ),
    ( NormalQueueCL, 1, 0, 0, 5, 0, [ 5, 7,  9, 11 ] )
  ]
)
def test_delay( QType, qsize, src_init, src_intv,
                sink_init, sink_intv, arrival_time ):
  th = TestHarness( Bits16, QType, test_msgs, test_msgs )
  th.set_param( "top.src.construct",
    initial_delay  = src_init,
    interval_delay = src_intv,
  )
  th.set_param( "top.dut.construct", num_entries=qsize )
  th.set_param( "top.sink.construct",
    initial_delay  = sink_init,
    interval_delay = sink_intv,
    arrival_time   = arrival_time,
  )
  run_sim( th )
