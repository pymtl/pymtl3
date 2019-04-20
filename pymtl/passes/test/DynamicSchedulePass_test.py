#=========================================================================
# ComponentLevel2_test.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Nov 3, 2018

from pymtl import *
from pymtl.passes import DynamicSchedulePass, GenDAGPass

from collections import deque

def _test_model( cls ):
  A = cls()
  A.elaborate()
  A.apply( GenDAGPass() )
  A.apply( DynamicSchedulePass() )

def test_simple():

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
        s.b = s.d

      @s.update
      def up2():
        s.c = s.b
        s.e = s.d + 1

      @s.update
      def up3():
        s.d = s.c

      @s.update
      def up4():
        s.f = s.d

      @s.update
      def up5():
        s.g = s.c
        s.h = s.j + 1

      @s.update
      def up6():
        s.i = 100

      @s.update
      def up7():
        s.j = s.g + 1
        print s.j

    def done( s ):
      return True

  _test_model( Top )
