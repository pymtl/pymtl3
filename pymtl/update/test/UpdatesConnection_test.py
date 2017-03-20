from pymtl import *

from pclib.update_conn import TestSource
from pclib.update_conn import TestSink

def test_wire_up_constraint():

  class Top(UpdatesConnection):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( [5,4,3,2,5,4,3,2] )

      @s.update
      def up_from_src():
        s.sink.in_ = s.src.out + 1

      s.add_constraints(
        U(up_from_src) < RD(s.sink.in_),
      )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
             " >>> " + s.sink.line_trace()

  A = Top()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()

def test_connect_plain():

  class Top(UpdatesConnection):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( [5,4,3,2,5,4,3,2] )

      s.wire0 = Wire(int)

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      s.add_constraints(
        U(up_from_src) < RD(s.wire0),
      )

      s.sink.in_ |= s.wire0

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

def test_connect_list_int_idx():

  class Top(UpdatesConnection):

    def __init__( s ):

      s.src_in0 = TestSource( [4,3,2,1] )
      s.src_in1 = TestSource( [8,7,6,5] )
      s.src_sel = TestSource( [1,0,1,0] )
      s.sink    = TestSink  ( [8,3,6,1] )

      from pclib.update_conn import Mux
      s.mux = Mux(2)

      # All constraints are within TestSource, TestSink, and Mux

      s.mux.in_[0]  |= s.src_in0.out
      s.mux.in_[1]  |= s.src_in1.out
      s.mux.sel     |= s.src_sel.out
      s.sink.in_    |= s.mux.out

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  A = Top()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()

MUX_SEL_0 = 0
MUX_SEL_1 = 1

def test_connect_list_const_idx():

  class Top(UpdatesConnection):

    def __init__( s ):

      s.src_in0 = TestSource( [4,3,2,1] )
      s.src_in1 = TestSource( [8,7,6,5] )
      s.src_sel = TestSource( [1,0,1,0] )
      s.sink    = TestSink  ( [8,3,6,1] )

      from pclib.update_conn import Mux
      s.mux = Mux(2)

      s.mux.in_[MUX_SEL_0] |= s.src_in0.out
      s.mux.in_[MUX_SEL_1] |= s.src_in1.out
      s.mux.sel            |= s.src_sel.out
      s.sink.in_           |= s.mux.out

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  A = Top()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()

def test_2d_array_vars():

  class Top(UpdatesConnection):

    def __init__( s ):

      s.src  = TestSource( [2,1,0,2,1,0] )
      s.sink = TestSink  ( ["?",(5+6),(3+4),(1+2),
                                (5+6),(3+4),(1+2)] )

      s.wire = [ [ Wire(int) for _ in xrange(2)] for _ in xrange(2) ]

      @s.update
      def up_from_src():
        s.wire[0][0] = s.src.out
        s.wire[0][1] = s.src.out + 1

      s.reg = Wire(int)

      @s.update
      def up_reg():
        s.reg = s.wire[0][0] + s.wire[0][1]

      s.add_constraints(
        U(up_reg) < RD(s.reg), # up_reg writes s.reg
      )

      @s.update
      def upA():
        for i in xrange(2):
          s.wire[1][i] = s.reg + i

      for i in xrange(2):
        s.add_constraints(
          U(up_reg) < WR(s.wire[0][i]), # up_reg reads  s.wire[0][i]
        )

      @s.update
      def up_to_sink():
        s.sink.in_ = s.wire[1][0] + s.wire[1][1]

      up_sink = s.sink.get_update_block("up_sink")

      s.add_constraints(
        U(upA)        < U(up_to_sink),
        U(up_to_sink) < U(up_sink),
      )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
             str(s.wire)+"r0=%s" % s.reg + \
             " >>> " + s.sink.line_trace()

  A = Top()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()

def test_2d_array_vars_connect():

  class Top(UpdatesConnection):

    def __init__( s ):

      s.src  = TestSource( [2,1,0,2,1,0] )
      s.sink = TestSink  ( ["?",(5+6),(3+4),(1+2),
                                (5+6),(3+4),(1+2)] )

      s.wire = [ [ Wire(int) for _ in xrange(2)] for _ in xrange(2) ]
      s.wire[0][0] |= s.src.out

      @s.update
      def up_from_src():
        s.wire[0][1] = s.src.out + 1

      s.reg = Wire(int)
      s.wire[1][0] |= s.reg

      @s.update
      def up_reg():
        s.reg = s.wire[0][0] + s.wire[0][1]

      s.add_constraints(
        U(up_reg) < RD(s.reg), # up_reg writes s.reg
      )
      for i in xrange(2):
        s.add_constraints(
          U(up_reg) < WR(s.wire[0][i]), # up_reg reads  s.wire[0][i]
        )

      @s.update
      def upA():
        s.wire[1][1] = s.reg + 1

      @s.update
      def up_to_sink():
        s.sink.in_ = s.wire[1][0] + s.wire[1][1]

      for i in xrange(2):
        s.add_constraints(
          WR(s.wire[1][i]) < U(up_to_sink),
        )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
             str(s.wire)+" r0=%s" % s.reg + \
             " >>> " + s.sink.line_trace()

  A = Top()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()

def test_lots_of_fan_connect():

  class Top(UpdatesConnection):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( ["?",(5+5+6+6),(4+4+5+5),(3+3+4+4),(2+2+3+3),
                                (5+5+6+6),(4+4+5+5),(3+3+4+4),(2+2+3+3)] )

      s.wire0 = Wire(int)

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      s.reg = Wire(int)

      @s.update
      def up_reg():
        s.reg = s.wire0

      s.add_constraints(
        U(up_reg) < WR(s.wire0),
        U(up_reg) < RD(s.reg),
      )

      s.wire1 = Wire(int)
      s.wire2 = Wire(int)

      s.wire1 |= s.reg

      @s.update
      def upA():
        s.wire2 = s.reg + 1

      s.add_constraints(
        U(upA) < RD(s.wire2),
      )

      s.wire3 = Wire(int)
      s.wire4 = Wire(int)

      s.wire3 |= s.wire1
      s.wire4 |= s.wire1

      s.wire5 = Wire(int)
      s.wire6 = Wire(int)

      s.wire5 |= s.wire2
      s.wire6 |= s.wire2

      s.wire7 = Wire(int)
      s.wire8 = Wire(int)

      @s.update
      def upD():
        s.wire7 = s.wire3 + s.wire6
        s.wire8 = s.wire4 + s.wire5

      s.add_constraints(
        WR(s.wire3) < U(upD),
        WR(s.wire4) < U(upD),
        WR(s.wire5) < U(upD),
        WR(s.wire6) < U(upD),
        U(upD) < RD(s.wire7),
        U(upD) < RD(s.wire8),
      )

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
