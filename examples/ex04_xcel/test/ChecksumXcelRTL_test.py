"""
==========================================================================
ChecksumXcelRTL_test.py
==========================================================================
Test cases for RTL checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
from pymtl3 import *

from ..ChecksumXcelRTL import ChecksumXcelRTL
from .ChecksumXcelCL_test import mk_xcel_transaction

#-------------------------------------------------------------------------
# Wrap Xcel into a function
#-------------------------------------------------------------------------
# [checksum_xcel_rtl] creates an RTL checksum accelerator, feeds in the
# input, ticks it, gets the response, and returns the result.

def checksum_xcel_rtl( words ):
  assert len(words) == 8

  # Create a simulator using RTL accelerator
  dut = ChecksumXcelRTL()
  dut.elaborate()
  dut.apply( SimulationPass )
  dut.sim_reset()

  reqs, _ = mk_xcel_transaction( words )

  for req in reqs:

    # Wait until xcel is ready to accept a request
    dut.xcel.resp.rdy = b1(1)
    while not dut.xcel.req.rdy:
      dut.xcel.req.en   = b1(0)
      dut.tick()

    # Send a request
    dut.xcel.req.en  = b1(1)
    dut.xcel.req.msg = req
    dut.tick()

    # Wait for response
    while not dut.xcel.resp.en:
      dut.xcel.req.en = b1(0)
      dut.tick()

    # Get the response message
    resp_data = dut.xcel.resp.msg.data
    dut.tick()

  return resp_data

#-------------------------------------------------------------------------
# Reuse ChecksumXcelCL_test
#-------------------------------------------------------------------------
# We reuse the function tests in ChecksumXcelFL_test.

from .ChecksumXcelCL_test import ChecksumXcelCL_Tests as BaseTests

# ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Implement the tests for ChecksumXcelRTL
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
#; Create a class called ChecksumXcelRTL_Tests that inherits from
#; BaseTests and override the cksum_func by calling checksum_xcel_rtl.
#; This way helps you reuse all test cases in the ChecksumXcelFL_Tests to
#; test this ChecksumXcelRTL model

class ChecksumXcelRTL_Tests( BaseTests ):

  def cksum_func( s, words ):
    return checksum_xcel_rtl( words )

# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

#-------------------------------------------------------------------------
# Src/sink based tests
#-------------------------------------------------------------------------
# Here we directly reuse all test cases in ChecksumXcelCL_test. We only
# need to provide a different DutType in the setup_class.

from .ChecksumXcelCL_test import ChecksumXcelCLSrcSink_Tests as SrcSinkBaseTests

class ChecksumXcelRTLSrcSink_Tests( SrcSinkBaseTests ):

  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumXcelRTL
