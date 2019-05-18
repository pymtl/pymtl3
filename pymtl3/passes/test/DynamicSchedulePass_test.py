#=========================================================================
# DynamicSchedulePass_test.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Apr 19, 2019

from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.dsl.errors import UpblkCyclicError
from pymtl3.passes import DynamicSchedulePass, GenDAGPass, SimpleTickPass


def _test_model( cls ):
  A = cls()
  A.elaborate()
  A.apply( GenDAGPass() )
  A.apply( DynamicSchedulePass() )
  A.apply( SimpleTickPass() )
  A.lock_in_simulation()

  T = 0
  while T < 5:
    A.tick()
    print(A.line_trace())
    T += 1

def test_false_cyclic_dependency():

  class Top(Component):

    def construct( s ):
      s.a = Wire(int)
      s.b = Wire(int)
      s.c = Wire(int)
      s.d = Wire(int)
      s.e = Wire(int)
      s.f = Wire(int)
      s.g = Wire(int)
      s.h = Wire(int)
      s.i = Wire(int)
      s.j = Wire(int)

      @s.update
      def up1():
        s.a = 10 + s.i
        s.b = s.d + 1

      @s.update
      def up2():
        s.c = s.a + 1
        s.e = s.d + 1

      @s.update
      def up3():
        s.d = s.c + 1
        print("up3 prints out d =", s.d)

      @s.update
      def up4():
        s.f = s.d + 1

      @s.update
      def up5():
        s.g = s.c + 1
        s.h = s.j + 1
        print("up5 prints out h =", s.h)

      @s.update
      def up6():
        s.i = s.i + 1

      @s.update
      def up7():
        s.j = s.g + 1

    def done( s ):
      return True

    def line_trace( s ):
      return "a {} | b {} | c {} | d {} | e {} | f {} | g {} | h {} | i {} | j {}" \
              .format( s.a, s.b, s.c, s.d, s.e, s.f, s.g, s.h, s.i, s.j )

  _test_model( Top )

def test_combinational_loop():

  class Top(Component):

    def construct( s ):
      s.a = Wire(int)
      s.b = Wire(int)
      s.c = Wire(int)
      s.d = Wire(int)

      @s.update
      def up1():
        s.b = s.d + 1

      @s.update
      def up2():
        s.c = s.b + 1

      @s.update
      def up3():
        s.d = s.c + 1
        print("up3 prints out d =", s.d)


    def done( s ):
      return True

    def line_trace( s ):
      return "a {} | b {} | c {} | d {}" \
              .format( s.a, s.b, s.c, s.d )


  try:
    _test_model( Top )
  except UpblkCyclicError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown UpblkCyclicError.")
