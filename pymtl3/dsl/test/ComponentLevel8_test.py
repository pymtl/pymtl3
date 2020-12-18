"""
========================================================================
ComponentLevel8_test.py
========================================================================

Author : Shunning Jiang
Date   : Dec 7, 2020
"""

from pymtl3.datatypes import Bits1, Bits16, Bits32, bitstruct, mk_bits, zext
from pymtl3.dsl.ComponentLevel1 import update
from pymtl3.dsl.ComponentLevel8 import ComponentLevel8, update_delay
from pymtl3.dsl.Connectable import InPort, Interface, OutPort, Wire

def test_gl():
  class Top(ComponentLevel8):
    def construct( s ):
      s.a = Wire(32)
      s.b = Wire(32)

      @update_delay(600)
      def up_a():
        s.a <<= Bits32(12)

      @update
      def up():
        s.b <<= s.a + 1

  x = Top()
  x.elaborate()
  print(x._dsl.all_update_delay)
  print(x._dsl.all_upblks)
