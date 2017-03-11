from pymtl import *

from pclib.update_impl import TestSourceImpl as TestSource
from pclib.update_impl import TestSinkImpl as TestSink

def test_bb():

  class Top(UpdatesImpl):

    def __init__( s ):

      s.a = s.b = 0

      @s.update
      def upA():
        s.a = s.b + 1

      @s.update
      def upB():
        s.b = s.b + 1

  A = Top()
  A.elaborate()

def test_bb_cyclic_dependency():

  class Top(UpdatesImpl):

    def __init__( s ):
      s.a = s.b = 0

      @s.update
      def upA():
        s.a = s.b

      @s.update
      def upB():
        s.b = s.a

  A = Top()
  try:
    A.elaborate()
  except Exception:
    return
  raise Exception("Should've thrown cyclic dependency exception.")

def test_add_loopback():

  class Top(UpdatesImpl):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1] )
      s.sink = TestSink  ( ["?",(4+1),(3+1)+(4+1),(2+1)+(3+1)+(4+1),(1+1)+(2+1)+(3+1)+(4+1)] )

      s.wire0 = 0
      s.wire1 = 0

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

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

def test_add_loopback_on_edge():

  class Top(UpdatesImpl):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1] )
      s.sink = TestSink  ( ["?",(4+1),(3+1)+(4+1),(2+1)+(3+1)+(4+1),(1+1)+(2+1)+(3+1)+(4+1)] )

      s.wire0 = 0
      s.wire1 = 0

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      s.reg0 = 0

      # UPDATE ON EDGE!
      @s.update_on_edge
      def upA():
        s.reg0 = s.wire0 + s.wire1

      @s.update
      def up_to_sink_and_loop_back():
        s.sink.in_ = s.reg0
        s.wire1 = s.reg0

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

  class Top(UpdatesImpl):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( ["?",(5+6+6+7),(4+5+5+6),(3+4+4+5),(2+3+3+4),
                                (5+6+6+7),(4+5+5+6),(3+4+4+5),(2+3+3+4)] )

      s.wire0 = 0

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

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

      s.wire7 = s.wire8 = 0

      @s.update
      def upD():
        s.wire7 = s.wire3 + s.wire6
        s.wire8 = s.wire4 + s.wire5

      @s.update
      def up_to_sink():
        s.sink.in_ = s.wire7 + s.wire8

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

def test_lots_of_fan_on_edge():

  class Top(UpdatesImpl):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( ["?",(5+6+6+7),(4+5+5+6),(3+4+4+5),(2+3+3+4),
                                (5+6+6+7),(4+5+5+6),(3+4+4+5),(2+3+3+4)] )

      s.wire0 = 0

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      s.reg = 0

      @s.update_on_edge
      def up_reg():
        s.reg = s.wire0

      s.wire1 = s.wire2 = 0

      @s.update
      def upA():
        s.wire1 = s.reg
        s.wire2 = s.reg + 1

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

      s.wire7 = s.wire8 = 0

      @s.update
      def upD():
        s.wire7 = s.wire3 + s.wire6
        s.wire8 = s.wire4 + s.wire5

      @s.update
      def up_to_sink():
        s.sink.in_ = s.wire7 + s.wire8

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
