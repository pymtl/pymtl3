
from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.passes.PassGroups import DynamicSim
from pymtl3.passes.yosys import TranslationPass, ImportPass
from ..ChecksumXcelRTL import ChecksumXcelRTL
from .ChecksumXcelCL_test import ChecksumXcelCLSrcSink_Tests as BaseTests


class XcelRTLSrcSinkSim_Tests( BaseTests ):

  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumXcelRTL

class XcelRTLSrcSinkTranslate_Tests( BaseTests ):

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
    th.apply( DynamicSim )
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