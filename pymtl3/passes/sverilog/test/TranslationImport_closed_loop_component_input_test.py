#=========================================================================
# TranslationImport_closed_loop_component_input_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 6, 2019
"""Closed-loop test cases for translation-import with component and input."""

from __future__ import absolute_import, division, print_function

import random

import pytest

from pymtl3.datatypes import Bits1, Bits16, Bits32, mk_bits
from pymtl3.dsl import Component, InPort, Interface, OutPort

from ..util.test_utility import closed_loop_component_input_test

random.seed( 0xdeadebeef )

@pytest.mark.parametrize( "Type", [ Bits16, Bits32 ] )
def test_adder( Type ):
  def tv_in( model, test_vector ):
    model.in_1 = Type( test_vector[0] )
    model.in_2 = Type( test_vector[1] )
  class A( Component ):
    def construct( s, Type ):
      s.in_1 = InPort( Type )
      s.in_2 = InPort( Type )
      s.out = OutPort( Type )
      @s.update
      def add_upblk():
        s.out = s.in_1 + s.in_2
    def line_trace( s ): return "sum = " + str( s.out )
  test_vector = \
    [(random.randint(-255, 255), random.randint(-255, 255)) for _ in range(10)]
  closed_loop_component_input_test( A( Type ), test_vector, tv_in )
