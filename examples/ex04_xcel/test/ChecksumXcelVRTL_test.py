"""
==========================================================================
 ChecksumXcelVRTL_test.py
==========================================================================
Test cases for translated RTL checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.passes.yosys import TranslationPass, ImportPass
from ..ChecksumXcelRTL import ChecksumXcelRTL

# TODO: add wrap func test.
# TODO: add more comments.

from .ChecksumXcelRTL_test import ChecksumXcelRTLSrcSink_Tests as BaseTests

class ChecksumXcelVRTLSrcSink_Tests( BaseTests ):

  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumXcelRTL

  def run_sim( s, th, max_cycles=1000 ):

    # Translate the DUT and import it back in using the yosys backend.
    th.elaborate()
    th.dut.yosys_translate = True
    th.dut.yosys_import = True
    th.apply( TranslationPass() )
    th = ImportPass()( th )

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
