"""
==========================================================================
ChecksumXcelVRTL_test.py
==========================================================================
Test cases for translated RTL checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
from pymtl3 import *
from pymtl3.passes.backends.yosys import TranslationImportPass

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
  dut.set_metadata( TranslationImportPass.enable, True )
  dut = TranslationImportPass()( dut )

  # Create a simulator
  dut.elaborate()
  dut.apply( SimulationPass() )
  dut.sim_reset()

  reqs, _ = mk_xcel_transaction( words )

  for req in reqs:

    # Wait until xcel is ready to accept a request
    dut.xcel.resp.rdy @= 1
    while not dut.xcel.req.rdy:
      dut.xcel.req.en @= 0
      dut.sim_tick()

    # Send a request
    dut.xcel.req.en  @= 1
    dut.xcel.req.msg @= req
    dut.sim_tick()

    # Wait for response
    while not dut.xcel.resp.en:
      dut.xcel.req.en @= 0
      dut.sim_tick()

    # Get the response message
    resp_data = dut.xcel.resp.msg.data
    dut.sim_tick()

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
    th.dut.set_metadata( TranslationImportPass.enable, True )
    th = TranslationImportPass()( th )

    # Create a simulator
    th.apply( SimulationPass() )

    # Tick the simulator
    while not th.done() and th.sim_cycle_count() < max_cycles:
      th.sim_tick()

    # Check timeout
    assert th.sim_cycle_count() < max_cycles

#-------------------------------------------------------------------------
# Test translation script
#-------------------------------------------------------------------------

def test_proc_xcel_translate():
  import os
  from os.path import dirname
  script_path = dirname(dirname(__file__)) + '/proc-xcel-translate'
  os.system(f'python {script_path} --xcel cksum')
