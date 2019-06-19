"""
==========================================================================
ChecksumXcelCL_test.py
==========================================================================
Tests for cycle level checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.passes.PassGroups import DynamicSim
from pymtl3.stdlib.cl.queues import BypassQueueCL
from pymtl3.stdlib.ifcs import XcelMsgType, mk_xcel_msg
from pymtl3.stdlib.test import TestSrcCL, TestSinkCL

from examples.ex02_cksum.ChecksumFL import checksum
from examples.ex02_cksum.utils import words_to_b128
from examples.ex02_cksum.test.ChecksumCL_test import ChecksumCL_Tests as BaseTests
from ..ChecksumXcelCL import ChecksumXcelCL

#-------------------------------------------------------------------------
# Helper functions to create a sequence of req/resp msg
#-------------------------------------------------------------------------

Req, Resp = mk_xcel_msg( 5, 32 )
rd = XcelMsgType.READ
wr = XcelMsgType.WRITE

def mk_xcel_transaction( words ):
  words = [ b16(x) for x in words ]
  bits = words_to_b128( words )
  reqs = []
  reqs.append( Req( wr, b5(0), bits[0 :32 ] ) )
  reqs.append( Req( wr, b5(1), bits[32:64 ] ) )
  reqs.append( Req( wr, b5(2), bits[64:96 ] ) )
  reqs.append( Req( wr, b5(3), bits[96:128] ) )
  reqs.append( Req( wr, b5(4), b32(1)       ) )
  reqs.append( Req( rd, b5(5), b32(0)       ) )
  
  resps = []
  resps.append( Resp( wr, b32(0)          ) )
  resps.append( Resp( wr, b32(0)          ) )
  resps.append( Resp( wr, b32(0)          ) )
  resps.append( Resp( wr, b32(0)          ) )
  resps.append( Resp( wr, b32(0)          ) )
  resps.append( Resp( rd, checksum(words) ) )

  return reqs, resps

#-------------------------------------------------------------------------
# WrappedChecksumXcelCL
#-------------------------------------------------------------------------
# WrappedChecksumXcelCL is a simple wrapper around the CL accelerator. It
# simply appends an output buffer at its response side so that its
# response can be obtained by calling dequeue.

class WrappedChecksumXcelCL( Component ):
  def construct( s ):
    ReqType, RespType = mk_xcel_msg( 5, 32 )
    s.recv = NonBlockingCalleeIfc( ReqType  )
    s.give = NonBlockingCalleeIfc( RespType )

    s.checksum_xcel = ChecksumXcelCL()
    s.out_q = BypassQueueCL( num_entries=1 )
    s.connect_pairs(
      s.recv,                    s.checksum_xcel.xcel.req,
      s.checksum_xcel.xcel.resp, s.out_q.enq, 
      s.out_q.deq,               s.give,
    )

  def line_trace( s ):
    return s.checksum_xcel.line_trace()

#-------------------------------------------------------------------------
# Wrap CL Xcel into a function
#-------------------------------------------------------------------------
# [checksum_xcel_cl] creates a checksum accelerator, feeds in the input,
# ticks it, gets the response, and returns the result.

def checksum_xcel_cl( words ):
  assert len( words ) == 8

  # Create a simulator

  dut = WrappedChecksumXcelCL()
  dut.apply( DynamicSim )
  
  reqs, _ = mk_xcel_transaction( words )

  for req in reqs:

    # Wait until xcel is ready to accept a request    
    while not dut.recv.rdy():
      dut.tick()
    
    # Send the request message to xcel
    dut.recv( req )
    dut.tick()
    
    # Wait until xcel is ready to give a response
    while not dut.give.rdy():
      dut.tick()

    resp_msg = dut.give()
    dut.tick()

  return resp_msg.data

#-------------------------------------------------------------------------
# Reuse ChecksumCL_test
#-------------------------------------------------------------------------
# We reuse the extened FL tests in ex02_cksum.test.ChecksumCL_test.

class ChecksumXcelCL_Tests( BaseTests ):

  def cksum_func( s, words ):
    return checksum_xcel_cl( words )

#-------------------------------------------------------------------------
# Test Harness for src/sink based tests
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, DutType=ChecksumXcelCL, src_msgs=[], sink_msgs=[] ):
    
    ReqType, RespType = mk_xcel_msg( 5, 32 )

    s.src  = TestSrcCL( ReqType, src_msgs )
    s.dut  = DutType()
    s.sink = TestSinkCL( ReqType, sink_msgs )

    s.connect( s.src.send,      s.dut.xcel.req )
    s.connect( s.dut.xcel.resp, s.sink.recv    )

  def done( s ):
    return s.src.done() and s.sink.done()
  
  def line_trace( s ):
    return "{}>{}>{}".format(
      s.src.line_trace(), s.dut.line_trace(), s.sink.line_trace()
    )

#-------------------------------------------------------------------------
# Src/sink based tests
#-------------------------------------------------------------------------

class ChecksumXcelCLSrcSink_Tests( object ):

  # [setup_class] will be called by pytest before running all the tests in
  # the test class. Here we specify the type of the design under test
  # that is used in all test cases. We can easily reuse all the tests in
  # this class simply by creating a new test class that inherits from
  # this class and overwrite the setup_class to provide a different DUT
  # type.
  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumXcelCL

  # [run_sim] is a helper function in the test suite that creates a
  # simulator and runs test. We can overwrite this function when
  # inheriting from the test class to apply different passes to the DUT.
  def run_sim( s, th, max_cycles=1000 ):
    
    # Create a simulator
    th.apply( DynamicSim )
    ncycles = 0
    th.sim_reset()
    print( "" )
    
    # Tick the simulator
    print("{:3}: {}".format( ncycles, th.line_trace() ))
    while not th.done() and ncycles < max_cycles:
      th.tick()
      ncycles += 1
      print("{:3}: {}".format( ncycles, th.line_trace() ))

    # Check timeout
    assert ncycles < max_cycles

  # [test_xcel_simple] is a simple test case with only 1 xcel transaction.
  def test_xcel_simple( s ):
    words = [ 1, 2, 3, 4, 5, 6, 7, 8 ]
    src_msgs, sink_msgs = mk_xcel_transaction( words )

    th = TestHarness( s.DutType, src_msgs, sink_msgs )
    s.run_sim( th )
  
  # [test_xcel_multi_msg] tests the xcel with multiple transactions.
  def test_xcel_multi_msg( s ):
    seq = [
      [ 1, 2, 3, 4, 5, 6, 7, 8 ],
      [ 8, 7, 6, 5, 4, 3, 2, 1 ],
      [ 0xf000, 0xff00, 0x1000, 0x2000, 0x5000, 0x6000, 0x7000, 0x8000 ],
    ]

    src_msgs  = []
    sink_msgs = []
    for words in seq:
      reqs, resps = mk_xcel_transaction( words )
      src_msgs.extend( reqs )
      sink_msgs.extend( resps )

    th = TestHarness( s.DutType, src_msgs, sink_msgs )
    s.run_sim( th )
