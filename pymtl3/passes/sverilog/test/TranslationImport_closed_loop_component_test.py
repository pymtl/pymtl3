#=========================================================================
# TranslationImport_closed_loop_component_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 6, 2019
"""Closed-loop test cases for translation-import with component."""

from __future__ import absolute_import, division, print_function

from itertools import product

import hypothesis.strategies as st
import pytest
from hypothesis import given, settings

from pymtl3.datatypes import Bits1, Bits16, Bits32, clog2, mk_bits
from pymtl3.dsl import Component, InPort, Interface, OutPort

from ..util.test_utility import DataStrategy, closed_loop_component_test


# Use @given(st.data()) to draw input vector inside the test function
#  - also note that data should the rightmost argument of the test function
# Set deadline to None to avoid checking how long each test spin is
# Set max_examples to limit the number of attempts after multiple successes
@given( st.data() )
@settings( deadline = None, max_examples = 5 )
@pytest.mark.parametrize( "Type", [ Bits16, Bits32 ] )
def test_adder( Type, data ):
  class A( Component ):
    def construct( s, Type ):
      s.in_1 = InPort( Type )
      s.in_2 = InPort( Type )
      s.out = OutPort( Type )
      @s.update
      def add_upblk():
        s.out = s.in_1 + s.in_2
    def line_trace( s ): return "sum = " + str( s.out )
  a = A( Type )
  closed_loop_component_test( a, data.draw( DataStrategy( a ) ) )

@given( st.data() )
@settings( deadline = None, max_examples = 5 )
@pytest.mark.parametrize("Type, n_ports", product([Bits16, Bits32], [2, 4]))
def test_mux( Type, n_ports, data ):
  class A( Component ):
    def construct( s, Type, n_ports ):
      s.in_ = [ InPort( Type ) for _ in xrange(n_ports) ]
      s.sel = InPort( mk_bits( clog2(n_ports) ) )
      s.out = OutPort( Type )
      @s.update
      def add_upblk():
        s.out = s.in_[ s.sel ]
    def line_trace( s ): return "out = " + str( s.out )
  a = A( Type, n_ports )
  closed_loop_component_test( a, data.draw( DataStrategy( a ) ) )
