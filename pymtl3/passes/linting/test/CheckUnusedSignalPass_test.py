"""
========================================================================
CheckUnusedSignalPass_test.py
========================================================================

Author : Shunning Jiang
Date   : Dec 29, 2019
"""

from pymtl3.datatypes import Bits1, Bits2
from pymtl3.dsl import *
from ..CheckUnusedSignalPass import CheckUnusedSignalPass


def test_signal_name_default_function():

  class Inner(Component):
    def construct( s ):
      s.in_ = InPort(Bits1)
      s.out = OutPort(Bits1)
      @s.update
      def up_good():
        s.out[0:1] = s.in_ + 1

      s.xx  = Wire(Bits1)
      s.xx2 = InPort(Bits1)

  class Top(Component):
    def construct( s ):
      s.inners = [ Inner() for i in range(2) ]
      s.wire = Wire(Bits1)
      s.wire2 = Wire(Bits2)
      s.wire2[1:2] //= s.inners[-1].out[0:1]

  top = Top()
  top.elaborate()
  top.apply( CheckUnusedSignalPass() )

  assert top._linting.unused_signals == [ top.inners[0].xx, top.inners[0].xx2,
                                          top.inners[1].xx, top.inners[1].xx2, top.wire ]
