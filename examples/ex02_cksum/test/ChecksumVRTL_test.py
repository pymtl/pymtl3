"""
==========================================================================
 ChecksumVRTL_test.py
==========================================================================
Test cases for translated checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""
from pymtl3 import *
from pymtl3.passes.backends.yosys import TranslationImportPass
from pymtl3.stdlib.test import TestSinkCL, TestSrcCL

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

  # Translate the checksum unit and import it back in using the yosys
  # backend
  dut.set_metadata( TranslationImportPass.enable, True )
  dut = TranslationImportPass()( dut )

  # Create a simulator
  dut.elaborate()
  dut.apply( SimulationPass() )
  dut.sim_reset()

  # Wait until the checksum unit is ready to receive input
  dut.send.rdy @= 1
  while not dut.recv.rdy:
    dut.sim_tick()

  # Feed in the input
  dut.recv.en  @= 1
  dut.recv.msg @= bits_in
  dut.sim_tick()

  # Wait until the checksum unit is about to send the message
  while not dut.send.en:
    dut.sim_tick()

  # Return the result
  return dut.send.msg

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

class ChecksumVRTSrcSink_Tests( BaseSrcSinkTests ):

  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumRTL

  def run_sim( s, th, max_cycles=1000 ):

    s.vcd_file_name = s.__class__.cmdline_opts["dump_vcd"]

    # Check command line arguments for vcd dumping
    if s.vcd_file_name:
      th.dump_vcd = True
      th.vcd_file_name = "translated."+s.vcd_file_name

    # Translate the DUT and import it back in using the yosys backend.
    th.elaborate()
    th.dut.set_metadata( TranslationImportPass.enable, True )

    # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''
    # Apply the translation-import and simulation passes
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

    th = TranslationImportPass()( th )
    th.apply( SimulationPass() )

    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

    th.sim_reset()

    # Tick the simulator
    while not th.done() and th.sim_cycle_count() < max_cycles:
      th.sim_tick()

    # Check timeout
    assert th.sim_cycle_count() < max_cycles

#-------------------------------------------------------------------------
# Test translation script
#-------------------------------------------------------------------------

def test_cksum_translate():
  import os
  from os.path import dirname
  script_path = dirname(dirname(__file__)) + '/cksum-translate'
  os.system(f'python {script_path}')
