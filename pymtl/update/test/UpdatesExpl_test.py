from pymtl import *

from pclib.update_impl import TestSourceExpl as TestSource
from pclib.update_impl import TestSinkExpl as TestSink

def test_bb():

  class Top(UpdatesExpl):

    def __init__( s ):

      @s.update
      def upA():
        pass

      @s.update
      def upB():
        pass

      s.add_constraints(
        U(upA) < U(upB),
      )

  A = Top()
  A.elaborate()

def test_bb_cyclic_dependency():

  class Top(UpdatesExpl):

    def __init__( s ):

      @s.update
      def upA():
        pass

      @s.update
      def upB():
        pass

      s.add_constraints(
        U(upA) < U(upB),
        U(upB) < U(upA),
      )

  A = Top()
  try:
    A.elaborate()
  except Exception:
    return
  raise Exception("Should've thrown cyclic dependency exception.")

def test_upblock_same_name():

  class Top(UpdatesExpl):

    def __init__( s ):

      @s.update
      def upA():
        pass

      @s.update
      def upA():
        pass

  try:
    A = Top()
  except Exception:
    return
  raise Exception("Should've thrown name conflict exception.")

def test_add_loopback():

  class Top(UpdatesExpl):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1] )
      s.sink = TestSink  ( ["?",(4+1),(3+1)+(4+1),(2+1)+(3+1)+(4+1),(1+1)+(2+1)+(3+1)+(4+1)] )

      s.wire0 = 0
      s.wire1 = 0

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      up_src = s.src.get_update_block("up_src")

      s.add_constraints(
        U(up_src) < U(up_from_src),
      )

      s.reg0 = 0

      @s.update
      def upA():
        s.reg0 = s.wire0 + s.wire1

      @s.update
      def up_to_sink_and_loop_back():
        s.sink.in_ = s.reg0
        s.wire1 = s.reg0

      s.add_constraints(
        U(upA) < U(up_to_sink_and_loop_back),
        U(upA) < U(up_from_src),
      )

      up_sink = s.sink.get_update_block("up_sink")

      s.add_constraints(
        U(up_to_sink_and_loop_back) < U(up_sink),
      )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0=%s > r0=%s > w1=%s" % (s.wire0,s.reg0,s.wire1) + \
             " >>> " + s.sink.line_trace()

  A = Top()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()

def test_lots_of_fan():

  class Top(UpdatesExpl):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( ["?",(5+6+6+7),(4+5+5+6),(3+4+4+5),(2+3+3+4),
                                (5+6+6+7),(4+5+5+6),(3+4+4+5),(2+3+3+4)] )

      s.wire0 = 0

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      up_src = s.src.get_update_block("up_src")

      s.add_constraints(
        U(up_src) < U(up_from_src),
      )

      s.reg = 0

      @s.update
      def up_reg():
        s.reg = s.wire0

      s.wire1 = s.wire2 = 0

      @s.update
      def upA():
        s.wire1 = s.reg
        s.wire2 = s.reg + 1

      s.add_constraints(
        U(up_reg) < U(upA),
        U(up_reg) < U(up_from_src),
      )

      s.wire3 = s.wire4 = 0

      @s.update
      def upB():
        s.wire3 = s.wire1
        s.wire4 = s.wire1 + 1

      s.wire5 = s.wire6 = 0

      @s.update
      def upC():
        s.wire5 = s.wire2
        s.wire6 = s.wire2 + 1

      s.add_constraints(
        U(upA) < U(upB),
        U(upA) < U(upC),
      )
      s.wire7 = s.wire8 = 0

      @s.update
      def upD():
        s.wire7 = s.wire3 + s.wire6
        s.wire8 = s.wire4 + s.wire5

      s.add_constraints(
        U(upB) < U(upD),
        U(upC) < U(upD),
      )

      @s.update
      def up_to_sink():
        s.sink.in_ = s.wire7 + s.wire8

      up_sink = s.sink.get_update_block("up_sink")

      s.add_constraints(
        U(upD) < U(up_to_sink),
        U(up_to_sink) < U(up_sink),
      )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0=%s > r0=%s" % (s.wire0,s.reg) + \
             " >>> " + s.sink.line_trace()

  A = Top()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()
