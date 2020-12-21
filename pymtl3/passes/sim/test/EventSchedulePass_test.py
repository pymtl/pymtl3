#=========================================================================
# DynamicSchedulePass_test.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Apr 19, 2019

from pymtl3.datatypes import Bits8, Bits32, bitstruct
from pymtl3.dsl import *
from pymtl3.dsl.errors import UpblkCyclicError

from ..GenDAGPass import GenDAGPass
from ..PrepareSimPass import PrepareSimPass
from ..EventSchedulePass import EventSchedulePass


def _test_model( cls ):
  A = cls()
  A.elaborate()
  A.apply( GenDAGPass() )
  A.apply( SimpleSchedulePass() )
  A.apply( PrepareSimPass() )

  A.sim_reset()
  A.sim_eval_combinational()

  T = 0
  while T < 5:
    A.sim_tick()
    T += 1
  return A

def test_gl():
  class Top(Component):
    def construct( s ):
      s.a = Wire(32)
      s.b = Wire(32)

      @update_delay(600)
      def up_a():
        s.a <<= Bits32(12)

      @update
      def up():
        s.b @= s.a + 1

  x = Top()
  x.elaborate()
  x.apply( GenDAGPass() )
  print(x._dsl.all_update_delay)
  print(x._dsl.all_upblks)

def test_clock_gen():

  class Top(Component):
    def construct( s ):
      s.en = InPort()
      s.nand_out = Wire()
      s.inv0_out = Wire()
      s.inv1_out = Wire()
      s.inv2_out = Wire()
      s.inv3_out = Wire()
      s.out = OutPort()

      @update_delay(300)
      def up_nand():
        s.nand_out <<= ~(s.inv1_out & s.en)

      @update_delay(100)
      def up_inv0():
        s.inv0_out <<= ~s.nand_out

      @update_delay(100)
      def up_inv1():
        s.inv1_out <<= ~s.inv0_out

      @update_delay(100)
      def up_inv2():
        s.inv2_out <<= ~s.inv1_out

      @update_delay(100)
      def up_inv3():
        s.inv3_out <<= ~s.inv2_out

      s.out //= s.inv3_out

  x = Top()
  x.elaborate()
  x.apply( GenDAGPass() )
  x.apply( EventSchedulePass() )

  x.en @= 0
  x.sim_delay( 2000 )
  print("\nenable @= 1\n")
  x.en @= 1
  x.sim_delay( 2000 )
