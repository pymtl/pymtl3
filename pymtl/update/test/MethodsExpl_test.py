from pymtl import *
from pclib.method import Reg

class Wire(MethodsExpl):

  def __init__( s ):
    s.v = 0

    s.add_constraints(
      M(s.wr) < M(s.rd),
    )

  def wr( s, v ):
    s.v = v

  def rd( s ):
    return s.v

  def line_trace( s ):
    return "%d" % s.v

class RegWire(MethodsExpl):

  def __init__( s ):
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

def test_2regs():

  class Top(MethodsExpl):

    def __init__( s ):
      s.inc = s.in_ = 0

      s.in_ |= s.inc

      @s.update
      def up_src():
        s.inc += 1

      s.reg0 = RegWire()

      @s.update
      def up_plus_one_to_reg0():
        s.reg0.wr( s.in_ + 1 )

      s.reg1 = Reg()

      @s.update
      def up_reg0_to_reg1():
        s.reg1.wr( min( 1000000, s.reg0.rd() ) ) 

      s.out = 0
      @s.update
      def up_sink():
        s.out = s.reg1.rd()

    def line_trace( s ):
      return  "in=%d" % s.in_ + " >>> " + s.reg0.line_trace() + \
              " > " + s.reg1.line_trace() +\
              " >>> " + "out=%d" % s.out

  A = Top()
  A.elaborate()
  A.print_schedule()

  for x in xrange(100):
    A.cycle()
    print A.line_trace()

def test_arr_of_2regs():

  class Top(MethodsExpl):

    def __init__( s ):
      s.inc = s.in_ = 0

      s.in_ |= s.inc

      @s.update
      def up_src():
        s.inc += 1

      s.reg = [ Reg() for _ in xrange(2) ]

      @s.update
      def up_plus_one_to_reg0():
        s.reg[0].wr( s.in_ + 1 )

      @s.update
      def up_reg0_to_reg1():
        s.reg[1].wr( s.reg[0].rd() )

      s.out = 0
      @s.update
      def up_sink():
        s.out = s.reg[1].rd()

    def line_trace( s ):
      return  "in=%d" % s.in_ + " >>> " + s.reg[0].line_trace() + \
              " > " + s.reg[1].line_trace() +\
              " >>> " + "out=%d" % s.out

  A = Top()
  A.elaborate()
  A.print_schedule()

  for x in xrange(100):
    A.cycle()
    print A.line_trace()

def test_add_loopback_implicit():

  from pclib.update import TestSource
  from pclib.update import TestSink

  class Top(MethodsExpl):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1] )
      s.sink = TestSink  ( ["?",(4+1),(3+1)+(4+1),(2+1)+(3+1)+(4+1),(1+1)+(2+1)+(3+1)+(4+1)] )

      s.reg0 = Reg()
      s.wire_back = 0
      s.sink.in_ |= s.wire_back

      @s.update
      def upA():
        tmp = s.src.out + 1
        s.reg0.wr( tmp + s.wire_back )

      @s.update
      def up_to_sink_and_loop_back():
        s.wire_back = s.reg0.rd()

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "reg=%s > w_back=%s" % (s.reg0.line_trace(),s.wire_back) + \
             " >>> " + s.sink.line_trace()

  A = Top()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()
