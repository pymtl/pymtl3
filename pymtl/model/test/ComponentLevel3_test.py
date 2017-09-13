from pymtl import *
from pymtl.model import ComponentLevel3
from pymtl.model.errors import MultiWriterError, InvalidConnectionError
from pclib.rtl import TestBasicSource as TestSource, TestBasicSink as TestSink
from pclib.rtl import Mux
from sim_utils import simple_sim_pass

def _test_model( cls ):
  A = cls()
  A.elaborate()
  simple_sim_pass( A, 0x123 )

  T, time = 0, 20
  while not A.done() and T < time:
    A.tick()
    print A.line_trace()
    T += 1

MUX_SEL_0 = 0
MUX_SEL_1 = 1

def test_connect_list_const_idx():

  class Top(ComponentLevel3):

    def __init__( s ):

      s.src_in0 = TestSource( int, [4,3,2,1] )
      s.src_in1 = TestSource( int, [8,7,6,5] )
      s.src_sel = TestSource( int, [1,0,1,0] )
      s.sink    = TestSink  ( int, [8,3,6,1] )

      s.mux = Mux(int, 2)

      s.connect( s.mux.in_[MUX_SEL_0], s.src_in0.out )
      s.connect( s.mux.in_[MUX_SEL_1], s.src_in1.out )
      s.connect( s.mux.sel           , s.src_sel.out )
      s.connect( s.sink.in_          , s.mux.out     )

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_connect_list_idx_call():

  class Top(ComponentLevel3):

    def __init__( s ):

      s.src_in0 = TestSource( int, [4,3,2,1] )
      s.src_in1 = TestSource( int, [8,7,6,5] )
      s.src_sel = TestSource( int, [1,0,1,0] )
      s.sink    = TestSink  ( int, [8,3,6,1] )

      s.mux = Mux(int, 2)(
        out = s.sink.in_,
        in_ = { MUX_SEL_0: s.src_in0.out, MUX_SEL_1: s.src_in1.out },
        sel = s.src_sel.out,
      )

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_connect_deep():

  class MuxWrap(ComponentLevel3):

    def __init__( s ):
      s.in_ = [ InVPort(int) for _ in xrange(2) ]
      s.sel = InVPort(int)
      s.out = OutVPort(int)

      s.mux = Mux(int, 2)(
        out = s.out,
        in_ = { 0: s.in_[0], 1: s.in_[1] },
        sel = s.sel,
      )

  class Top(ComponentLevel3):

    def __init__( s ):

      s.src_in0 = TestSource( int, [4,3,2,1] )
      s.src_in1 = TestSource( int, [8,7,6,5] )
      s.src_sel = TestSource( int, [1,0,1,0] )
      s.sink    = TestSink  ( int, [8,3,6,1] )

      s.mux_wrap = MuxWrap()(
        out = s.sink.in_,
        in_ = { 0: s.src_in0.out, 1: s.src_in1.out },
        sel = s.src_sel.out,
      )

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_deep_connect():

  class MuxWrap3(ComponentLevel3):

    def __init__( s ):
      s.in_ = [ InVPort(int) for _ in xrange(2) ]
      s.sel = InVPort(int)
      s.out = OutVPort(int)

      s.mux1 = Mux(int, 2)(
        in_ = { 0: s.in_[0], 1: s.in_[1] },
        sel = s.sel,
      )
      s.mux2 = Mux(int, 2)(
        in_ = { 0: s.in_[0], 1: s.in_[1] },
        sel = s.sel,
      )
      s.mux3 = Mux(int, 2)(
        out = s.out,
        in_ = { 0: s.mux1.out, 1: s.mux2.out },
        sel = s.sel,
      )

  class Top(ComponentLevel3):

    def __init__( s ):

      s.src_in0 = TestSource( int, [4,3,2,1] )
      s.src_in1 = TestSource( int, [8,7,6,5] )
      s.src_sel = TestSource( int, [1,0,1,0] )
      s.sink    = TestSink  ( int, [8,3,6,1] )

      s.mux_wrap = MuxWrap3()(
        out = s.sink.in_,
        in_ = { 0: s.src_in0.out, 1: s.src_in1.out },
        sel = s.src_sel.out,
      )

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_2d_array_vars_connect_impl():

  class Top(ComponentLevel3):

    def __init__( s ):

      s.src  = TestSource( int, [2,1,0,2,1,0] )
      s.sink = TestSink  ( int, ["*",(5+6),(3+4),(1+2),
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

  _test_model( Top )

def test_lots_of_fan_connect():

  class Top(ComponentLevel3):

    def __init__( s ):

      s.src  = TestSource( int, [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( int, ["*",(5+5+6+6),(4+4+5+5),(3+3+4+4),(2+2+3+3),
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

  _test_model( Top )

def test_connect_plain():

  class Top(ComponentLevel3):

    def __init__( s ):

      s.src  = TestSource( int, [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( int, [5,4,3,2,5,4,3,2] )

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

  _test_model( Top )

def test_2d_array_vars_connect():

  class Top(ComponentLevel3):

    def __init__( s ):

      s.src  = TestSource( int, [2,1,0,2,1,0] )
      s.sink = TestSink  ( int, ["*",(5+6),(3+4),(1+2),
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

  _test_model( Top )

def test_connect_const_same_level():

  class Top(ComponentLevel3):

    def __init__( s ):

      s.a = Wire(int)
      s.connect( s.a, 0 )

      @s.update
      def up_printa():
        print s.a

    def done( s ):
      return False

    def line_trace( s ):
      return ""

  _test_model( Top )

def test_connect_const_two_writer():

  class Top(ComponentLevel3):

    def __init__( s ):

      s.a = Wire(int)
      s.connect( s.a, 0 )

      @s.update
      def up_printa():
        print s.a

      @s.update
      def up_writea():
        s.a = 123

    def done( s ):
      return False

    def line_trace( s ):
      return ""

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print "{} is thrown\n{}".format( e.__class__.__name__, e )
    return
  raise Exception("Should've thrown MultiWriterError.")

def test_connect_list_idx_call():

  class Top(ComponentLevel3):

    def __init__( s ):

      s.src_in0 = TestSource( int, [4,3,2,1] )
      s.src_sel = TestSource( int, [1,0,1,0] )
      s.sink    = TestSink  ( int, [12,3,12,1] )

      s.mux = Mux(int, 2)(
        out = s.sink.in_,
        in_ = { MUX_SEL_0: s.src_in0.out },
        sel = s.src_sel.out,
      )
      s.connect( s.mux.in_[MUX_SEL_1], 12 )

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_connect_list_idx_invalid_call():

  class Top(ComponentLevel3):

    def __init__( s ):

      s.src_in0 = TestSource( int, [4,3,2,1] )
      s.src_sel = TestSource( int, [1,0,1,0] )
      s.sink    = TestSink  ( int, [12,3,12,1] )

      s.mux = Mux(int, 2)(
        out = s.sink.in_,
        in_ = { MUX_SEL_0: s.src_in0.out, MUX_SEL_1: 12 },
        sel = s.src_sel.out,
      )

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  try:
    _test_model( Top )
  except InvalidConnectionError as e:
    print "{} is thrown\n{}".format( e.__class__.__name__, e )
    return
  raise Exception("Should've thrown InvalidConnectionError.")

def test_top_level_inport():

  class Top( ComponentLevel3 ):

    def __init__( s ):

      s.a = InVPort(Bits10)
      s.b = Wire(Bits32)
      s.connect( s.a, s.b[0:10] )

      @s.update
      def up():
        print s.b[10:32]

    def done( s ):
      return False

    def line_trace( s ):
      return ""

  _test_model( Top )

def test_top_level_outport():

  class Top( ComponentLevel3 ):

    def __init__( s ):

      s.a = OutVPort(Bits10)
      s.b = Wire(Bits32)
      s.connect( s.a, s.b[9:19] )

      @s.update
      def up():
        s.b[0:10] = 1023

    def done( s ):
      return False

    def line_trace( s ):
      return str(s.a)

  A = Top()
  A.elaborate()
  simple_sim_pass( A )

  A.tick()
  trace = A.line_trace()
  print " >>>", trace
  assert trace == "001"
