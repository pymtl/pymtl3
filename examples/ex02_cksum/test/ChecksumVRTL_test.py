"""
==========================================================================
 ChecksumVRTL_test.py
==========================================================================
Test cases for translated checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""
from pymtl3 import *
from pymtl3.passes.backends.verilog import *
from pymtl3.passes.tracing import *
from pymtl3.stdlib.test_utils.test_helpers import finalize_verilator

from ..ChecksumFL import checksum
from ..ChecksumRTL import ChecksumRTL, StepUnit
from ..utils import b128_to_words, words_to_b128

#-------------------------------------------------------------------------
# Wrap RTL checksum unit into a function
#-------------------------------------------------------------------------
# Similar to [checksum_cl] in for the CL tests, [checksum_rtl] creates an
# RTL checksum unit, feeds in the input, ticks the checksum unit and gets
# the output.

def checksum_vrtl( words ):

  # Convert input words into bits
  bits_in = words_to_b128( words )

  # Instantiate and elaborate the checksum unit
  dut = ChecksumRTL()
  dut.elaborate()

  # Translate the checksum unit and import it back in using the verilog
  # backend
  dut.set_metadata( VerilogTranslationImportPass.enable, True )
  dut = VerilogTranslationImportPass()( dut )

  # Create a simulator
  dut.elaborate()
  dut.apply( DefaultPassGroup() )
  dut.sim_reset()

  # Wait until the checksum unit is ready to receive input
  dut.ostream.rdy @= 1
  while not dut.istream.rdy:
    dut.sim_tick()

  # Feed in the input
  dut.istream.val @= 1
  dut.istream.msg @= bits_in
  dut.sim_tick()

  # Wait until the checksum unit is about to send the message
  while not dut.ostream.val:
    dut.sim_tick()

  # Return the result
  return dut.ostream.msg

#-------------------------------------------------------------------------
# Reuse functionality from CL test suite
#-------------------------------------------------------------------------
# Similar to what we did for CL tests, we can reuse CL test cases by
# inherit from the CL test class and overwrite cksum_func to use the rtl
# version instead.

from .ChecksumRTL_test import ChecksumRTL_Tests as BaseTests

class ChecksumVRTL_Tests( BaseTests ):

  def cksum_func( s, words ):
    return checksum_vrtl( words )

#-------------------------------------------------------------------------
# Reuse src/sink based tests from CL test suite to test translation
#-------------------------------------------------------------------------
# We reuse all source/sink based tests for CL again to test whether our
# RTL code can be properly translated into system verilog. We overwrite
# [run_sim] of the CL test suite so that we can apply the translation and
# import pass to the DUT.

from .ChecksumRTL_test import ChecksumRTLSrcSink_Tests as BaseSrcSinkTests

class ChecksumVRTLSrcSink_Tests( BaseSrcSinkTests ):

  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumRTL

  def run_sim( s, th ):

    vcd_file_name = s.__class__.cmdline_opts["dump_vcd"]
    max_cycles = s.__class__.cmdline_opts["max_cycles"] or 10000

    th.elaborate()

    # Check command line arguments for vcd dumping
    if vcd_file_name:
      th.set_metadata( VcdGenerationPass.vcd_file_name, vcd_file_name )
      th.dut.set_metadata( VerilogVerilatorImportPass.vl_trace, True )
      th.dut.set_metadata( VerilogVerilatorImportPass.vl_trace_filename, vcd_file_name )

    # Translate the DUT and import it back in using the verilog backend.
    th.dut.set_metadata( VerilogTranslationImportPass.enable, True )

    # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''
    # Apply the translation-import and simulation passes
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

    th = VerilogTranslationImportPass()( th )
    th.apply( DefaultPassGroup(linetrace=False) )

    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

    th.sim_reset()

    # Tick the simulator
    while not th.done() and th.sim_cycle_count() < max_cycles:
      th.sim_tick()

    # Check timeout
    assert th.sim_cycle_count() < max_cycles

    finalize_verilator( th )

#-------------------------------------------------------------------------
# Test translation script
#-------------------------------------------------------------------------

def test_cksum_translate():
  import os
  from os.path import dirname
  script_path = dirname(dirname(__file__)) + '/cksum-translate'
  os.system(f'python {script_path}')
