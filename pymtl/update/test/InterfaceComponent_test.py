from pymtl import *
from pclib.method import Reg
from pclib.update import TestSource
from pclib.update import TestSink

class Port(InterfaceComponent):

  def __init__( s, type_ ):
    s.value = type_()

    s.add_constraints(
      M(s.wr) < M(s.rd)
    )

  def wr( s, v ):
    s.value = v

  def rd( s ):
    return s.value

class Incr(MethodComponent):

  def __init__( s ):
    s.in_ = Port(int)
    s.reg = Reg()
    s.out = Port(int)

    @s.update
    def up_A():
      s.reg.wr( s.in_.rd() )

    @s.update
    def up_B():
      s.out.wr( s.reg.rd() + 1 )

  def line_trace( s ):
    return s.reg.line_trace()

def test_simple_ifcs():

  class Top(MethodComponent):

    def __init__( s ):
      s.src  = TestSource( [4,3,2,1] )
      s.sink = TestSink  ( ["?","?",6,5,4,3] )

      s.A1 = Incr()
      s.A2 = Incr()

      @s.update
      def up_from_src():
        s.A1.in_.wr( s.src.out )

      s.A1.out |= s.A2.in_

      @s.update
      def up_to_sink():
        s.sink.in_ = s.A2.out.rd()

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return  s.src.line_trace() + " >>> " + s.A1.line_trace() + \
              " > " + s.A2.line_trace() +\
              " >>> " + s.sink.line_trace()

  A = Top()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()

def test_ifcs_fanout():

  class Top(MethodComponent):

    def __init__( s ):
      s.src  = TestSource( [4,3,2,1] )
      s.sink = TestSink  ( ["?","?",12,10,8,6] )

      s.A1 = Incr()
      s.A2 = Incr()
      s.A3 = Incr()

      @s.update
      def up_from_src():
        s.A1.in_.wr( s.src.out )

      s.A1.out |= s.A2.in_
      s.A1.out |= s.A3.in_

      @s.update
      def up_to_sink():
        s.sink.in_ = s.A2.out.rd() + s.A3.out.rd()

    def line_trace( s ):
      return  s.src.line_trace() + " >>> " + s.A1.line_trace() + \
              " > " + s.A2.line_trace() +\
              " >>> " + s.sink.line_trace()

    def done( s ):
      return s.src.done() and s.sink.done()

  A = Top()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()
