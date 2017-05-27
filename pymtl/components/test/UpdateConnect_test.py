from pymtl import *
from pclib.rtl import TestBasicSource as TestSource, TestBasicSink as TestSink
from pclib.rtl import Mux
from collections import deque

def simulate( cls ):
  A = cls()
  sim = SimLevel3( A )

  while not A.done():
    sim.tick()
    print A.line_trace()

def test_connect_list_int_idx():

  class Top(UpdateConnect):

    def __init__( s ):

      s.src_in0 = TestSource( [4,3,2,1] )
      s.src_in1 = TestSource( [8,7,6,5] )
      s.src_sel = TestSource( [1,0,1,0] )
      s.sink    = TestSink  ( [8,3,6,1] )

      s.mux = Mux(int, 2)

      # All constraints are within TestSource, TestSink, and Mux

      s.connect( s.mux.in_[0], s.src_in0.out )
      s.connect( s.mux.in_[1], s.src_in1.out )
      s.connect( s.mux.sel,    s.src_sel.out )
      s.connect( s.sink.in_,   s.mux.out )

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  simulate( Top )

def test_2d_array_vars_connect_impl():

  class Top(UpdateConnect):

    def __init__( s ):

      s.src  = TestSource( [2,1,0,2,1,0] )
      s.sink = TestSink  ( ["*",(5+6),(3+4),(1+2),
                                (5+6),(3+4),(1+2)] )

      s.wire = [ [ Wire(int) for _ in xrange(2)] for _ in xrange(2) ]
      s.connect( s.wire[0][0], s.src.out )

      @s.update
      def up_from_src():
        s.wire[0][1] = s.src.out + 1

      s.reg = Wire(int)
      s.connect( s.wire[1][0], s.reg )

      @s.update_on_edge
      def up_reg():
        s.reg = s.wire[0][0] + s.wire[0][1]

      @s.update
      def upA():
        s.wire[1][1] = s.reg + 1

      @s.update
      def up_to_sink():
        s.sink.in_ = s.wire[1][0] + s.wire[1][1]

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
             str(s.wire)+" r0=%s" % s.reg + \
             " >>> " + s.sink.line_trace()

  simulate( Top )

def test_lots_of_fan_connect():

  class Top(UpdateConnect):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( ["?",(5+5+6+6),(4+4+5+5),(3+3+4+4),(2+2+3+3),
                                (5+5+6+6),(4+4+5+5),(3+3+4+4),(2+2+3+3)] )

      s.wire0 = Wire(int)

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      s.reg = Wire(int)

      @s.update_on_edge
      def up_reg():
        s.reg = s.wire0

      s.wire1 = Wire(int)
      s.wire2 = Wire(int)

      s.connect( s.wire1, s.reg )

      @s.update
      def upA():
        s.wire2 = s.reg + 1

      s.wire3 = Wire(int)
      s.wire4 = Wire(int)

      s.connect( s.wire3, s.wire1 )
      s.connect( s.wire4, s.wire1 )

      s.wire5 = Wire(int)
      s.wire6 = Wire(int)

      s.connect( s.wire5, s.wire2 )
      s.connect( s.wire6, s.wire2 )

      s.wire7 = Wire(int)
      s.wire8 = Wire(int)

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

  simulate( Top )

def test_connect_plain():

  class Top(UpdateConnect):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( [5,4,3,2,5,4,3,2] )

      s.wire0 = Wire(int)

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      s.connect( s.sink.in_, s.wire0 )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0=%s" % (s.wire0) + \
             " >>> " + s.sink.line_trace()

  simulate( Top )

def test_connect_list_int_idx():

  class Top(UpdateConnect):

    def __init__( s ):

      s.src_in0 = TestSource( [4,3,2,1] )
      s.src_in1 = TestSource( [8,7,6,5] )
      s.src_sel = TestSource( [1,0,1,0] )
      s.sink    = TestSink  ( [8,3,6,1] )

      s.mux = Mux(int, 2)

      # All constraints are within TestSource, TestSink, and Mux

      s.connect( s.mux.in_[0] , s.src_in0.out )
      s.connect( s.mux.in_[1] , s.src_in1.out )
      s.connect( s.mux.sel    , s.src_sel.out )
      s.connect( s.sink.in_   , s.mux.out     )

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  simulate( Top )

MUX_SEL_0 = 0
MUX_SEL_1 = 1

def test_connect_list_const_idx():

  class Top(UpdateConnect):

    def __init__( s ):

      s.src_in0 = TestSource( [4,3,2,1] )
      s.src_in1 = TestSource( [8,7,6,5] )
      s.src_sel = TestSource( [1,0,1,0] )
      s.sink    = TestSink  ( [8,3,6,1] )

      s.mux = Mux(int,2)

      s.connect( s.mux.in_[MUX_SEL_0], s.src_in0.out )
      s.connect( s.mux.in_[MUX_SEL_1], s.src_in1.out )
      s.connect( s.mux.sel           , s.src_sel.out )
      s.connect( s.sink.in_          , s.mux.out     )

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  simulate( Top )

def test_2d_array_vars_connect():

  class Top(UpdateConnect):

    def __init__( s ):

      s.src  = TestSource( [2,1,0,2,1,0] )
      s.sink = TestSink  ( ["?",(5+6),(3+4),(1+2),
                                (5+6),(3+4),(1+2)] )

      s.wire = [ [ Wire(int) for _ in xrange(2)] for _ in xrange(2) ]
      s.connect( s.wire[0][0], s.src.out )

      @s.update
      def up_from_src():
        s.wire[0][1] = s.src.out + 1

      s.reg = Wire(int)
      s.connect( s.wire[1][0], s.reg )

      @s.update
      def up_reg():
        s.reg = s.wire[0][0] + s.wire[0][1]

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

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
             str(s.wire)+" r0=%s" % s.reg + \
             " >>> " + s.sink.line_trace()

  simulate( Top )

def test_lots_of_fan_connect():

  class Top(UpdateConnect):

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

      s.connect( s.wire1, s.reg )

      @s.update
      def upA():
        s.wire2 = s.reg + 1

      s.add_constraints(
        U(upA) < RD(s.wire2),
      )

      s.wire3 = Wire(int)
      s.wire4 = Wire(int)

      s.connect( s.wire3, s.wire1 )
      s.connect( s.wire4, s.wire1 )

      s.wire5 = Wire(int)
      s.wire6 = Wire(int)

      s.connect( s.wire5, s.wire2 )
      s.connect( s.wire6, s.wire2 )

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

  simulate( Top )

