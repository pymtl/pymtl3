from pymtl import *

from pclib.update import TestSource as TestSource
from pclib.update import TestSink as TestSink

def test_connect():

  class Top(Updates):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( [5,4,3,2,5,4,3,2] )

      s.wire0 = 0

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      s.wire0 |= s.sink.in_

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0=%s" % (s.wire0) + \
             " >>> " + s.sink.line_trace()

  A = Top()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()

def test_lots_of_fan_on_edge_connect():

  class Top(Updates):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( ["?",(5+5+6+6),(4+4+5+5),(3+3+4+4),(2+2+3+3),
                                (5+5+6+6),(4+4+5+5),(3+3+4+4),(2+2+3+3)] )

      s.wire0 = 0

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      s.reg = 0

      @s.update_on_edge
      def up_reg():
        s.reg = s.wire0

      s.wire1 = s.wire2 = 0
      s.wire1 |= s.reg

      @s.update
      def upA():
        s.wire2 = s.reg + 1

      s.wire3 = s.wire4 = 0

      s.wire3 |= s.wire1
      s.wire4 |= s.wire1

      s.wire5 = s.wire6 = 0

      s.wire5 |= s.wire2
      s.wire6 |= s.wire2

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
