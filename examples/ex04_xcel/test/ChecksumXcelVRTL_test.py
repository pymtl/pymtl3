"""
==========================================================================
ChecksumXcelVRTL_test.py
==========================================================================
Test cases for translated RTL checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
from pymtl3 import *
from pymtl3.passes.yosys import TranslationImportPass

from ..ChecksumXcelRTL import ChecksumXcelRTL
from .ChecksumXcelCL_test import mk_xcel_transaction

#-------------------------------------------------------------------------
# Wrap Xcel into a function
#-------------------------------------------------------------------------
# [checksum_xcel_vrtl] creates an RTL checksum accelerator, translates
# it using the yosys backend and imports the translated model back, feeds
# in the input, ticks it, gets the response, and returns the result.

def checksum_xcel_vrtl( words ):
  assert len(words) == 8

  # Create a simulator using RTL accelerator
  dut = ChecksumXcelRTL()
  dut.elaborate()

  # Translate the checksum unit and import it back in using the yosys
  # backend
  dut.yosys_translate_import = True
  dut = TranslationImportPass()( dut )

  # Create a simulator
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
# Reuse ChecksumXcelRTL_test
#-------------------------------------------------------------------------
# We reuse the function tests in ChecksumXcelFL_test.

from .ChecksumXcelRTL_test import ChecksumXcelRTL_Tests as BaseTests

class ChecksumXcelVRTL_Tests( BaseTests ):

  def cksum_func( s, words ):
    return checksum_xcel_vrtl( words )

#-------------------------------------------------------------------------
# Src/sink based tests
#-------------------------------------------------------------------------
# Here we directly reuse all test cases in ChecksumXcelRTL_test. We only
# need to overwrite the [run_sim] function to apply translation and import
# pass to the DUT.

class ChecksumXcelVRTLSrcSink_Tests( BaseTests ):

  def run_sim( s, th, max_cycles=1000 ):

    # Translate the DUT and import it back in using the yosys backend.
    th.elaborate()
    th.dut.yosys_translate_import = True
    th = TranslationImportPass()( th )

    # Create a simulator
    th.apply( SimulationPass )
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
