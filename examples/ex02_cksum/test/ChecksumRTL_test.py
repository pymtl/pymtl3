"""
==========================================================================
 ChecksumRTL_test.py
==========================================================================
Test cases for RTL checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.passes.yosys import TranslationPass, ImportPass
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
  step_unit.apply( SimulationPass )

  step_unit.word_in  = b16(1)
  step_unit.sum1_acc = b32(1)
  step_unit.sum2_acc = b32(1)
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
  dut.apply( SimulationPass )
  dut.sim_reset()

  # Wait until the checksum unit is ready to receive input
  dut.send.rdy = b1(1)
  while not dut.recv.rdy:
    dut.tick()
  
  # Feed in the input
  dut.recv.en = b1(1)
  dut.recv.msg = bits_in
  dut.tick()
  
  # Wait until the checksum unit is about to send the message
  while not dut.send.en:
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

  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumRTL

  def run_sim( s, th, max_cycles=1000 ):
    
    # Check command line arguments for vcd dumping
    import sys
    if hasattr( sys, '_pymtl_dump_vcd' ):
      if sys._pymtl_dump_vcd:
        th.dump_vcd = True
        th.vcd_file_name = "ChecksumRTL"

    # Elaborate the component
    th.elaborate()

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
