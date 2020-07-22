#=========================================================================
# DynamicSchedulePass_test.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Apr 19, 2019

from pymtl3.dsl import Component, Wire, update_ff

from ... import DefaultPassGroup
from ...backends.verilog import *
from ..AddDebugSignalPass import AddDebugSignalPass


def test_bring_up_non_top_debug_signal():

  class Mult(Component):
    def construct( s, init=0 ):
      s.en = Wire(32)
      @update_ff
      def ff():
        if s.reset:
          s.en <<= init
        else:
          s.en <<= s.en ^ 1

  class Dpath(Component):
    def construct( s ):
      s.mult = Mult()

  class Core(Component):
    def construct( s ):
      s.dpath = Dpath()

  class Tile(Component):
    def construct( s ):
      s.core = Core()

  class CoreChip(Component):
    def construct( s ):
      s.tile0 = Tile()
      # s.tile1 = Tile()

  class FullChip(Component):
    def construct( s ):
      s.corechip = CoreChip()

  class Top(Component):
    def construct( s ):
      s.fullchip = FullChip()

    def line_trace( s ):
      return str(s.debug_0)

  top1 = Top()
  top1.set_param( "top.fullchip.corechip.tile0.core.dpath.mult.construct", init=0x100 )
  # top.set_param( "top.fullchip.corechip.tile1.core.dpath.mult.construct", init=0x888 )
  top1.elaborate()

  AddDebugSignalPass()( top1, [ "top.fullchip.corechip.tile0.core.dpath.mult.en",
                              # "top.fullchip.corechip.tile1.core.dpath.mult.en",
                              ])

  top1.apply( DefaultPassGroup() )
  top1.sim_reset()

  for i in range(10):
    top1.sim_tick()

  top2 = Top()
  top2.set_param( "top.fullchip.corechip.tile0.core.dpath.mult.construct", init=0x100 )
  # top2.set_param( "top.fullchip.corechip.tile1.core.dpath.mult.construct", init=0x888 )
  top2.elaborate()

  AddDebugSignalPass()( top2, [ "top.fullchip.corechip.tile0.core.dpath.mult.en",
                              # "top.fullchip.corechip.tile1.core.dpath.mult.en",
                              ])

  top2.set_metadata( VerilogTranslationImportPass.enable, True )
  top2 = VerilogTranslationImportPass()( top2 )

  top2.apply( DefaultPassGroup() )
  top2.sim_reset()

  for i in range(10):
    top2.sim_tick()

  top2.finalize()
