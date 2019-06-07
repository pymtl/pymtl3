"""
========================================================================
ComponentLevel2_test.py
========================================================================

Author : Shunning Jiang
Date   : Nov 3, 2018
"""
from __future__ import absolute_import, division, print_function

from collections import deque

from pymtl3.datatypes import Bits32
from pymtl3.dsl.ComponentLevel2 import ComponentLevel2
from pymtl3.dsl.Connectable import InPort, OutPort, Wire
from pymtl3.dsl.ConstraintTypes import RD, WR, U
from pymtl3.dsl.errors import (
    InvalidConstraintError,
    InvalidFuncCallError,
    UpblkCyclicError,
    VarNotDeclaredError,
)

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

class TestSource( ComponentLevel2 ):

  def construct( s, input_ ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!"

    s.input_ = deque( input_ ) # deque.popleft() is faster
    s.out = OutPort(int)

    @s.update
    def up_src():
      if not s.input_:
        s.out = 0
      else:
        s.out = s.input_.popleft()

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return "%s" % s.out

class TestSink( ComponentLevel2 ):

  def construct( s, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!"

    s.answer = deque( answer )
    s.in_ = InPort(int)

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

def test_simple():

  class Top(ComponentLevel2):

    def construct( s ):
      s.a = Wire(int)
      s.b = Wire(int)

      @s.update
      def upA():
        s.a = s.b + 1

      @s.update
      def upB():
        s.b = s.b + 1

    def done( s ):
      return True

  _test_model( Top )

def test_cyclic_impl_dependency():

  class Top(ComponentLevel2):

    def construct( s ):
      s.a = Wire(int)
      s.b = Wire(int)

      @s.update
      def upA():
        s.a = s.b

      @s.update
      def upB():
        s.b = s.a

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

      s.a = Wire(int)
      s.b = Wire(int)

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

  class SomeMsg( object ):

    def __init__( s, a=0, b=0 ):
      s.a = int( a )
      s.b = Bits32( b )

  class A(ComponentLevel2):
    def construct( s ):
      s.a = Wire( SomeMsg )
      s.b = Wire( int )

      @s.update
      def upA():
        s.a.a.zzz = s.b + 1

      @s.update
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

def test_2d_array_vars():

  class Top(ComponentLevel2):

    def construct( s ):

      s.src  = TestSource( [2,1,0,2,1,0] )
      s.sink = TestSink  ( ["*",(5+6),(3+4),(1+2),
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

  _test_model( Top )

def test_wire_up_constraint():

  class Top(ComponentLevel2):

    def construct( s ):

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

  _test_model( Top )

# write two disjoint slices
def test_write_two_disjoint_slices():

  class Top(ComponentLevel2):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_0_16():
        s.A[0:16] = Bits16( 0xff )

      @s.update
      def up_wr_16_30():
        s.A[16:30] = Bits16( 0xff )

      @s.update
      def up_rd_12_30():
        assert s.A[12:30] == 0xff0

    def done( s ):
      return True

  _test_model( Top )

# WR A.b - RD A
def test_wr_A_b_rd_A_impl():


  class SomeMsg( object ):

    def __init__( s, a=0, b=0 ):
      s.a = int(a)
      s.b = Bits32(b)

  class Top(ComponentLevel2):
    def construct( s ):
      s.A  = Wire( SomeMsg )

      @s.update
      def up_wr_A_b():
        s.A.b = 123

      @s.update
      def up_rd_A():
        z = s.A

    def done( s ):
      return True

  _test_model( Top )

def test_add_loopback():

  class Top(ComponentLevel2):

    def construct( s ):

      s.src  = TestSource( [4,3,2,1] )
      s.sink = TestSink  ( ["*",(4+1),(3+1)+(4+1),(2+1)+(3+1)+(4+1),(1+1)+(2+1)+(3+1)+(4+1)] )

      s.wire0 = Wire(int)
      s.wire1 = Wire(int)

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      s.reg0 = Wire(int)

      @s.update
      def upA():
        s.reg0 = s.wire0 + s.wire1

      @s.update
      def up_to_sink_and_loop_back():
        s.sink.in_ = s.reg0
        s.wire1 = s.reg0

      s.add_constraints(
        U(upA) < WR(s.wire1),
        U(upA) < WR(s.wire0),
        U(upA) < RD(s.reg0), # also implicit
      )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0=%s > r0=%s > w1=%s" % (s.wire0,s.reg0,s.wire1) + \
             " >>> " + s.sink.line_trace()
  _test_model( Top )

def test_add_loopback_on_edge():

  class Top(ComponentLevel2):

    def construct( s ):

      s.src  = TestSource( [4,3,2,1] )
      s.sink = TestSink  ( ["*",(4+1),(3+1)+(4+1),(2+1)+(3+1)+(4+1),(1+1)+(2+1)+(3+1)+(4+1)] )

      s.wire0 = Wire(int)
      s.wire1 = Wire(int)

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      s.reg0 = Wire(int)

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

  _test_model( Top )

def test_2d_array_vars_impl():

  class Top(ComponentLevel2):

    def construct( s ):

      s.src  = TestSource( [2,1,0,2,1,0] )
      s.sink = TestSink  ( ["*",(5+6),(3+4),(1+2),
                                (5+6),(3+4),(1+2)] )

      s.wire = [ [ Wire(int) for _ in xrange(2)] for _ in xrange(2) ]

      @s.update
      def up_from_src():
        s.wire[0][0] = s.src.out
        s.wire[0][1] = s.src.out + 1

      s.reg = Wire(int)

      @s.update_on_edge
      def up_reg():
        s.reg = s.wire[0][0] + s.wire[0][1]

      @s.update
      def upA():
        for i in xrange(2):
          s.wire[1][i] = s.reg + i

      @s.update
      def up_to_sink():
        s.sink.in_ = s.wire[1][0] + s.wire[1][1]

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
      s.a = Wire(int)
      s.b = Wire(int)

      s.counter_assign = Wire(int)
      s.counter_read   = Wire(int)

      @s.func
      def assignb( b ):
        s.b = b + (s.counter_assign == -1) # never -1

      @s.update
      def up_write():
        if s.counter_assign & 1:
          assign( 1, 2 )
        else:
          assign( 10, 20 )
        s.counter_assign += 1

      @s.update
      def up_read():
        if s.counter_read & 1:
          assert s.a == 1 and s.b == min(100,2)
        else:
          assert s.a == 10 and s.b == 20
        s.counter_read += 1

      # The order doesn't matter. As a result, funcs should be processed
      # after construction time
      @s.func
      def assign( a, b ):
        s.a = a + (s.counter_assign == -1)
        assignb( b )

    def done( s ):
      return False

    def line_trace( s ):
      return "{} {}".format( s.a, s.b )

  _test_model( Top )

def test_func_cyclic_invalid():

  class Top(ComponentLevel2):

    def construct( s ):
      s.a = Wire(int)
      s.b = Wire(int)
      s.c = Wire(int)

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

      @s.update
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
