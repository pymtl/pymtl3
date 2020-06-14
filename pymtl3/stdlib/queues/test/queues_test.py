"""
========================================================================
Tests for CL queues
========================================================================

Author: Yanghui Ou
  Date: Mar 24, 2019
"""
from itertools import product

import pytest

from pymtl3 import *
from pymtl3.stdlib.test_utils import TestSinkCL, TestSrcCL, TestVectorSimulator, run_sim

from ..queues import (
    BypassQueue1EntryRTL,
    BypassQueueRTL,
    NormalQueue1EntryRTL,
    NormalQueueRTL,
    PipeQueue1EntryRTL,
    PipeQueueRTL,
)

#-------------------------------------------------------------------------
# TestVectorSimulator test
#-------------------------------------------------------------------------

def run_tv_test( dut, test_vectors ):

  # Define input/output functions

  def tv_in( dut, tv ):
    dut.enq.en  @= tv[0]
    dut.enq.msg @= tv[2]
    dut.deq.en  @= tv[3]

  def tv_out( dut, tv ):
    if tv[1] != '?': assert dut.enq.rdy == tv[1]
    if tv[4] != '?': assert dut.deq.rdy == tv[4]
    if tv[5] != '?': assert dut.deq.ret == tv[5]

  # Run the test

  sim = TestVectorSimulator( dut, test_vectors, tv_in, tv_out )
  sim.run_test()

def test_pipe_Bits():

  B1  = mk_bits(1)
  B32 = mk_bits(32)
  run_tv_test( NormalQueueRTL( Bits32, 2 ), [
    #  enq.en  enq.rdy enq.msg   deq.en  deq.rdy deq.ret
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

  def construct( s, MsgType, QType, src_msgs, sink_msgs ):

    s.src  = TestSrcCL ( MsgType, src_msgs )
    s.dut  = QType( MsgType )

    s.sink = TestSinkCL( MsgType, sink_msgs )

    connect( s.src.send, s.dut.enq )

    @update_once
    def dut2sink():
      s.dut.deq.en @= 0

      if s.dut.deq.rdy and s.sink.recv.rdy():
        s.dut.deq.en @= 1
        s.sink.recv( s.dut.deq.ret )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{} ({}) {}".format(
      s.src.line_trace(), s.dut.line_trace(), s.sink.line_trace() )

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

test_msgs = [ Bits16( 4 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ) ]

arrival_normal = [ 2, 4, 6, 8 ]
arrival_pipe   = [ 2, 3, 4, 5 ]
arrival_bypass = [ 1, 2, 3, 4 ]


def test_normal1_simple():
  th = TestHarness( Bits16, NormalQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", arrival_time = arrival_normal )
  th.set_param( "top.dut.construct", num_entries = 1 )
  run_sim( th )

def test_normal2_simple():
  th = TestHarness( Bits16, NormalQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", arrival_time = arrival_pipe )
  th.set_param( "top.dut.construct", num_entries = 2 )
  run_sim( th )

def test_pipe1_simple():
  th = TestHarness( Bits16, PipeQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", arrival_time = arrival_pipe )
  th.set_param( "top.dut.construct", num_entries = 1 )
  run_sim( th )

def test_pipe1_backpressure():
  th = TestHarness( Bits16, PipeQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", initial_delay = 20 )
  th.set_param( "top.dut.construct", num_entries = 1 )
  run_sim( th )

def test_pipe2_backpressure():
  th = TestHarness( Bits16, PipeQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", initial_delay = 20 )
  th.set_param( "top.dut.construct", num_entries = 2 )
  run_sim( th )

def test_bypass1_simple():
  th = TestHarness( Bits16, BypassQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", arrival_time = arrival_bypass )
  th.set_param( "top.dut.construct", num_entries = 1 )
  run_sim( th )

def test_bypass1_backpressure():
  th = TestHarness( Bits16, BypassQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", initial_delay = 20 )
  th.set_param( "top.dut.construct", num_entries = 1 )
  run_sim( th )

def test_bypass2_sparse():
  th = TestHarness( Bits16, BypassQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.src.construct", interval_delay = 3 )
  th.set_param( "top.dut.construct", num_entries = 2 )
  run_sim( th )

@pytest.mark.parametrize(
  'QType, num_entries',
  product( [ NormalQueueRTL, PipeQueueRTL, BypassQueueRTL ], [ 8, 10, 12, 16 ] )
)
def test_large_backpressure( QType, num_entries ):
  msgs = test_msgs * 8
  th = TestHarness( Bits16, QType, msgs, msgs )
  th.set_param( "top.sink.construct", initial_delay = 20 )
  th.set_param( "top.dut.construct", num_entries = 16 )
  run_sim( th )

@pytest.mark.parametrize(
  'QType', [ NormalQueue1EntryRTL, PipeQueue1EntryRTL, BypassQueue1EntryRTL ]
)
def test_single_simple( QType ):
  th = TestHarness( Bits16, QType, test_msgs, test_msgs )
  run_sim( th )

@pytest.mark.parametrize(
  'QType', [ NormalQueue1EntryRTL, PipeQueue1EntryRTL, BypassQueue1EntryRTL ]
)
def test_single_backpressure( QType ):
  th = TestHarness( Bits16, QType, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", initial_delay = 10, interval_delay=2 )
  run_sim( th )
