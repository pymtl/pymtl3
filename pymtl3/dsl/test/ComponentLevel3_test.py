"""
========================================================================
ComponentLevel3_test.py
========================================================================

Author : Shunning Jiang
Date   : Dec 25, 2017
"""
from collections import deque

from pymtl3.datatypes import Bits1, Bits8, Bits10, Bits32, bitstruct, clog2, mk_bits
from pymtl3.dsl.ComponentLevel1 import update
from pymtl3.dsl.ComponentLevel2 import update_ff
from pymtl3.dsl.ComponentLevel3 import ComponentLevel3, connect
from pymtl3.dsl.Connectable import InPort, OutPort, Wire
from pymtl3.dsl.ConstraintTypes import WR, U
from pymtl3.dsl.errors import (
    InvalidConnectionError,
    MultiWriterError,
    PyMTLDeprecationError,
    UpblkFuncSameNameError,
)

from .sim_utils import simple_sim_pass


def _test_model( cls ):
  A = cls()
  A.elaborate()
  simple_sim_pass( A, 0x123 )
  A.tick()

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
    s.input_ = deque([ Type(x) for x in input_ ]) # deque.popleft() is faster

    s.out = OutPort(Type)

    @update
    def up_src():
      if not s.input_:
        s.out @= Type()
      else:
        s.out @= s.input_.popleft()

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return "%s" % s.out

class TestSink( ComponentLevel3 ):

  def construct( s, Type, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!"

    s.answer = deque( [ x if x == "*" else Type(x) for x in answer ] )
    s.in_ = InPort(Type)

    @update
    def up_sink():
      if not s.answer:
        assert False, "Simulation has ended"
      else:
        ref = s.answer.popleft()
        ans = s.in_

        assert ref == ans or ref == "*", "Expect {}, get {} instead".format(ref, ans)

  def done( s ):
    return not s.answer

  def line_trace( s ):
    return "%s" % s.in_

class Mux( ComponentLevel3 ):

  def construct( s, Type, ninputs ):
    s.in_ = [ InPort( Type ) for _ in range(ninputs) ]
    s.sel = InPort( mk_bits( clog2(ninputs) ) )
    s.out = OutPort( Type )

    @update
    def up_mux():
      s.out @= s.in_[ s.sel ]

  def line_trace( s ):  pass

def test_connect_list_const_idx():

  class Top(ComponentLevel3):

    def construct( s ):

      s.src_in0 = TestSource( Bits32, [4,3,2,1] )
      s.src_in1 = TestSource( Bits32, [8,7,6,5] )
      s.src_sel = TestSource( Bits1,  [1,0,1,0] )
      s.sink    = TestSink  ( Bits32, [8,3,6,1] )

      s.mux = Mux(Bits32, 2)

      connect( s.mux.in_[MUX_SEL_0], s.src_in0.out )
      connect( s.mux.in_[MUX_SEL_1], s.src_in1.out )
      connect( s.mux.sel           , s.src_sel.out )
      connect( s.sink.in_          , s.mux.out     )

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_connect_list_const_idx_ifloordiv_sugar():

  class Top(ComponentLevel3):

    def construct( s ):

      s.src_in0 = TestSource( Bits32, [4,3,2,1] )
      s.src_in1 = TestSource( Bits32, [8,7,6,5] )
      s.src_sel = TestSource( Bits1,  [1,0,1,0] )
      s.sink    = TestSink  ( Bits32, [8,3,6,1] )

      s.mux = Mux(Bits32, 2)

      s.mux.in_[MUX_SEL_0] //= s.src_in0.out
      s.mux.in_[MUX_SEL_1] //= s.src_in1.out
      s.mux.sel            //= s.src_sel.out
      s.sink.in_           //= s.mux.out

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_connect_deep():

  class MuxWrap(ComponentLevel3):

    def construct( s ):
      s.in_ = [ InPort(32) for _ in range(2) ]
      s.sel = InPort(1)
      s.out = OutPort(32)

      s.mux = Mux(Bits32, 2)
      s.mux.in_[0] //= s.in_[0]
      s.mux.in_[1] //= s.in_[1]
      s.mux.sel    //= s.sel
      s.out        //= s.mux.out

  class Top(ComponentLevel3):

    def construct( s ):

      s.src_in0 = TestSource( Bits32, [4,3,2,1] )
      s.src_in1 = TestSource( Bits32, [8,7,6,5] )
      s.src_sel = TestSource( Bits1, [1,0,1,0] )
      s.sink    = TestSink  ( Bits32, [8,3,6,1] )

      s.mux_wrap = m = MuxWrap()
      m.out    //= s.sink.in_
      m.in_[0] //= s.src_in0.out
      m.in_[1] //= s.src_in1.out
      m.sel    //= s.src_sel.out

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_deep_connect():

  class MuxWrap3(ComponentLevel3):

    def construct( s ):
      s.in_ = [ InPort(32) for _ in range(2) ]
      s.sel = InPort(1)
      s.out = OutPort(32)

      s.mux1 = Mux(Bits32, 2)
      s.mux1.in_[0] //= s.in_[0]
      s.mux1.in_[1] //= s.in_[1]
      s.mux1.sel //= s.sel

      s.mux2 = Mux(Bits32, 2)
      s.mux2.in_[0] //= s.in_[0]
      s.mux2.in_[1] //= s.in_[1]
      s.mux2.sel //= s.sel

      s.mux3 = Mux(Bits32, 2)
      s.mux3.in_[0] //= s.mux1.out
      s.mux3.in_[1] //= s.mux2.out
      s.mux3.sel //= s.sel
      s.mux3.out //= s.out

  class Top(ComponentLevel3):

    def construct( s ):

      s.src_in0 = TestSource( Bits32, [4,3,2,1] )
      s.src_in1 = TestSource( Bits32, [8,7,6,5] )
      s.src_sel = TestSource( Bits1, [1,0,1,0] )
      s.sink    = TestSink  ( Bits32, [8,3,6,1] )

      s.mux_wrap = MuxWrap3()

      s.mux_wrap.out //= s.sink.in_
      s.mux_wrap.in_[0] //= s.src_in0.out
      s.mux_wrap.in_[1] //= s.src_in1.out
      s.mux_wrap.sel //= s.src_sel.out

    def done( s ):
      return s.src_in0.done() and s.sink.done()

    def line_trace( s ):
      return " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_2d_array_vars_connect_impl():

  class Top(ComponentLevel3):

    def construct( s ):

      s.src  = TestSource( Bits32, [2,1,0,2,1,0] )
      s.sink = TestSink  ( Bits32, ["*",(5+6),(3+4),(1+2),
                                 (5+6),(3+4),(1+2)] )

      s.wire = [ [ Wire(Bits32) for _ in range(2)] for _ in range(2) ]
      connect( s.wire[0][0], s.src.out )

      @update
      def up_from_src():
        s.wire[0][1] @= s.src.out + 1

      s.reg = Wire(Bits32)
      connect( s.wire[1][0], s.reg )

      @update_ff
      def up_reg():
        s.reg <<= s.wire[0][0] + s.wire[0][1]

      @update
      def upA():
        s.wire[1][1] @= s.reg + 1

      @update
      def up_to_sink():
        s.sink.in_ @= s.wire[1][0] + s.wire[1][1]

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

      s.src  = TestSource( Bits32, [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( Bits32, ["*",(5+5+6+6),(4+4+5+5),(3+3+4+4),(2+2+3+3),
                                     (5+5+6+6),(4+4+5+5),(3+3+4+4),(2+2+3+3)] )

      s.wire0 = Wire(Bits32)

      @update
      def up_from_src():
        s.wire0 @= s.src.out + 1

      s.reg = Wire(Bits32)

      @update_ff
      def up_reg():
        s.reg <<= s.wire0

      s.wire1 = Wire(Bits32)
      s.wire2 = Wire(Bits32)

      connect( s.wire1, s.reg )

      @update
      def upA():
        s.wire2 @= s.reg + 1

      s.wire3 = Wire(Bits32)
      s.wire4 = Wire(Bits32)

      connect( s.wire3, s.wire1 )
      connect( s.wire4, s.wire1 )

      s.wire5 = Wire(Bits32)
      s.wire6 = Wire(Bits32)

      connect( s.wire5, s.wire2 )
      connect( s.wire6, s.wire2 )

      s.wire7 = Wire(Bits32)
      s.wire8 = Wire(Bits32)

      @update
      def upD():
        s.wire7 @= s.wire3 + s.wire6
        s.wire8 @= s.wire4 + s.wire5

      @update
      def up_to_sink():
        s.sink.in_ @= s.wire7 + s.wire8

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0={} > r0={}".format(s.wire0,s.reg) + \
             " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_connect_plain():

  class Top(ComponentLevel3):

    def construct( s ):

      s.src  = TestSource( Bits32, [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( Bits32, [5,4,3,2,5,4,3,2] )

      s.wire0 = Wire(32)

      @update
      def up_from_src():
        s.wire0 @= s.src.out + 1

      connect( s.sink.in_, s.wire0 )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0=%s" % (s.wire0) + \
             " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_2d_array_vars_connect2():

  class Top(ComponentLevel3):

    def construct( s ):

      s.src  = TestSource( Bits32, [2,1,0,2,1,0] )
      s.sink = TestSink  ( Bits32, ["*",(5+6),(3+4),(1+2),
                                        (5+6),(3+4),(1+2)] )

      s.wire = [ [ Wire(32) for _ in range(2)] for _ in range(2) ]
      connect( s.wire[0][0], s.src.out )

      @update
      def up_from_src():
        s.wire[0][1] @= s.src.out + 1

      s.reg = Wire(32)
      connect( s.wire[1][0], s.reg )

      @update
      def up_reg():
        s.reg @= s.wire[0][0] + s.wire[0][1]

      for i in range(2):
        s.add_constraints(
          U(up_reg) < WR(s.wire[0][i]), # up_reg reads  s.wire[0][i]
        )

      @update
      def upA():
        s.wire[1][1] @= s.reg + 1

      @update
      def up_to_sink():
        s.sink.in_ @= s.wire[1][0] + s.wire[1][1]

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
             str(s.wire)+" r0=%s" % s.reg + \
             " >>> " + s.sink.line_trace()

  a = Top()
  a.elaborate()
  _test_model( Top )

def test_connect_const_same_level():

  class Top(ComponentLevel3):

    def construct( s ):

      s.a = Wire(32)
      connect( s.a, 0 )

      @update
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

      s.a = Wire(32)
      connect( s.a, 0 )

      @update
      def up_printa():
        print(s.a)

      @update
      def up_writea():
        s.a @= 123

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

def test_connect_list_idx_const_in_call():

  class Top(ComponentLevel3):

    def construct( s ):

      s.src_in0 = TestSource( Bits32, [4,3,2,1] )
      s.src_sel = TestSource( Bits1, [1,0,1,0] )
      s.sink    = TestSink  ( Bits32, [12,3,12,1] )

      s.mux = Mux(Bits32, 2)
      s.mux.out //= s.sink.in_
      s.mux.in_[MUX_SEL_0] //= s.src_in0.out
      s.mux.in_[MUX_SEL_1] //= 12
      s.mux.sel //= s.src_sel.out

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
      connect( s.a, s.b[0:10] )

      @update
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
      connect( s.a, s.b[9:19] )

      @update
      def up():
        s.b[0:10] @= 1023

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

      connect( s.in_[0:8], s.out1[0:8] )
      connect( s.in_[0:4], s.out2[0:4] )

  a = A()
  a.elaborate()

# A similar case for struct

def test_multiple_fields_are_net_writers():

  @bitstruct
  class SomeMsg1:
    a: Bits8
    b: Bits32

  @bitstruct
  class SomeMsg2:
    c: Bits8

  class A( ComponentLevel3 ):

    def construct( s ):
      s.in_  = InPort( SomeMsg1 )
      s.out1 = OutPort( SomeMsg2 )
      s.out2 = OutPort( SomeMsg2 )

      connect( s.in_.a, s.out1.c )
      connect( s.in_.b[0:8], s.out2.c )

  a = A()
  a.elaborate()
  simple_sim_pass( a )

  a.in_ = SomeMsg1(4, 5)
  a.tick()
  assert a.out1.c == 4

# The counterpart of the above test

def test_multiple_fields_are_assigned():

  @bitstruct
  class SomeMsg1:
    a: Bits8
    b: Bits32

  @bitstruct
  class SomeMsg2:
    c: Bits8

  class A( ComponentLevel3 ):

    def construct( s ):
      s.in_  = InPort( SomeMsg1 )
      s.out1 = OutPort( SomeMsg2 )
      s.out2 = OutPort( SomeMsg2 )

      # connect( s.in_.a, s.out1.c )
      # connect( s.in_.b[0:8], s.out2.c )
      @update
      def up_pass():
        s.out1.c @= s.in_.a
        s.out2.c @= s.in_.b[0:8]

  a = A()
  a.elaborate()
  simple_sim_pass( a )

  a.in_ = SomeMsg1(4, 5)
  a.tick()
  assert a.out1.c == 4

def test_const_connect_struct_signal_to_int():

  @bitstruct
  class SomeMsg1:
    a: Bits8
    b: Bits32

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.wire = Wire(SomeMsg1)
      connect( s.wire, 1 )

  try:
    x = Top()
    x.elaborate()
  except InvalidConnectionError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidConnectionError.")

def test_const_connect_struct_signal_to_Bits():

  @bitstruct
  class SomeMsg1:
    a: Bits8
    b: Bits32

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.wire = Wire(SomeMsg1)
      connect( s.wire, Bits32(1) )

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
      connect( s.wire, 1 )

  x = Top()
  x.elaborate()
  print(x._dsl.consts)
  assert len(x._dsl.consts) == 1

  simple_sim_pass(x)
  x.tick()

def test_const_connect_int_signal_to_int():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.wire = Wire(32)
      connect( s.wire, 1 )

  x = Top()
  x.elaborate()
  print(x._dsl.consts)
  assert len(x._dsl.consts) == 1

  simple_sim_pass(x)
  x.tick()

def test_const_connect_Bits_signal_to_Bits():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.wire = Wire(Bits32)
      connect( s.wire, Bits32(0) )

  x = Top()
  x.elaborate()
  print(x._dsl.consts)
  assert len(x._dsl.consts) == 1

  simple_sim_pass(x)
  x.tick()

def test_const_connect_Bits_signal_to_mismatch_Bits():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.wire = Wire(Bits32)
      connect( s.wire, Bits8(8) )

  try:
    x = Top()
    x.elaborate()
  except InvalidConnectionError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidConnectionError.")

def test_const_connect_struct_signal_to_struct():

  @bitstruct
  class SomeMsg1:
    a: Bits8
    b: Bits32

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.out = OutPort(SomeMsg1)
      connect( s.out, SomeMsg1(1,3) )

  x = Top()
  x.elaborate()
  simple_sim_pass(x)
  x.tick()
  assert x.out == SomeMsg1(1,3)

def test_const_connect_nested_struct_signal_to_struct():

  @bitstruct
  class SomeMsg1:
    a: Bits8
    b: Bits32

  @bitstruct
  class SomeMsg2:
    a: SomeMsg1
    b: Bits32

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.out = OutPort(SomeMsg2)
      connect( s.out, SomeMsg2(SomeMsg1(1,2),3) )

  x = Top()
  x.elaborate()
  simple_sim_pass(x)
  x.tick()
  assert x.out == SomeMsg2(SomeMsg1(1,2),3)

def test_const_connect_cannot_handle_same_name_nested_struct():

  class A:
    @bitstruct
    class SomeMsg1:
      a: Bits8
      b: Bits32

  class B:
    @bitstruct
    class SomeMsg1:
      c: Bits8
      d: Bits32

  @bitstruct
  class SomeMsg2:
    a: A.SomeMsg1
    b: B.SomeMsg1

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.out = OutPort(SomeMsg2)
      connect( s.out, SomeMsg2(A.SomeMsg1(1,2),B.SomeMsg1(3,4)) )

  x = Top()
  x.elaborate()
  try:
    simple_sim_pass(x)
  except AssertionError as e:
    print(e)
    assert str(e).startswith("Cannot handle two subfields with the same struct name but different structs")
    return
  raise Exception("Should've thrown AssertionError")

def test_const_connect_diffrent_structs_same_name():

  class A:
    @bitstruct
    class SomeMsg1:
      a: Bits8
      b: Bits32
  class B:
    @bitstruct
    class SomeMsg1:
      c: Bits8

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.out = OutPort(A.SomeMsg1)
      connect( s.out, A.SomeMsg1(1,3) )

      s.out2 = OutPort(B.SomeMsg1)
      connect( s.out2, B.SomeMsg1(4) )

  x = Top()
  x.elaborate()
  simple_sim_pass(x)
  x.tick()
  assert x.out == A.SomeMsg1(1,3)
  assert x.out2 == B.SomeMsg1(4)

def test_invalid_connect_outside_hierarchy():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.wire = InPort(Bits32)

  try:
    x = Top()
    x.elaborate()
    connect( x.wire, Bits32(8) )
  except InvalidConnectionError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidConnectionError.")

globalvar = 2
def test_connect_lambda():

  class Top( ComponentLevel3 ):
    def construct( s, x ):
      s.in_ = InPort(Bits32)
      s.out = OutPort(Bits32)

      s.out //= lambda: s.in_ + x + globalvar

  x = Top(3)
  x.elaborate()
  simple_sim_pass(x)
  x.in_ = 10
  x.tick()
  assert x.out == 10 + 3 + 2

  y = Top(33)
  y.elaborate()
  simple_sim_pass(y)
  y.in_ = 100
  y.tick()
  assert y.out == 100 + 33 + 2

def test_connect_lambda_linebreak():

  class Top( ComponentLevel3 ):
    def construct( s, x ):
      s.in_ = InPort(Bits32)
      s.out = OutPort(Bits32)

      s.out //= lambda: s.in_ + x + \
                        globalvar

  x = Top(3)
  x.elaborate()
  simple_sim_pass(x)
  x.in_ = 10
  x.tick()
  assert x.out == 10 + 3 + 2

  y = Top(33)
  y.elaborate()
  simple_sim_pass(y)
  y.in_ = 100
  y.tick()
  assert y.out == 100 + 33 + 2

def test_lambda_name_conflict():

  class Top( ComponentLevel3 ):
    def construct( s, x ):
      s.in_ = InPort(Bits32)
      s.out = OutPort(Bits32)
      s.out2 = OutPort(Bits32)

      s.out //= lambda: s.in_ + x

      # TODO throw some better error message when
      # the implicit name of a lambda function conflicts
      # with the explicit name of an update block

      @update
      def _lambda__s_out():
        s.out2 = Bits32(2)

  try:
    x = Top(3)
    x.elaborate()
  except UpblkFuncSameNameError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown UpblkFuncSameNameError.")

def test_loop_with_temp_name_lambda():

  class A( ComponentLevel3 ):
    def construct( s ):
      s.in_ = InPort(32)
      s.out = OutPort(32)
      s.out //= s.in_

  class Top( ComponentLevel3 ):
    def construct( s, x ):
      s.in_ = InPort(Bits32)
      s.out = [ OutPort(Bits32) for _ in range(5) ]

      s.xs = [ A() for _ in range(5) ]
      for i, m in enumerate(s.xs):
        m.in_ //= lambda: s.in_ + i
        m.out //= s.out[i]

  x = Top(3)
  x.elaborate()
  simple_sim_pass(x)
  x.in_ = 10
  x.tick()
  assert x.out == [ 10, 11, 12, 13, 14 ]

def test_invalid_in_out_loopback_at_self():

  class Comp( ComponentLevel3 ):
    def construct( s ):
      s.y = OutPort( Bits32 )
      s.z = OutPort( Bits32 )
      s.x = InPort( Bits32 )

      s.y //= Bits32(1)
      s.x //= s.y
      s.z //= s.x

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.comp = Comp()

  try:
    a = Top()
    a.elaborate()
  except InvalidConnectionError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidConnectionError.")

def test_in_out_loopback_at_parent():

  class Comp( ComponentLevel3 ):
    def construct( s ):
      s.y = OutPort( Bits32 )
      s.z = OutPort( Bits32 )
      s.x = InPort( Bits32 )

      s.y //= Bits32(1)
      s.z //= s.x

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.comp = Comp()
      s.comp.x //= s.comp.y

  a = Top()
  a.elaborate()

def test_misconnect_component_to_signal():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.y = OutPort( Bits8 )
      s.x = Wire( Bits32 )
      s.y //= s # this is garbage

  a = Top()
  try:
    a.elaborate()
  except InvalidConnectionError as e:
    print(e)
    return
  raise Exception("Should've thrown InvalidConnectionError")

def test_s_connect_deprecated():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.y = OutPort( Bits8 )
      s.x = Wire( Bits32 )
      s.connect(s.x, s.y)

  a = Top()
  try:
    a.elaborate()
  except PyMTLDeprecationError as e:
    print(e)
    return
  raise Exception("Should've thrown InvalidConnectionError")

def test_slice_over_slice():
  class A( ComponentLevel3 ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits8 )
      connect( s.out, s.in_[16:32][3:12][1:9] )
  a = A()
  a.elaborate()
  assert str(a._dsl.connect_order) == "[(s.out, s.in_[20:28])]"
