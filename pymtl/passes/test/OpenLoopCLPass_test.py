#=========================================================================
# OpenLoopCLPass_test.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Apr 19, 2019

from pymtl import *
from pymtl.passes import OpenLoopCLPass, GenDAGPass
from pymtl.dsl.errors import UpblkCyclicError

from collections import deque

def test_top_level_method():

  class Top(Component):

    def construct( s ):
      s.element = None

      s.count = Wire(int)
      s.count_next = Wire(int)
      s.amp   = Wire(int)

      s.value = Wire(int)

      @s.update_on_edge
      def up_incr():
        s.count = s.count_next

      @s.update
      def up_amp():
        s.amp = s.count * 100

      @s.update
      def up_compose_in():
        if s.element:
          s.value = s.amp + s.element
          s.element = None
        else:
          s.value = -1

      @s.update
      def up_count_next():
        s.count_next = s.count + 1

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
  A.apply( GenDAGPass() )
  A.apply( OpenLoopCLPass() )
  A.lock_in_simulation()

  print "- push!"
  A.push(7)
  print "- pull!"
  print A.pull()

  print "- pull!"
  print A.pull()

  print "- push!"
  A.push(33)
  print "- push!"
  A.push(55)
  print "- pull!"
  print A.pull()

  print "num_cycles_executed: ", A.num_cycles_executed

def test_top_level_non_blocking_ifc():

  class Top(Component):

    def construct( s ):
      s.element = None

      s.count = Wire(int)
      s.count_next = Wire(int)
      s.amp   = Wire(int)

      s.value = Wire(int)

      @s.update_on_edge
      def up_incr():
        s.count = s.count_next

      @s.update
      def up_amp():
        s.amp = s.count * 100

      @s.update
      def up_compose_in():
        if s.element:
          s.value = s.amp + s.element
          s.element = None
        else:
          s.value = -1

      @s.update
      def up_count_next():
        s.count_next = s.count + 1

      s.add_constraints(
        M( s.push ) < U( up_compose_in ),
        U( up_compose_in ) < M( s.pull ), # bypass behavior
      )

    @non_blocking( lambda s: s.element is None and s.count % 5 == 4 )
    def push( s, ele ):
      s.element = ele

    @non_blocking( lambda s: s.value >= 0 )
    def pull( s ):
      return s.value

    def line_trace( s ):
      return "line trace: {}".format(s.value)

    def done( s ):
      return True

  A = Top()
  A.elaborate()
  A.apply( GenDAGPass() )
  A.apply( OpenLoopCLPass() )
  A.lock_in_simulation()

  print "- push_rdy?",
  rdy = A.push.rdy()
  print rdy
  if rdy:
    print "- push!"
    A.push(7)

  print "- push_rdy?",
  rdy = A.push.rdy()
  print rdy
  if rdy:
    print "- push!"
    A.push(8)

  print "- push_rdy?",
  rdy = A.push.rdy()
  print rdy
  if rdy:
    print "- push!"
    A.push(9)

  print "- push_rdy?",
  rdy = A.push.rdy()
  print rdy
  if rdy:
    print "- push!"
    A.push(11)

  print "- push_rdy?",
  rdy = A.push.rdy()
  print rdy
  if rdy:
    print "- push!"
    A.push(13)

  print "- pull!"
  print A.pull()

  print "- pull!"
  print A.pull()

  print "- push!"
  A.push(33)
  print "- push!"
  A.push(55)
  print "- pull!"
  print A.pull()

  # regression

  assert A.num_cycles_executed == 8

def test_top_level_non_blocking_ifc_in_net():

  class Top(Component):
    def construct( s ):
      s.push = NonBlockingCalleeIfc()
      s.pull = NonBlockingCalleeIfc()
      s.inner = Top_inner()( push = s.push, pull = s.pull )

    def line_trace( s ):
      return s.inner.line_trace()

    def done( s ):
      return True

  class Top_inner(Component):

    def construct( s ):
      s.element = None

      s.count = Wire(int)
      s.count_next = Wire(int)
      s.amp   = Wire(int)

      s.value = Wire(int)

      @s.update_on_edge
      def up_incr():
        s.count = s.count_next

      @s.update
      def up_amp():
        s.amp = s.count * 100

      @s.update
      def up_compose_in():
        if s.element:
          s.value = s.amp + s.element
          s.element = None
        else:
          s.value = -1

      @s.update
      def up_count_next():
        s.count_next = s.count + 1

      s.add_constraints(
        M( s.push ) < U( up_compose_in ),
        U( up_compose_in ) < M( s.pull ), # bypass behavior
      )

    @non_blocking( lambda s: s.element is None and s.count % 5 == 4 )
    def push( s, ele ):
      s.element = ele

    @non_blocking( lambda s: s.value >= 0 )
    def pull( s ):
      return s.value

    def line_trace( s ):
      return "line trace: {}".format(s.value)

    def done( s ):
      return True

  A = Top()
  A.elaborate()
  A.apply( GenDAGPass() )
  A.apply( OpenLoopCLPass() )
  A.lock_in_simulation()

  print "- push_rdy?",
  rdy = A.push.rdy()
  print rdy
  if rdy:
    print "- push!"
    A.push(7)

  print "- push_rdy?",
  rdy = A.push.rdy()
  print rdy
  if rdy:
    print "- push!"
    A.push(8)

  print "- push_rdy?",
  rdy = A.push.rdy()
  print rdy
  if rdy:
    print "- push!"
    A.push(9)

  print "- push_rdy?",
  rdy = A.push.rdy()
  print rdy
  if rdy:
    print "- push!"
    A.push(11)

  print "- push_rdy?",
  rdy = A.push.rdy()
  print rdy
  if rdy:
    print "- push!"
    A.push(13)

  print "- pull!"
  print A.pull()

  print "- pull!"
  print A.pull()

  print "- push!"
  A.push(33)
  print "- push!"
  A.push(55)
  print "- pull!"
  print A.pull()

  # regression

  assert A.num_cycles_executed == 8
