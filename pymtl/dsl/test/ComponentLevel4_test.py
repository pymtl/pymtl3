#=========================================================================
# ComponentLevel3_test.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Dec 25, 2017

from pymtl import *
from pymtl.dsl import ComponentLevel4
from sim_utils import simple_sim_pass
from collections import deque

def _test_model( cls ):
  A = cls()
  A.elaborate()
  simple_sim_pass( A, 0x123 )
  print A._schedule

  T, time = 0, 20
  while not A.done() and T < time:
    A.tick()
    print A.line_trace()
    T += 1

class SimpleReg( ComponentLevel4 ):

  def construct( s ):
    s.read  = CalleePort( s.rd )
    s.write = CalleePort( s.wr )

    s.v = 0

    s.add_constraints(
      M(s.rd) < M(s.wr),
    )

  def wr( s, v ):
    s.v = v

  def rd( s ):
    return s.v

  def line_trace( s ):
    return "%d" % s.v

class SimpleWire( ComponentLevel4 ):

  def construct( s ):
    s.read  = CalleePort( s.rd )
    s.write = CalleePort( s.wr )

    s.v = 0

    s.add_constraints(
      M(s.rd) > M(s.wr),
    )

  def wr( s, v ):
    s.v = v

  def rd( s ):
    return s.v

  def line_trace( s ):
    return "%d" % s.v

def test_2regs():

  class Top( ComponentLevel4 ):

    def construct( s ):
      s.in_ = Wire(int)

      @s.update
      def up_src():
        s.in_ += 1

      s.reg0 = SimpleReg()

      @s.update
      def up_plus_one_to_reg0():
        s.reg0.write( s.in_ + 1 )

      s.reg1 = SimpleReg()

      @s.update
      def up_reg0_to_reg1():
        s.reg1.write( s.reg0.read() + 1)

      s.out = Wire(int)
      @s.update
      def up_sink():
        s.out = s.reg1.read()

    def done( s ):
      return s.in_ >= 5

    def line_trace( s ):
      return  "in=%d" % s.in_ + " >>> " + s.reg0.line_trace() + \
              " > " + s.reg1.line_trace() +\
              " >>> " + "out=%d" % s.out


  _test_model( Top )
