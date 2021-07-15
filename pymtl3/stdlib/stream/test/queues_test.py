"""
========================================================================
Tests for queues
========================================================================

Author: Shunning Jiang, Yanghui Ou
  Date: Feb 22, 2021
"""
from itertools import product

import pytest

from pymtl3 import *
from pymtl3.stdlib.test_utils import TestVectorSimulator, run_sim
from ..SourceRTL import SourceRTL
from ..SinkRTL import SinkRTL

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

def run_tv_test( dut, test_vectors, cmdline_opts  ):

  # Define input/output functions

  def tv_in( dut, tv ):
    dut.recv.val @= tv[0]
    dut.recv.msg @= tv[2]
    dut.send.rdy @= tv[4]

  def tv_out( dut, tv ):
    if tv[1] != '?': assert dut.recv.rdy == tv[1]
    if tv[3] != '?': assert dut.send.val == tv[3]
    if tv[5] != '?': assert dut.send.msg == tv[5]

  # Run the test

  sim = TestVectorSimulator( dut, test_vectors, tv_in, tv_out )
  sim.run_test( cmdline_opts )

def test_normal_behavior( cmdline_opts ):

  B1  = mk_bits(1)
  B32 = mk_bits(32)
  run_tv_test( NormalQueueRTL( Bits32, 2 ), [
    #  recv.val recv.rdy recv.msg  send.val send.rdy send.msg
    [  1,       1,       0x123,    0,       0,       '?'   ],
    [  1,       1,       0x345,    1,       0,       0x123 ],
    [  1,       0,       0x567,    1,       0,       0x123 ],
    [  1,       0,       0x567,    1,       1,       0x123 ],
    [  1,       1,       0x567,    1,       1,       0x345 ],
    [  1,       1,       0x890,    1,       0,       '?'   ],
    [  1,       0,       0x0  ,    1,       1,       0x567 ],
    [  0,       1,       0x0  ,    1,       1,       0x890 ],
    [  1,       1,       0x2  ,    0,       1,       '?'   ],
    [  1,       1,       0x3  ,    1,       1,       0x2   ],
    [  1,       1,       0x4  ,    1,       1,       0x3   ],
  ], cmdline_opts )

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, MsgType, QueueType, src_msgs, sink_msgs ):

    s.src  = SourceRTL( MsgType, src_msgs )
    s.dut  = QueueType( MsgType )
    s.sink = SinkRTL( MsgType, sink_msgs )

    s.src.send //= s.dut.recv
    s.dut.send //= s.sink.recv

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{} ({}) {}".format(
      s.src.line_trace(), s.dut.line_trace(), s.sink.line_trace() )

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

test_msgs = [ Bits16( 4 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ) ]

arrival_normal = [ 3, 5, 7, 9 ]
arrival_pipe   = [ 3, 4, 5, 6 ]
arrival_bypass = [ 2, 3, 4, 5 ]


def test_normal1_simple( cmdline_opts ):
  th = TestHarness( Bits16, NormalQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", arrival_time = arrival_normal )
  th.set_param( "top.dut.construct", num_entries = 1 )
  run_sim( th, cmdline_opts, duts=['dut'] )

def test_normal2_simple( cmdline_opts ):
  th = TestHarness( Bits16, NormalQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", arrival_time = arrival_pipe )
  th.set_param( "top.dut.construct", num_entries = 2 )
  run_sim( th, cmdline_opts, duts=['dut'] )

def test_normal3_simple( cmdline_opts ):
  th = TestHarness( Bits16, NormalQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", arrival_time = arrival_pipe )
  th.set_param( "top.dut.construct", num_entries = 3 )
  run_sim( th, cmdline_opts, duts=['dut'] )

def test_pipe1_simple( cmdline_opts ):
  th = TestHarness( Bits16, PipeQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", arrival_time = arrival_pipe )
  th.set_param( "top.dut.construct", num_entries = 1 )
  run_sim( th, cmdline_opts, duts=['dut'] )

def test_pipe1_backpressure( cmdline_opts ):
  th = TestHarness( Bits16, PipeQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", initial_delay = 20 )
  th.set_param( "top.dut.construct", num_entries = 1 )
  run_sim( th, cmdline_opts, duts=['dut'] )

def test_pipe2_backpressure( cmdline_opts ):
  th = TestHarness( Bits16, PipeQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", initial_delay = 20 )
  th.set_param( "top.dut.construct", num_entries = 2 )
  run_sim( th, cmdline_opts, duts=['dut'] )

def test_pipe3_backpressure( cmdline_opts ):
  th = TestHarness( Bits16, PipeQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", initial_delay = 20 )
  th.set_param( "top.dut.construct", num_entries = 3 )
  run_sim( th, cmdline_opts, duts=['dut'] )

def test_bypass1_simple( cmdline_opts ):
  th = TestHarness( Bits16, BypassQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", arrival_time = arrival_bypass )
  th.set_param( "top.dut.construct", num_entries = 1 )
  run_sim( th, cmdline_opts, duts=['dut'] )

def test_bypass1_backpressure( cmdline_opts ):
  th = TestHarness( Bits16, BypassQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", initial_delay = 20 )
  th.set_param( "top.dut.construct", num_entries = 1 )
  run_sim( th, cmdline_opts, duts=['dut'] )

def test_bypass2_sparse( cmdline_opts ):
  th = TestHarness( Bits16, BypassQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.src.construct", interval_delay = 3 )
  th.set_param( "top.dut.construct", num_entries = 2 )
  run_sim( th, cmdline_opts, duts=['dut'] )

def test_bypass3_sparse( cmdline_opts ):
  th = TestHarness( Bits16, BypassQueueRTL, test_msgs, test_msgs )
  th.set_param( "top.src.construct", interval_delay = 3 )
  th.set_param( "top.dut.construct", num_entries = 3 )
  run_sim( th, cmdline_opts, duts=['dut'] )

@pytest.mark.parametrize(
  'QType, num_entries',
  product( [ NormalQueueRTL, PipeQueueRTL, BypassQueueRTL ], [ 8, 10, 12, 16 ] )
)
def test_large_backpressure( QType, num_entries, cmdline_opts ):
  msgs = test_msgs * 8
  th = TestHarness( Bits16, QType, msgs, msgs )
  th.set_param( "top.sink.construct", initial_delay = 20 )
  th.set_param( "top.dut.construct", num_entries = 16 )
  run_sim( th, cmdline_opts, duts=['dut'] )

@pytest.mark.parametrize(
  'QType', [ NormalQueue1EntryRTL, PipeQueue1EntryRTL, BypassQueue1EntryRTL ]
)
def test_single_simple( QType, cmdline_opts ):
  th = TestHarness( Bits16, QType, test_msgs, test_msgs )
  run_sim( th, cmdline_opts, duts=['dut'] )

@pytest.mark.parametrize(
  'QType', [ NormalQueue1EntryRTL, PipeQueue1EntryRTL, BypassQueue1EntryRTL ]
)
def test_single_backpressure( QType, cmdline_opts ):
  th = TestHarness( Bits16, QType, test_msgs, test_msgs )
  th.set_param( "top.sink.construct", initial_delay = 10, interval_delay=2 )
  run_sim( th, cmdline_opts, duts=['dut'] )


@pytest.mark.parametrize(
  'QType, num_entries',
  product( [ NormalQueueRTL, PipeQueueRTL, BypassQueueRTL ], [ 8, 10, 12, 16 ] )
)
def test_large_delay( QType, num_entries, cmdline_opts ):
  msgs = test_msgs * 8
  th = TestHarness( Bits16, QType, msgs, msgs )
  th.set_param( "top.src.construct",  initial_delay=5,  interval_delay = 3)
  th.set_param( "top.sink.construct", initial_delay=20, interval_delay = 7)
  th.set_param( "top.dut.construct", num_entries = 16 )
  run_sim( th, cmdline_opts, duts=['dut'] )
