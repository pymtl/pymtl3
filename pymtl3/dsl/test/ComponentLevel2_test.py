"""
========================================================================
ComponentLevel2_test.py
========================================================================

Author : Shunning Jiang
Date   : Nov 3, 2018
"""
from collections import deque

from pymtl3.datatypes import Bits1, Bits16, Bits32, bitstruct, mk_bits, zext
from pymtl3.dsl.ComponentLevel1 import update
from pymtl3.dsl.ComponentLevel2 import ComponentLevel2, update_ff
from pymtl3.dsl.Connectable import InPort, Interface, OutPort, Wire
from pymtl3.dsl.ConstraintTypes import RD, WR, U
from pymtl3.dsl.errors import (
    InvalidConstraintError,
    InvalidFuncCallError,
    MultiWriterError,
    PyMTLDeprecationError,
    UpblkCyclicError,
    UpdateBlockWriteError,
    UpdateFFBlockWriteError,
    UpdateFFNonTopLevelSignalError,
    VarNotDeclaredError,
    WriteNonSignalError,
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

class TestSource( ComponentLevel2 ):

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

class TestSink( ComponentLevel2 ):

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

def test_signal_require_type_or_int():

  class Top(ComponentLevel2):
    def construct( s ):
      s.a = Wire('a')

  a = Top()
  try:
    a.elaborate()
  except AssertionError as e:
    print(e)
    assert str(e).startswith( "RTL signal can only be of Bits type or bitstruct type" )

def test_ast_caching_closure():

  class Parametrized(ComponentLevel2):
    def construct( s, nbits ):
      s.x = Wire( nbits*2 )
      @update
      def upA():
        print(s.x[nbits])
        print(s.x[0:nbits])
        print(s.x[nbits:nbitsX2])

  p1 = Parametrized( 100 )
  p2 = Parametrized( 1 )
  p1.elaborate()
  print(p1._dsl.all_upblk_reads)
  p2.elaborate()
  print(p2._dsl.all_upblk_reads)

def test_simple():

  class Top(ComponentLevel2):

    def construct( s ):
      s.a = Wire(Bits1)
      s.b = Wire(Bits1)

      @update
      def upA():
        s.a @= s.b + 1

      @update
      def upB():
        s.b @= s.b + 1

    def done( s ):
      return True

  _test_model( Top )

def test_cyclic_impl_dependency():

  class Top(ComponentLevel2):

    def construct( s ):
      s.a = Wire()
      s.b = Wire()

      @update
      def upA():
        s.a @= s.b

      @update
      def upB():
        s.b @= s.a

    def done( s ):
      return True

  try:
    _test_model( Top )
  except UpblkCyclicError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown UpblkCyclicError.")

def test_invalid_dependency():

  class Top(ComponentLevel2):

    def construct( s ):

      s.a = Wire()
      s.b = Wire()

      s.add_constraints(
        WR(s.a) < RD(s.b),
      )

  try:
    _test_model( Top )
  except InvalidConstraintError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return

  raise Exception("Should've thrown InvalidConstraintError.")

def test_variable_not_declared():

  @bitstruct
  class SomeMsg:
    a: Bits1
    b: Bits32

  class A(ComponentLevel2):
    def construct( s ):
      s.a = Wire( SomeMsg )
      s.b = Wire()

      @update
      def upA():
        s.a.a.zzz = s.b + 1

      @update
      def upB():
        s.b = s.b + 1

  class Top(ComponentLevel2):

    def construct( s ):
      s.x = A()

    def done( s ):
      return True

  try:
    _test_model( Top )
  except VarNotDeclaredError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown VarNotDeclaredError.")

def test_s_update_on_edge_deprecated():

  class Top(ComponentLevel2):
    def construct( s ):

      @s.update_on_edge
      def up():
        pass

  try:
    Top().elaborate()
  except PyMTLDeprecationError as e:
    print(e)
    return
  raise Exception("Should've thrown PyMTLDeprecationError.")

def test_invalid_ff_assignment1():

  class Top(ComponentLevel2):
    def construct( s ):
      s.wire0 = Wire(Bits32)

      @update_ff
      def up_from_src():
        temp **= s.wire0 + 1
        s.wire0 = temp

  try:
    _test_model( Top )
  except UpdateFFBlockWriteError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown UpdateFFBlockWriteError.")

def test_invalid_ff_assignment2():

  class Top(ComponentLevel2):
    def construct( s ):
      s.wire0 = Wire(Bits32)

      @update_ff
      def up_from_src():
        temp **= s.wire0 + 1
        s.wire0 <<= temp

  try:
    _test_model( Top )
  except UnboundLocalError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown UnboundLocalError.")

def test_invalid_ff_assignment_slice():

  class Top(ComponentLevel2):
    def construct( s ):
      s.wire0 = Wire(Bits32)

      @update_ff
      def upup():
        s.wire0[0:16] <<= s.wire0[16:32] + 1

  try:
    _test_model( Top )
  except UpdateFFNonTopLevelSignalError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown UpdateFFNonTopLevelSignalError.")

def test_2d_array_vars():

  class Top(ComponentLevel2):

    def construct( s ):

      s.src  = TestSource( Bits32, [2,1,0,2,1,0] )
      s.sink = TestSink  ( Bits32, ["*",(5+6),(3+4),(1+2),
                                (5+6),(3+4),(1+2)] )

      s.wire = [ [ Wire(Bits32) for _ in range(2)] for _ in range(2) ]

      @update
      def up_from_src():
        s.wire[0][0] @= s.src.out
        s.wire[0][1] @= s.src.out + 1

      s.reg = Wire(Bits32)

      @update
      def up_reg():
        s.reg @= s.wire[0][0] + s.wire[0][1]

      s.add_constraints(
        U(up_reg) < RD(s.reg), # up_reg writes s.reg
      )

      @update
      def upA():
        for i in range(2):
          s.wire[1][i] @= s.reg + i

      for i in range(2):
        s.add_constraints(
          U(up_reg) < WR(s.wire[0][i]), # up_reg reads  s.wire[0][i]
        )

      @update
      def up_to_sink():
        s.sink.in_ @= s.wire[1][0] + s.wire[1][1]

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

  _test_model( Top )

def test_wire_up_constraint():

  class Top(ComponentLevel2):

    def construct( s ):

      s.src  = TestSource( Bits32, [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( Bits32, [5,4,3,2,5,4,3,2] )

      @update
      def up_from_src():
        s.sink.in_ @= s.src.out + 1

      s.add_constraints(
        U(up_from_src) < RD(s.sink.in_),
      )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
             " >>> " + s.sink.line_trace()

  _test_model( Top )

class A:
  pass
# write two disjoint slices
def test_write_two_disjoint_slices():

  class Top(ComponentLevel2):
    def construct( s ):
      s.A  = Wire( Bits32 )
      s.B  = Wire( Bits16 )

      s.x = 16
      x = A()
      x.y = 4
      @update
      def up_wr_0_16():
        s.x <<= 123
        x.y = 123
        s.A[0:16] @= Bits16( 0xff )

      @update
      def up_wr_16_30():
        s.A[16:32] @= Bits16( 0xff )
        s.B @= s.A[1:17]

      @update
      def up_rd_12_30():
        assert s.A[12:30] == 0xff0
        print(s.B)

    def done( s ):
      return True

  _test_model( Top )

# WR A.b - RD A
def test_wr_A_b_rd_A_impl():

  @bitstruct
  class SomeMsg:
    a: Bits32
    b: Bits32

  class Top(ComponentLevel2):
    def construct( s ):
      s.A = Wire( SomeMsg )

      @update
      def up_wr_A_b():
        s.A.b @= 123

      @update
      def up_rd_A():
        z = s.A

    def done( s ):
      return True

  _test_model( Top )

def test_add_loopback():

  class Top(ComponentLevel2):

    def construct( s ):

      s.src  = TestSource( Bits32, [4,3,2,1] )
      s.sink = TestSink  ( Bits32, ["*",(4+1),(3+1)+(4+1),(2+1)+(3+1)+(4+1),(1+1)+(2+1)+(3+1)+(4+1)] )

      s.wire0 = Wire(Bits32)
      s.wire1 = Wire(Bits32)

      @update
      def up_from_src():
        s.wire0 @= s.src.out + 1

      s.reg0 = Wire(Bits32)

      @update
      def upA():
        s.reg0 @= s.wire0 + s.wire1

      @update
      def up_to_sink_and_loop_back():
        s.sink.in_ @= s.reg0
        s.wire1 @= s.reg0

      s.add_constraints(
        U(upA) < WR(s.wire1),
        U(upA) < WR(s.wire0),
        U(upA) < RD(s.reg0), # also implicit
      )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0={} > r0={} > w1={}".format(s.wire0,s.reg0,s.wire1) + \
             " >>> " + s.sink.line_trace()
  _test_model( Top )

def test_add_loopback_ff():

  class Top(ComponentLevel2):

    def construct( s ):

      s.src  = TestSource( Bits32, [4,3,2,1] )
      s.sink = TestSink  ( Bits32, ["*",(4+1),(3+1)+(4+1),(2+1)+(3+1)+(4+1),(1+1)+(2+1)+(3+1)+(4+1)] )

      s.wire0 = Wire(Bits32)
      s.wire1 = Wire(Bits32)

      @update
      def up_from_src():
        s.wire0 @= s.src.out + 1

      s.reg0 = Wire(Bits32)

      # UPDATE FF!
      @update_ff
      def upA():
        s.reg0 <<= s.wire0 + s.wire1

      @update
      def up_to_sink_and_loop_back():
        s.sink.in_ @= s.reg0
        s.wire1 @= s.reg0

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0={} > r0={} > w1={}".format(s.wire0,s.reg0,s.wire1) + \
             " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_2d_array_vars_impl():

  class Top(ComponentLevel2):

    def construct( s ):

      s.src  = TestSource( Bits32, [2,1,0,2,1,0] )
      s.sink = TestSink  ( Bits32, ["*",(5+6),(3+4),(1+2), (5+6),(3+4),(1+2)] )

      s.wire = [ [ Wire(Bits32) for _ in range(2)] for _ in range(2) ]

      @update
      def up_from_src():
        s.wire[0][0] @= s.src.out
        s.wire[0][1] @= s.src.out + 1

      s.reg = Wire(Bits32)

      @update_ff
      def up_reg():
        s.reg <<= s.wire[0][0] + s.wire[0][1]

      @update
      def upA():
        for i in range(2):
          s.wire[1][i] @= s.reg + i

      @update
      def up_to_sink():
        s.sink.in_ @= s.wire[1][0] + s.wire[1][1]

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
             str(s.wire)+"r0=%s" % s.reg + \
             " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_simple_func_impl():

  class Top(ComponentLevel2):

    def construct( s ):
      s.a = Wire(Bits32)
      s.b = Wire(Bits32)

      s.counter_assign = Wire(Bits32)
      s.counter_read   = Wire(Bits32)

      @s.func
      def assignb( b ):
        s.b @= b + zext(s.counter_assign < 0, 32) # never -1

      @update
      def up_write():
        if s.counter_assign & 1:
          assign( Bits32(1), Bits32(2) )
        else:
          assign( Bits32(10), Bits32(20) )
        s.counter_assign @= s.counter_assign + 1

      @update
      def up_read():
        if s.counter_read & 1:
          assert s.a == 1 and s.b == min(100,2)
        else:
          assert s.a == 10 and s.b == 20
        s.counter_read @= s.counter_read + 1

      # The order doesn't matter. As a result, funcs should be processed
      # after construction time
      @s.func
      def assign( a, b ):
        s.a = a + zext( s.counter_assign < 0, 32)
        assignb( b )

    def done( s ):
      return False

    def line_trace( s ):
      return "{} {}".format( s.a, s.b )

  _test_model( Top )

def test_func_cyclic_invalid():

  class Top(ComponentLevel2):

    def construct( s ):
      s.a = Wire(Bits32)
      s.b = Wire(Bits32)
      s.c = Wire(Bits32)

      @s.func
      def assignc( a, b ):
        s.c = a
        assign( a, b )

      @s.func
      def assignb( a, b ):
        s.b = b
        assignc( a, b )

      @s.func
      def assign( a, b ):
        s.a = b
        assignb( b, a )

      @update
      def up_write():
        assign( 1, 2 )

    def done( s ):
      return False

    def line_trace( s ):
      return "{} {}".format( s.a, s.b )

  try:
    _test_model( Top )
  except InvalidFuncCallError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown InvalidFuncCallError.")

def test_update_ff_swap():

  class Top(ComponentLevel2):

    def construct( s ):

      s.wire0 = Wire(Bits32)
      s.wire1 = Wire(Bits32)

      @update_ff
      def up():
        temp = s.wire1 + 1
        s.wire0 <<= temp
        s.wire1 <<= s.wire0 + 1

    def line_trace( s ):
      return "wire0={} , wire1={}".format(s.wire0, s.wire1)

  A = Top()
  A.elaborate()
  simple_sim_pass( A, 0x123 )

  T, time = 1, 20
  while T < time:
    A.tick()
    assert A.wire0 == T
    assert A.wire1 == T
    T += 1

def test_var_written_in_both_ff_and_up():

  class Top(ComponentLevel2):

    def construct( s ):

      s.wire0 = Wire(Bits32)
      s.wire1 = Wire(Bits32)

      @update_ff
      def up_src():
        s.wire0 <<= s.wire1 + 1
        s.wire1 <<= s.wire0 + 1

      @update
      def comb():
        s.wire1 @= 1

    def line_trace( s ):
      return "wire0={} , wire1={}".format(s.wire0, s.wire1)

  A = Top()
  try:
    A.elaborate()
  except MultiWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")

def test_signal_default_Bits1():

  class Top(ComponentLevel2):

    def construct( s ):
      s.x0 = Wire()
      s.x1 = InPort()
      s.x2 = OutPort()
      assert s.x0._dsl.Type == Bits1
      assert s.x1._dsl.Type == Bits1
      assert s.x2._dsl.Type == Bits1

  A = Top()
  A.elaborate()

def test_write_component_update():

  class A(ComponentLevel2):
    def construct( s ):
      s.x = Wire(Bits32)

  class Top(ComponentLevel2):
    def construct( s ):
      s.a = A()

      @update
      def up():
        s.a @= Bits32(12)

  x = Top()
  try:
    x.elaborate()
  except WriteNonSignalError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown WriteNonSignalError.")

def test_write_component_update_ff():

  class A(ComponentLevel2):
    def construct( s ):
      s.x = Wire(Bits32)

  class Top(ComponentLevel2):
    def construct( s ):
      s.a = A()

      @update_ff
      def up():
        s.a <<= Bits32(12)

  x = Top()
  try:
    x.elaborate()
  except WriteNonSignalError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown WriteNonSignalError.")

def test_write_interface_update_ff():

  class A(Interface):
    def construct( s ):
      s.x = InPort(Bits32)

  class Top(ComponentLevel2):
    def construct( s ):
      s.a = A()

      @update_ff
      def up():
        s.a <<= Bits32(12)

  x = Top()
  try:
    x.elaborate()
  except WriteNonSignalError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown WriteNonSignalError.")
