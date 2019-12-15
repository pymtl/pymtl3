#=========================================================================
# DynamicSchedulePass_test.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Apr 19, 2019

from pymtl3.datatypes import Bits8, Bits32, bitstruct
from pymtl3.dsl import *
from pymtl3.dsl.errors import UpblkCyclicError

from ..AutoEvalPass import AutoEvalPass
from ..GenDAGPass import GenDAGPass
from ..SimpleSchedulePass import SimpleSchedulePass
from ..SimpleTickPass import SimpleTickPass

class Adder(Component):
  def construct( s ):
    s.in0 = InPort( Bits32 )
    s.in1 = InPort( Bits32 )
    s.out = OutPort( Bits32 )
    @s.update
    def add():
      s.out = s.in0 + s.in1

def test_comb_adder():
  a = Adder()
  a.elaborate()
  a.apply( GenDAGPass() )
  a.apply( SimpleSchedulePass() )
  a.apply( SimpleTickPass() )
  a.apply( AutoEvalPass() )
  a.lock_in_simulation()
  a.tick()

  assert not a._autoeval.need_eval_comb

  a.in0 = Bits32(10)
  assert a._autoeval.need_eval_comb

  a.in1 = Bits32(10)
  assert a._autoeval.need_eval_comb

  # NO need to call eval_combinational!
  assert a.out == 20
  assert not a._autoeval.need_eval_comb

  assert a.out == 20
  assert not a._autoeval.need_eval_comb

class WrapAdder(Component):
  def construct( s ):
    s.in0 = InPort( Bits32 )
    s.in1 = InPort( Bits32 )
    s.out = OutPort( Bits32 )

    s.adder = Adder()( in0 = s.in0, in1 = s.in1, out = s.out )

def test_wrapped_comb_adder():
  a = WrapAdder()
  a.elaborate()
  a.apply( GenDAGPass() )
  a.apply( SimpleSchedulePass() )
  a.apply( SimpleTickPass() )
  a.apply( AutoEvalPass() )
  a.lock_in_simulation()

  assert not a._autoeval.need_eval_comb

  a.in0 = Bits32(10)
  assert a._autoeval.need_eval_comb

  a.in1 = Bits32(10)
  assert a._autoeval.need_eval_comb

  # NO need to call eval_combinational!
  assert a.out == 20
  assert not a._autoeval.need_eval_comb

  assert a.out == 20
  assert not a._autoeval.need_eval_comb
