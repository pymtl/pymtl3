#=========================================================================
# OpenLoopCLPass_test.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Apr 19, 2019

from pymtl import *
from pymtl.passes import OpenLoopCLPass, GenDAGPass, SimpleSchedPass, SimpleTickPass
from pymtl.dsl.errors import UpblkCyclicError

from collections import deque

def _test_model( cls ):
  A = cls()
  A.elaborate()
  A.apply( GenDAGPass() )
  A.apply( OpenLoopCLPass() )
  #  A.apply( SimpleSchedPass() )
  #  A.apply( SimpleTickPass() )
  A.lock_in_simulation()

  A.push(7)
  print A.pull()

  print A.pull()

  A.push(1333)
  A.push(255)
  print A.pull()

  #  T = 0
  #  while T < 5:
    #  A.tick()
    #  print A.line_trace()
    #  T += 1

guarded_ifc, GuardedCalleeIfc, GuardedCallerIfc = generate_guard_decorator_ifcs( "rdy" )

def test_top_level_method():

  class Top(Component):

    def construct( s ):
      s.element = None

      s.count = Wire(int)
      s.amp   = Wire(int)

      s.value = OutPort(int)

      @s.update_on_edge
      def up_incr():
        s.count = s.count + 1

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

      s.add_constraints(
        M( s.push ) < U( up_compose_in ),
        U( up_compose_in ) < M( s.pull ), # bypass behavior
      )

    @method_port
    def push( s, ele ):
      if s.element is not None:
        s.element = ele

    @method_port
    def pull( s ):
      return s.value

    def line_trace( s ):
      return "{}".format(s.value)

    def done( s ):
      return True

  _test_model( Top )
