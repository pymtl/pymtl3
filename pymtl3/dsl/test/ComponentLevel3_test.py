"""
========================================================================
ComponentLevel3_test.py
========================================================================

Author : Shunning Jiang
Date   : Dec 25, 2017
"""
from __future__ import absolute_import, division, print_function

from collections import deque

from pymtl3.datatypes import Bits8, Bits10, Bits32
from pymtl3.dsl.ComponentLevel3 import ComponentLevel3
from pymtl3.dsl.Connectable import InPort, OutPort, Wire
from pymtl3.dsl.ConstraintTypes import WR, U
from pymtl3.dsl.errors import InvalidConnectionError, MultiWriterError

from .sim_utils import simple_sim_pass


def _test_model( cls ):
  A = cls()
  A.elaborate()
  simple_sim_pass( A, 0x123 )

  T, time = 0, 20
  while not A.done() and T < time:
    A.tick()
    print(A.line_trace())
    T += 1

MUX_SEL_0 = 0
MUX_SEL_1 = 1

class TestSource( ComponentLevel3 ):

  def construct( s, Type, input_ ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!"

    s.Type = Type
    s.input_ = deque( input_ ) # deque.popleft() is faster
    s.out = OutPort( Type )

    @s.update
    def up_src():
      if not s.input_:
        s.out = s.Type()
      else:
        s.out = s.input_.popleft()

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return "%s" % s.out

class TestSink( ComponentLevel3 ):

  def construct( s, Type, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!"

    s.answer = deque( answer )
    s.in_ = InPort( Type )

    @s.update
    def up_sink():
      if not s.answer:
        assert False, "Simulation has ended"
      else:
        ref = s.answer.popleft()
        ans = s.in_

        assert ref == ans or ref == "*", "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.answer

  def line_trace( s ):
    return "%s" % s.in_

class Mux( ComponentLevel3 ):

  def construct( s, Type, ninputs ):
    s.in_ = [ InPort( Type ) for _ in xrange(ninputs) ]
    s.sel = InPort( int if Type is int else mk_bits( clog2(ninputs) ) )
    s.out = OutPort( Type )

    @s.update
    def up_mux():
      s.out = s.in_[ s.sel ]

  def line_trace( s ):  pass

def test_connect_list_const_idx():

  class Top(ComponentLevel3):

    def construct( s ):

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

    def construct( s ):

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

    def construct( s ):
      s.in_ = [ InPort(int) for _ in xrange(2) ]
      s.sel = InPort(int)
      s.out = OutPort(int)

      s.mux = Mux(int, 2)(
        out = s.out,
        in_ = { 0: s.in_[0], 1: s.in_[1] },
        sel = s.sel,
      )

  class Top(ComponentLevel3):

    def construct( s ):

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

    def construct( s ):
      s.in_ = [ InPort(int) for _ in xrange(2) ]
      s.sel = InPort(int)
      s.out = OutPort(int)

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

    def construct( s ):

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

    def construct( s ):

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

    def construct( s ):

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

    def construct( s ):

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

    def construct( s ):

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

    def construct( s ):

      s.a = Wire(int)
      s.connect( s.a, 0 )

      @s.update
      def up_printa():
        print(s.a)

    def done( s ):
      return False

    def line_trace( s ):
      return ""

  _test_model( Top )

def test_connect_const_two_writer():

  class Top(ComponentLevel3):

    def construct( s ):

      s.a = Wire(int)
      s.connect( s.a, 0 )

      @s.update
      def up_printa():
        print(s.a)

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
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")

def test_connect_list_idx_call():

  class Top(ComponentLevel3):

    def construct( s ):

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

def test_connect_list_idx_const_in_call():

  class Top(ComponentLevel3):

    def construct( s ):

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

  _test_model( Top )

def test_top_level_inport():

  class Top( ComponentLevel3 ):

    def construct( s ):

      s.a = InPort(Bits10)
      s.b = Wire(Bits32)
      s.connect( s.a, s.b[0:10] )

      @s.update
      def up():
        print(s.b[10:32])

    def done( s ):
      return False

    def line_trace( s ):
      return ""

  _test_model( Top )

def test_top_level_outport():

  class Top( ComponentLevel3 ):

    def construct( s ):

      s.a = OutPort(Bits10)
      s.b = Wire(Bits32)
      s.connect( s.a, s.b[9:19] )

      @s.update
      def up():
        s.b[0:10] = 1023

    def done( s ):
      return False

    def line_trace( s ):
      return str(int(s.a))

  A = Top()
  A.elaborate()
  simple_sim_pass( A )

  A.tick()
  trace = A.line_trace()
  print(" >>>", trace)
  assert trace == "1"

# This is a simplified test case from Peitian

def test_multiple_slices_are_net_writers():

  class A( ComponentLevel3 ):

    def construct( s ):
      s.in_  = InPort( Bits32 )
      s.out1 = OutPort( Bits8 )
      s.out2 = OutPort( Bits8 )

      s.connect( s.in_[0:8], s.out1[0:8] )
      s.connect( s.in_[0:4], s.out2[0:4] )

  a = A()
  a.elaborate()

# A similar case for struct

def test_multiple_fields_are_net_writers():

  class SomeMsg1( object ):
    def __init__( s, a=0, b=0 ):
      s.a = Bits8(a)
      s.b = Bits32(b)

  class SomeMsg2( object ):
    def __init__( s, a=0 ):
      s.c = Bits8(a)

  class A( ComponentLevel3 ):

    def construct( s ):
      s.in_  = InPort( SomeMsg1 )
      s.out1 = OutPort( SomeMsg2 )
      s.out2 = OutPort( SomeMsg2 )

      s.connect( s.in_.a, s.out1.c )
      s.connect( s.in_.b[0:8], s.out2.c )

  a = A()
  a.elaborate()
  simple_sim_pass( a )

  a.in_ = SomeMsg1(4, 5)
  a.tick()
  assert a.out1.c == 4

# The counterpart of the above test

def test_multiple_fields_are_assigned():

  class SomeMsg1( object ):
    def __init__( s, a=0, b=0 ):
      s.a = Bits8(a)
      s.b = Bits32(b)

  class SomeMsg2( object ):
    def __init__( s, a=0 ):
      s.c = Bits8(a)

  class A( ComponentLevel3 ):

    def construct( s ):
      s.in_  = InPort( SomeMsg1 )
      s.out1 = OutPort( SomeMsg2 )
      s.out2 = OutPort( SomeMsg2 )

      # s.connect( s.in_.a, s.out1.c )
      # s.connect( s.in_.b[0:8], s.out2.c )
      @s.update
      def up_pass():
        s.out1.c = s.in_.a
        s.out2.c = s.in_.b[0:8]

  a = A()
  a.elaborate()
  simple_sim_pass( a )

  a.in_ = SomeMsg1(4, 5)
  a.tick()
  assert a.out1.c == 4

def test_const_connect_struct_signal_to_int():

  class SomeMsg1( object ):
    def __init__( s, a=0, b=0 ):
      s.a = Bits8(a)
      s.b = Bits32(b)

    def __eq__( s, other ):
      return s.a == other.a and s.b == other.b

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.wire = Wire(SomeMsg1)
      s.connect( s.wire, 1 )

  try:
    x = Top()
    x.elaborate()
  except InvalidConnectionError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidConnectionError.")

def test_const_connect_struct_signal_to_Bits():

  class SomeMsg1( object ):
    def __init__( s, a=0, b=0 ):
      s.a = Bits8(a)
      s.b = Bits32(b)

    def __eq__( s, other ):
      return s.a == other.a and s.b == other.b

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.wire = Wire(SomeMsg1)
      s.connect( s.wire, Bits32(1) )

  try:
    x = Top()
    x.elaborate()
  except InvalidConnectionError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidConnectionError.")

def test_const_connect_Bits_signal_to_int():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.wire = Wire(Bits32)
      s.connect( s.wire, 1 )

  x = Top()
  x.elaborate()
  print(x._dsl.consts)
  assert len(x._dsl.consts) == 1

def test_const_connect_int_signal_to_int():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.wire = Wire(int)
      s.connect( s.wire, 1 )

  x = Top()
  x.elaborate()
  print(x._dsl.consts)
  assert len(x._dsl.consts) == 1

def test_const_connect_Bits_signal_to_Bits():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.wire = Wire(Bits32)
      s.connect( s.wire, Bits32(0) )

  x = Top()
  x.elaborate()
  print(x._dsl.consts)
  assert len(x._dsl.consts) == 1

def test_const_connect_Bits_signal_to_mismatch_Bits():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.wire = Wire(Bits32)
      s.connect( s.wire, Bits8(8) )

  try:
    x = Top()
    x.elaborate()
  except InvalidConnectionError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidConnectionError.")
