"""
==========================================================================
ChecksumXcelVRTL_test.py
==========================================================================
Test cases for translated RTL checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
import pytest

from pymtl3 import *
from pymtl3.passes.backends.verilog import VerilogTranslationImportPass
from pymtl3.stdlib.test_utils.test_helpers import finalize_verilator

from ..ChecksumXcelRTL import ChecksumXcelRTL
from .ChecksumXcelRTL_test import mk_xcel_transaction

#-------------------------------------------------------------------------
# Wrap Xcel into a function
#-------------------------------------------------------------------------
# [checksum_xcel_vrtl] creates an RTL checksum accelerator, translates
# it using the verilog backend and imports the translated model back, feeds
# in the input, ticks it, gets the response, and returns the result.

def checksum_xcel_vrtl( words ):
  assert len(words) == 8

  # Create a simulator using RTL accelerator
  dut = ChecksumXcelRTL()
  dut.elaborate()

  # Translate the checksum unit and import it back in using the verilog
  # backend
  dut.set_metadata( VerilogTranslationImportPass.enable, True )
  dut = VerilogTranslationImportPass()( dut )

  # Create a simulator
  dut.elaborate()
  dut.apply( DefaultPassGroup() )
  dut.sim_reset()

  reqs, _ = mk_xcel_transaction( words )

  for req in reqs:

    # Wait until xcel is ready to accept a request
    dut.xcel.respstream.rdy @= 1
    while not dut.xcel.reqstream.rdy:
      dut.xcel.reqstream.val @= 0
      dut.sim_tick()

    # Send a request
    dut.xcel.reqstream.val @= 1
    dut.xcel.reqstream.msg @= req
    dut.sim_tick()

    # Wait for response
    while not dut.xcel.respstream.val:
      dut.xcel.reqstream.val @= 0
      dut.sim_tick()

    # Get the response message
    resp_data = dut.xcel.respstream.msg.data
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

@pytest.mark.usefixtures("cmdline_opts")
class ChecksumXcelVRTLSrcSink_Tests( BaseTests ):

  def run_sim( s, th ):
    vcd_file_name = s.__class__.cmdline_opts["dump_vcd"]
    max_cycles = s.__class__.cmdline_opts["max_cycles"] or 10000

    # Translate the DUT and import it back in using the verilog backend.
    th.elaborate()

    # Check command line arguments for vcd dumping
    if vcd_file_name:
      th.set_metadata( VcdGenerationPass.vcd_file_name, vcd_file_name )
      th.dut.set_metadata( VerilogVerilatorImportPass.vl_trace, True )
      th.dut.set_metadata( VerilogVerilatorImportPass.vl_trace_filename, vcd_file_name )

    # Translate the DUT and import it back in using the verilog backend.
    th.dut.set_metadata( VerilogTranslationImportPass.enable, True )

    th = VerilogTranslationImportPass()( th )

    # Create a simulator
    th.apply( DefaultPassGroup() )

    # Tick the simulator
    while not th.done() and th.sim_cycle_count() < max_cycles:
      th.sim_tick()

    # Check timeout
    assert th.sim_cycle_count() < max_cycles

    finalize_verilator( th )

#-------------------------------------------------------------------------
# Test translation script
#-------------------------------------------------------------------------

def test_proc_xcel_translate():
  import os
  from os.path import dirname
  script_path = dirname(dirname(__file__)) + '/proc-xcel-translate'
  os.system(f'python {script_path} --xcel cksum')
