"""
========================================================================
ComponentLevel1_test.py
========================================================================

Author : Shunning Jiang
Date   : Dec 23, 2017
"""
from __future__ import absolute_import, division, print_function

from collections import deque

from pymtl3.dsl import *
from pymtl3.dsl.errors import UpblkCyclicError, UpblkFuncSameNameError

from .sim_utils import simple_sim_pass


def _test_model( cls ):
  A = cls()
  A.elaborate()
  simple_sim_pass( A, 0x123 )

  while not A.done():
    A.tick()
    print(A.line_trace())

class TestSource( ComponentLevel1 ):

  def construct( s, input_ ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!"

    s.input_ = deque( input_ ) # deque.popleft() is faster
    s.out = 0

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

class TestSink( ComponentLevel1 ):

  def construct( s, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!"

    s.answer = deque( answer )
    s.in_ = 0

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

def test_cyclic_dependency():

  class Top(ComponentLevel1):

    def construct( s ):

      @s.update
      def upA():
        pass

      @s.update
      def upB():
        pass

      s.add_constraints(
        U(upA) < U(upB),
        U(upB) < U(upA),
      )

  try:
    _test_model( Top )
  except UpblkCyclicError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown cyclic dependency UpblkCyclicError.")

def test_upblock_same_name():

  class Top(ComponentLevel1):

    def construct( s ):

      @s.update
      def upA():
        pass

      @s.update
      def upA():
        pass

  try:
    _test_model( Top )
  except UpblkFuncSameNameError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown name conflict UpblkFuncSameNameError.")

def test_register_behavior():

  class Top(ComponentLevel1):

    def construct( s ):

      s.src  = TestSource( [5,4,3,2,1] )
      s.sink = TestSink  ( [0,5,4,3,2] )

      s.wire0 = 0
      s.wire1 = 0

      @s.update
      def up_from_src():
        s.wire0 = s.src.out

      up_src = s.src.get_update_block("up_src")

      s.add_constraints(
        U(up_src) < U(up_from_src),
      )

      @s.update
      def up_reg():
        s.wire1 = s.wire0

      @s.update
      def up_to_sink():
        s.sink.in_ = s.wire1

      s.add_constraints(
        U(up_reg) < U(up_to_sink),
        U(up_reg) < U(up_from_src),
      )

      up_sink = s.sink.get_update_block("up_sink")

      s.add_constraints(
        U(up_to_sink) < U(up_sink),
      )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0={} > w1={}".format(s.wire0,s.wire1) + \
             " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_add_loopback():

  class Top(ComponentLevel1):

    def construct( s ):

      s.src  = TestSource( [4,3,2,1] )
      s.sink = TestSink  ( ["*",(4+1),(3+1)+(4+1),(2+1)+(3+1)+(4+1),(1+1)+(2+1)+(3+1)+(4+1)] )

      s.wire0 = 0
      s.wire1 = 0

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      up_src = s.src.get_update_block("up_src")

      s.add_constraints(
        U(up_src) < U(up_from_src),
      )

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

      up_sink = s.sink.get_update_block("up_sink")

      s.add_constraints(
        U(up_to_sink_and_loop_back) < U(up_sink),
      )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0=%s > r0=%s > w1=%s" % (s.wire0,s.reg0,s.wire1) + \
             " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_lots_of_fan():

  class Top(ComponentLevel1):

    def construct( s ):

      s.src  = TestSource( [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( ["*",(5+6+6+7),(4+5+5+6),(3+4+4+5),(2+3+3+4),
                                (5+6+6+7),(4+5+5+6),(3+4+4+5),(2+3+3+4)] )

      s.wire0 = 0

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      up_src = s.src.get_update_block("up_src")

      s.add_constraints(
        U(up_src) < U(up_from_src),
      )

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

      s.add_constraints(
        U(upA) < U(upB),
        U(upA) < U(upC),
      )
      s.wire7 = s.wire8 = 0

      @s.update
      def upD():
        s.wire7 = s.wire3 + s.wire6
        s.wire8 = s.wire4 + s.wire5

      s.add_constraints(
        U(upB) < U(upD),
        U(upC) < U(upD),
      )

      @s.update
      def up_to_sink():
        s.sink.in_ = s.wire7 + s.wire8

      up_sink = s.sink.get_update_block("up_sink")

      s.add_constraints(
        U(upD) < U(up_to_sink),
        U(up_to_sink) < U(up_sink),
      )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0=%s > r0=%s" % (s.wire0,s.reg) + \
             " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_2d_array_vars():

  class Top(ComponentLevel1):

    def construct( s ):

      s.src  = TestSource( [2,1,0,2,1,0] )
      s.sink = TestSink  ( ["*",(5+6),(3+4),(1+2),
                                (5+6),(3+4),(1+2)] )

      s.wire = [ [0 for _ in xrange(2)] for _ in xrange(2) ]

      @s.update
      def up_from_src():
        s.wire[0][0] = s.src.out
        s.wire[0][1] = s.src.out + 1

      up_src = s.src.get_update_block("up_src")

      s.add_constraints(
        U(up_src) < U(up_from_src),
      )

      s.reg = 0

      @s.update
      def up_reg():
        s.reg = s.wire[0][0] + s.wire[0][1]

      @s.update
      def upA():
        s.wire[1][0] = s.reg
        s.wire[1][1] = s.reg + 1

      s.add_constraints(
        U(up_reg) < U(upA),
        U(up_reg) < U(up_from_src),
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
