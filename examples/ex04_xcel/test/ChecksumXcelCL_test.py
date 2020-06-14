"""
==========================================================================
ChecksumXcelCL_test.py
==========================================================================
Tests for cycle level checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
import pytest

from examples.ex02_cksum.ChecksumFL import checksum
from examples.ex02_cksum.utils import words_to_b128
from pymtl3 import *
from pymtl3.stdlib.queues import BypassQueueCL
from pymtl3.stdlib.connects import connect_pairs
from pymtl3.stdlib.ifcs import XcelMsgType, mk_xcel_msg
from pymtl3.stdlib.test_utils import TestSinkCL, TestSrcCL, run_sim

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
  reqs.append( Req( wr, 0, bits[0 :32 ] ) )
  reqs.append( Req( wr, 1, bits[32:64 ] ) )
  reqs.append( Req( wr, 2, bits[64:96 ] ) )
  reqs.append( Req( wr, 3, bits[96:128] ) )
  reqs.append( Req( wr, 4, 1            ) )
  reqs.append( Req( rd, 5, 0            ) )

  resps = []
  resps.append( Resp( wr, 0               ) )
  resps.append( Resp( wr, 0               ) )
  resps.append( Resp( wr, 0               ) )
  resps.append( Resp( wr, 0               ) )
  resps.append( Resp( wr, 0               ) )
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

    s.recv = CalleeIfcCL( Type=Req  )
    s.give = CalleeIfcCL( Type=Resp )

    s.checksum_xcel = ChecksumXcelCL()
    s.out_q = BypassQueueCL( num_entries=1 )
    connect_pairs(
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

  # Create a simulator using CL accelerator
  dut = WrappedChecksumXcelCL()
  dut.elaborate()
  dut.apply( DefaultPassGroup() )
  dut.sim_reset()

  reqs, _ = mk_xcel_transaction( words )

  for req in reqs:

    # Wait until xcel is ready to accept a request
    while not dut.recv.rdy():
      dut.sim_tick()

    # Send the request message to xcel
    dut.recv( req )
    dut.sim_tick()

    # Wait until xcel is ready to give a response
    while not dut.give.rdy():
      dut.sim_tick()

    resp_msg = dut.give()

  return resp_msg.data

#-------------------------------------------------------------------------
# Reuse ChecksumXcelFL_test
#-------------------------------------------------------------------------
# We reuse the function tests in ChecksumXcelFL_test.

from .ChecksumXcelFL_test import ChecksumXcelFL_Tests as BaseTests

# ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Implement the tests for ChecksumXcelCL
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
#; Create a class called ChecksumXcelCL_Tests that inherits from BaseTests
#; and override the cksum_func by calling checksum_xcel_cl. This way helps
#; you reuse all test cases in the ChecksumXcelFL_Tests to test this
#; ChecksumXcelCL model

class ChecksumXcelCL_Tests( BaseTests ):

  def cksum_func( s, words ):
    return checksum_xcel_cl( words )

# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

#-------------------------------------------------------------------------
# Test Harness for src/sink based tests
#-------------------------------------------------------------------------
# The test harness has a test source that sends requests to the xcel and a
# test sink that checks the xcel responses.

class TestHarness( Component ):

  def construct( s, DutType=ChecksumXcelCL, src_msgs=[], sink_msgs=[] ):

    ReqType, RespType = mk_xcel_msg( 5, 32 )

    s.src  = TestSrcCL( ReqType, src_msgs )
    s.dut  = DutType()
    s.sink = TestSinkCL( ReqType, sink_msgs )

    connect( s.src.send,      s.dut.xcel.req )
    connect( s.dut.xcel.resp, s.sink.recv    )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{}>{}>{}".format(
      s.src.line_trace(), s.dut.line_trace(), s.sink.line_trace()
    )

#-------------------------------------------------------------------------
# Src/sink based tests
#-------------------------------------------------------------------------
# More adavanced testsing that uses test source and test sink.

@pytest.mark.usefixtures("cmdline_opts")
class ChecksumXcelCLSrcSink_Tests:

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
  def run_sim( s, th ):
    run_sim( th, s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # test_xcel_srcsink_simple
  #-----------------------------------------------------------------------
  # A simple test case with only 1 xcel transaction.

  def test_xcel_srcsink_simple( s ):
    words = [ 1, 2, 3, 4, 5, 6, 7, 8 ]
    src_msgs, sink_msgs = mk_xcel_transaction( words )

    th = TestHarness( s.DutType, src_msgs, sink_msgs )
    s.run_sim( th )

  #-----------------------------------------------------------------------
  # test_xcel_srcsink_multi_msg
  #-----------------------------------------------------------------------
  # Test the xcel with multiple transactions.

  def test_xcel_srcsink_multi_msg( s ):
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
