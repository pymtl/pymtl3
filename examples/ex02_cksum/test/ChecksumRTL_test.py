"""
==========================================================================
 ChecksumRTL_test.py
==========================================================================
Test cases for RTL checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""
from pymtl3 import *
from pymtl3.passes import TracingConfigs
from pymtl3.passes.backends.yosys import ImportPass, TranslationPass
from pymtl3.stdlib.test import TestSinkCL, TestSrcCL

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
  step_unit.apply( SimulationPass() )

  step_unit.word_in = b16(1)
  step_unit.sum1_in = b32(1)
  step_unit.sum2_in = b32(1)
  step_unit.tick()

  assert step_unit.sum1_out == b32(2)
  assert step_unit.sum2_out == b32(3)

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
  dut.apply( SimulationPass() )
  dut.sim_reset()

  # Wait until the checksum unit is ready to receive input
  dut.send.rdy = b1(1)
  while not dut.recv.rdy:
    dut.recv.en = b1(0)
    dut.eval_combinational()
    dut.tick()

  # Feed in the input
  dut.recv.en = b1(1)
  dut.recv.msg = bits_in
  dut.eval_combinational()
  dut.tick()

  # Wait until the checksum unit is about to send the message
  while not dut.send.en:
    dut.recv.en = b1(0)
    dut.eval_combinational()
    dut.tick()

  # Return the result
  return dut.send.msg

#-------------------------------------------------------------------------
# Reuse functionality from CL test suite
#-------------------------------------------------------------------------
# Similar to what we did for CL tests, we can reuse CL test cases by
# inherit from the CL test class and overwrite cksum_func to use the rtl
# version instead.

from .ChecksumCL_test import ChecksumCL_Tests as BaseTests

class ChecksumRTL_Tests( BaseTests ):

  def cksum_func( s, words ):
    return checksum_rtl( words )

#-------------------------------------------------------------------------
# Reuse src/sink based tests from CL test suite to test simulation
#-------------------------------------------------------------------------
# Again, we reuse all source/sink based tests for CL by simply inheriting
# from the test class and providing a different DUT type in [setup_class].

from .ChecksumCL_test import ChecksumCLSrcSink_Tests as BaseSrcSinkTests

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
    s.vcd_file_name = ""

    import sys
    if hasattr( sys, '_pymtl_dump_vcd' ):
      if sys._pymtl_dump_vcd:
        s.vcd_file_name = "{}.{}".format( s.DutType.__name__, method.__name__ )

  # [teardown_method] will be called by pytest after executing each class method.
  # See pytest documetnation for more details.
  def teardown_method( s, method ):
    s.vcd_file_name = ""

  def run_sim( s, th, max_cycles=1000 ):

    # Check for vcd dumping
    if s.vcd_file_name:
      th.config_tracing = TracingConfigs(tracing='text_fancy', vcd_file_name=s.vcd_file_name)

    # Create a simulator
    th.apply( SimulationPass() )
    ncycles = 0
    th.sim_reset()
    print( "" )

    # Tick the simulator
    print("{:3}: {}".format( ncycles, th.line_trace() ))
    while not th.done() and ncycles < max_cycles:
      th.tick()
      ncycles += 1
      print("{:3}: {}".format( ncycles, th.line_trace() ))

    if s.vcd_file_name:
      th.print_textwave()

    # Check timeout
    assert ncycles < max_cycles
