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

def test_clock_gen_flat():

  class Top(Component):
    def construct( s ):
      s.en = InPort()
      s.nand_out = Wire()
      s.inv0_out = Wire()
      s.inv1_out = Wire()
      s.out = OutPort()

      @update_delay(300)
      def up_nand():
        s.nand_out |= ~(s.inv1_out & s.en)

      @update_delay(100)
      def up_inv0():
        s.inv0_out |= ~s.nand_out

      @update_delay(100)
      def up_inv1():
        s.inv1_out |= ~s.inv0_out

      s.out //= s.inv1_out

  x = Top()
  x.elaborate()
  x.apply( GenDAGPass() )
  x.apply( EventSchedulePass() )

  x.en @= 0
  x.sim_delay( 2000 )
  print("\nenable @= 1\n")
  x.en @= 1
  x.sim_delay( 2000 )

def test_clock_gen_modular():

  class Inverter(Component):
    def construct( s, delay ):
      s.in_ = InPort()
      s.out = OutPort()

      @update_delay(delay)
      def up_inverter():
        s.out |= ~s.in_

  class Nand(Component):
    def construct( s, delay ):
      s.in0 = InPort()
      s.in1 = InPort()
      s.out = OutPort()

      @update_delay(delay)
      def up_nand():
        s.out <<= ~(s.in0 & s.in1)

  class Top(Component):
    def construct( s ):
      s.en  = InPort()
      s.clk_out = OutPort()

      s.nand = Nand( delay=500 )
      s.invs = [ Inverter(delay=50) for _ in range(4) ]

      s.nand.in0 //= s.en
      s.nand.in1 //= s.invs[-1].out

      s.invs[0].in_ //= s.nand.out
      for i in range(3):
        s.invs[i].out //= s.invs[i+1].in_
      s.invs[-1].out //= s.clk_out

  x = Top()
  x.elaborate()
  x.apply( GenDAGPass() )
  x.apply( EventSchedulePass() )

  x.en @= 0
  x.sim_delay( 10000 )
  print("\nenable @= 1\n")
  x.en @= 1
  x.sim_delay( 10000 )

def test_d_latch():

  class PosTrigDLatch(Component):
    def construct( s, delay ):
      s.in_clk = InPort()
      s.D = InPort()
      s.Q = OutPort()

      @update_delay(delay)
      def update_dlatch():
        s.Q |= s.D if s.in_clk else s.Q

  x = PosTrigDLatch(delay=720)
  x.elaborate()
  x.apply( GenDAGPass() )
  x.apply( EventSchedulePass() )

  x.in_clk @= 0
  for i in range(10):
    x.D @= 1
    x.sim_delay( 50 )
    x.D @= 0
    x.sim_delay( 150 )
  print("gogogo")

  x.in_clk @= 1
  for i in range(10):
    x.D @= 1
    x.sim_delay( 50 )
    x.D @= 0
    x.sim_delay( 150 )
  x.in_clk @= 0
  # first cycle
  for i in range(10):
    x.D @= 1
    x.sim_delay( 50 )
    x.D @= 0
    x.sim_delay( 150 )

def test_DFF():

  class PosTrigDLatch(Component):
    def construct( s, delay ):
      s.in_clk = InPort()
      s.D = InPort()
      s.Q = OutPort()

      @update_delay(delay)
      def update_dlatch():
        s.Q |= s.D if s.in_clk else s.Q

  class DFF(Component):
    def construct( s ):
      s.in_clk = InPort()
      s.D = InPort()
      s.Q = OutPort()

      s.DL1 = PosTrigDLatch(delay=50)
      s.DL2 = PosTrigDLatch(delay=50)

      s.DL1.in_clk //= lambda: ~s.in_clk
      s.DL2.in_clk //= lambda: s.in_clk
      s.D //= s.DL1.D
      s.DL1.Q //= s.DL2.D
      s.DL2.Q //= s.Q

  x = DFF()
  x.elaborate()
  x.apply( GenDAGPass() )
  x.apply( EventSchedulePass() )

  x.in_clk @= 0
  x.D @= 1
  x.sim_delay(1000)
  x.in_clk @= 1

  for i in range(10):
    x.D @= 1
    x.sim_delay( 50 )
    x.D @= 0
    x.sim_delay( 150 )

  x.in_clk @= 0

  for i in range(10):
    x.D @= 1
    x.sim_delay( 50 )
    x.D @= 0
    x.sim_delay( 150 )

  x.in_clk @= 1

  for i in range(10):
    x.D @= 1
    x.sim_delay( 50 )
    x.D @= 0
    x.sim_delay( 150 )

  x.in_clk @= 0

  for i in range(10):
    x.D @= 0
    x.sim_delay( 50 )
    x.D @= 1
    x.sim_delay( 150 )

  x.in_clk @= 1

  for i in range(10):
    x.D @= 1
    x.sim_delay( 50 )
    x.D @= 0
    x.sim_delay( 150 )

