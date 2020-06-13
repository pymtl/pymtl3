"""
==========================================================================
 ChecksumRTL_test.py
==========================================================================
Test cases for RTL checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""
import pytest

from pymtl3 import *
from pymtl3.passes.tracing import VcdGenerationPass, PrintTextWavePass
from pymtl3.stdlib.test_utils import TestSinkCL, TestSrcCL
from pymtl3.stdlib.test_utils.test_helpers import finalize_verilator

from ..ChecksumFL import checksum
from ..ChecksumRTL import ChecksumRTL, StepUnit
from ..utils import b128_to_words, words_to_b128

#-------------------------------------------------------------------------
# Unit test the step unit
#-------------------------------------------------------------------------
# A very simple unit test for the step unit.

def test_step_unit():
  step_unit = StepUnit()
  step_unit.elaborate()
  step_unit.apply( DefaultPassGroup() )

  step_unit.word_in @= 1
  step_unit.sum1_in @= 1
  step_unit.sum2_in @= 1
  step_unit.sim_eval_combinational()
  assert step_unit.sum1_out == 2
  assert step_unit.sum2_out == 3

  step_unit.sim_tick()

#-------------------------------------------------------------------------
# Wrap RTL checksum unit into a function
#-------------------------------------------------------------------------
# Similar to [checksum_cl] in for the CL tests, [checksum_rtl] creates an
# RTL checksum unit, feeds in the input, ticks the checksum unit and gets
# the output.

def checksum_rtl( words ):
  bits_in = words_to_b128( words )

  # Create a simulator
  dut = ChecksumRTL()
  dut.elaborate()
  dut.apply( DefaultPassGroup() )
  dut.sim_reset()

  # Wait until the checksum unit is ready to receive input
  dut.send.rdy @= 1
  while not dut.recv.rdy:
    dut.recv.en @= 0
    dut.sim_tick()

  # Feed in the input
  dut.recv.en  @= 1
  dut.recv.msg @= bits_in
  dut.sim_tick()

  # Wait until the checksum unit is about to send the message
  while not dut.send.en:
    dut.recv.en @= 0
    dut.sim_tick()

  # Return the result
  return dut.send.msg

#-------------------------------------------------------------------------
# Reuse functionality from CL test suite
#-------------------------------------------------------------------------
# Similar to what we did for CL tests, we can reuse CL test cases by
# inherit from the CL test class and overwrite cksum_func to use the rtl
# version instead.

from .ChecksumCL_test import ChecksumCL_Tests as BaseTests

@pytest.mark.usefixtures("cmdline_opts")
class ChecksumRTL_Tests( BaseTests ):

  def cksum_func( s, words ):
    return checksum_rtl( words )

#-------------------------------------------------------------------------
# Reuse src/sink based tests from CL test suite to test simulation
#-------------------------------------------------------------------------
# Again, we reuse all source/sink based tests for CL by simply inheriting
# from the test class and providing a different DUT type in [setup_class].

from .ChecksumCL_test import ChecksumCLSrcSink_Tests as BaseSrcSinkTests

@pytest.mark.usefixtures("cmdline_opts")
class ChecksumRTLSrcSink_Tests( BaseSrcSinkTests ):

  # [setup_class] will be called by pytest before running all the tests in
  # the test class. Here we specify the type of the design under test
  # that is used in all test cases. We can easily reuse all the tests in
  # this class simply by creating a new test class that inherits from
  # this class and overwrite the setup_class to provide a different DUT
  # type.
  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumRTL

  # [setup_method] will be called by pytest before executing each class method.
  # See pytest documetnation for more details.
  def setup_method( s, method ):
    s.current_test_method_name = method.__name__

  # [teardown_method] will be called by pytest after executing each class method.
  # See pytest documetnation for more details.
  def teardown_method( s, method ):
    s.current_test_method_name = ""

  def run_sim( s, th ):

    vcd_file_name = s.__class__.cmdline_opts["dump_vcd"]
    max_cycles = s.__class__.cmdline_opts["max_cycles"] or 10000

    # Check for vcd dumping
    if vcd_file_name:
      th.set_metadata( VcdGenerationPass.vcd_file_name, vcd_file_name )
      th.set_metadata( PrintTextWavePass.enable, True )

    # Create a simulator
    th.apply( DefaultPassGroup() )
    th.sim_reset()

    while not th.done() and th.sim_cycle_count() < max_cycles:
      th.sim_tick()

    if vcd_file_name:
      th.print_textwave()

    # Check timeout
    assert th.sim_cycle_count() < max_cycles

    finalize_verilator( th )
