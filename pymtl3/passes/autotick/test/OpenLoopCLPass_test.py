"""
#=========================================================================
# OpenLoopCLPass_test.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Apr 19, 2019
"""
from pymtl3.datatypes import Bits32
from pymtl3.dsl import *
from pymtl3.dsl.errors import UpblkCyclicError
from pymtl3.passes.sim.GenDAGPass import GenDAGPass
from pymtl3.passes.tracing.PrintTextWavePass import PrintTextWavePass

from ..OpenLoopCLPass import OpenLoopCLPass


def test_top_level_method_tracing():

  class Top(Component):

    def construct( s ):
      s.element = None

      s.count = Wire(Bits32)
      s.amp   = Wire(Bits32)

      s.value = Wire(Bits32)

      @update_ff
      def up_incr():
        s.count <<= s.count + 1

      @update
      def up_amp():
        s.amp @= s.count * 100

      @update
      def up_compose_in():
        if s.element:
          s.value @= s.amp + s.element
          s.element = None
        else:
          s.value @= Bits32( -1 )

      s.add_constraints(
        M( s.push ) < U( up_compose_in ),
        U( up_compose_in ) < M( s.pull ), # bypass behavior
      )

    @method_port
    def push( s, ele ):
      if s.element is None:
        s.element = ele

    @method_port
    def pull( s ):
      return s.value

    def line_trace( s ):
      return "line trace: {}".format(s.value)

    def done( s ):
      return True

  A = Top()
  A.elaborate()

  # Turn on textwave
  A.set_metadata( PrintTextWavePass.enable, True )

  A.apply( GenDAGPass() )
  A.apply( OpenLoopCLPass() )

  print("- push!")
  A.push(7)
  print("- pull!")
  print(A.pull())

  print("- pull!")
  print(A.pull())

  print("- push!")
  A.push(33)
  print("- push!")
  A.push(55)
  print("- pull!")
  print(A.pull())

  print("num_cycles_executed: ", A.sim_cycle_count())
  A.print_textwave()

class TestModuleNonBlockingIfc(Component):

  def construct( s ):
    s.element = None

    s.count = Wire(Bits32)
    s.amp   = Wire(Bits32)

    s.value = Wire(Bits32)

    @update_ff
    def up_incr():
      if s.reset:
        s.count <<= 0
      else:
        s.count <<= s.count + 1

    @update
    def up_amp():
      s.amp @= s.count * 100

    @update
    def up_compose_in():
      if s.element:
        s.value @= s.amp + s.element
        s.element = None
      else:
        s.value @= -1

    s.add_constraints(
      M( s.push ) < U( up_compose_in ),
      U( up_compose_in ) < M( s.pull ), # bypass behavior
    )

  @non_blocking( lambda s: s.element is None and s.count % 5 == 4 )
  def push( s, ele ):
    assert s.element is None and s.count % 5 == 4
    s.element = ele

  @non_blocking( lambda s: s.value != Bits32(-1) )
  def pull( s ):
    return s.value

  def line_trace( s ):
    return "line trace: {}".format(s.value)

  def done( s ):
    return True

def _test_TestModuleNonBlockingIfc( cls ):

  A = cls()
  A.elaborate()
  A.apply( GenDAGPass() )
  A.apply( OpenLoopCLPass() )
  A.sim_reset()

  rdy = A.push.rdy()
  print("- push_rdy?", rdy )
  assert not rdy

  rdy = A.push.rdy()
  print("- push_rdy?", rdy)
  assert not rdy

  rdy = A.push.rdy()
  print("- push_rdy?", rdy)
  assert not rdy

  rdy = A.push.rdy()
  print("- push_rdy?", rdy)
  assert not rdy

  rdy = A.push.rdy()
  print("- push_rdy?", rdy)
  assert rdy
  print("- push 13!")
  A.push(13)

  assert A.pull.rdy()
  ret = A.pull()
  print("- pull!", ret)
  assert ret == 413

  assert not A.pull.rdy()

  rdy = A.push.rdy()
  print("- push_rdy?", rdy )
  assert not rdy

  rdy = A.push.rdy()
  print("- push_rdy?", rdy)
  assert not rdy

  rdy = A.push.rdy()
  print("- push_rdy?", rdy)
  assert not rdy

  rdy = A.push.rdy()
  print("- push_rdy?", rdy)
  assert rdy
  print("- push 33!")
  A.push(33)

  assert A.pull.rdy()
  ret = A.pull()
  print("- pull!", ret)
  assert ret == 933

  assert not A.pull.rdy()

  return A.sim_cycle_count()

def test_top_level_non_blocking_ifc():
  num_cycles = _test_TestModuleNonBlockingIfc( TestModuleNonBlockingIfc )
  assert num_cycles == 3 + 10 # regression

def test_top_level_non_blocking_ifc_in_deep_net():

  class Top(Component):
    def construct( s ):
      s.push = CalleeIfcCL()
      s.pull = CalleeIfcCL()
      s.inner = Top_less_less_inner()
      s.inner.push //= s.push
      s.inner.pull //= s.pull

    def line_trace( s ):
      return s.inner.line_trace()

    def done( s ):
      return True

  class Top_less_less_inner(Component):
    def construct( s ):
      s.push = CalleeIfcCL()
      s.pull = CalleeIfcCL()
      s.inner = Top_less_inner()
      s.inner.push //= s.push
      s.inner.pull //= s.pull
    def line_trace( s ):
      return s.inner.line_trace()

    def done( s ):
      return True

  class Top_less_inner(Component):
    def construct( s ):
      s.push = CalleeIfcCL()
      s.pull = CalleeIfcCL()
      s.inner = TestModuleNonBlockingIfc()
      s.inner.push //= s.push
      s.inner.pull //= s.pull

    def line_trace( s ):
      return s.inner.line_trace()

    def done( s ):
      return True

  num_cycles = _test_TestModuleNonBlockingIfc( Top )
  assert num_cycles == 3 + 10 # regression

class PassThroughPlus100( Component ):

  @non_blocking( lambda s: s.real_push.rdy() )
  def push( s, msg ):
    assert s.real_push.rdy()
    s.real_push( msg )

  def construct( s ):
    s.real_push = CallerIfcCL()

    s.add_constraints(
      M(s.push) == M(s.real_push),
    )

def test_pass_through_equal_m_constraint():

  class Top(Component):
    def construct( s ):
      s.push = CalleeIfcCL()
      s.pull = CalleeIfcCL()
      s.pass1 = PassThroughPlus100()
      s.pass1.push //= s.push
      s.inner = TestModuleNonBlockingIfc()
      s.inner.push //= s.pass1.real_push
      s.inner.pull //= s.pull

    def line_trace( s ):
      return s.inner.line_trace()

    def done( s ):
      return True

  num_cycles = _test_TestModuleNonBlockingIfc( Top )
  assert num_cycles == 3+10 # regression


def test_deep_pass_through_equal_m_constraint():

  class Top(Component):
    def construct( s ):
      s.push = CalleeIfcCL()
      s.pull = CalleeIfcCL()
      s.through = [ PassThroughPlus100() for _ in range(10) ]
      for i in range(10):
        connect( s.through[i].push, s.push if i == 0 else \
                                      s.through[i-1].real_push )

      s.inner = TestModuleNonBlockingIfc()
      s.inner.push //= s.through[-1].real_push
      s.inner.pull //= s.pull

    def line_trace( s ):
      return "push's line trace:" + str(s.push)

    def done( s ):
      return True

  num_cycles = _test_TestModuleNonBlockingIfc( Top )
  assert num_cycles == 3 + 10 # regression
