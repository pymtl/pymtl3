#=========================================================================
# TranslationImport_closed_loop_component_input_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 6, 2019
"""Closed-loop test cases for translation-import with component and input."""

from random import randint, seed

import pytest

from pymtl3.datatypes import Bits1, Bits16, Bits32, clog2, mk_bits
from pymtl3.dsl import Component, InPort, Interface, OutPort
from pymtl3.passes.rtlir.util.test_utility import do_test

from ..util.test_utility import closed_loop_component_input_test

seed( 0xdeadebeef )

def local_do_test( m ):
  test_vector = m._test_vector
  tv_in = m._tv_in
  closed_loop_component_input_test( m, test_vector, tv_in )

@pytest.mark.parametrize( "Type", [ Bits16, Bits32 ] )
def test_adder( do_test, Type ):
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
  a = A( Type )
  a._test_vector = [ (randint(-255, 255), randint(-255, 255)) for _ in range(10) ]
  a._tv_in = tv_in
  do_test( a )

@pytest.mark.parametrize("Type, n_ports",
  [ (Bits16, 2), (Bits16, 3), (Bits16, 4),
    (Bits32, 2), (Bits32, 3), (Bits32, 4) ]
)
def test_mux( do_test, Type, n_ports ):
  def tv_in( model, test_vector ):
    for i in range(n_ports):
      model.in_[i] = Type( test_vector[i] )
    model.sel = mk_bits( clog2(n_ports) )( test_vector[n_ports] )
  class A( Component ):
    def construct( s, Type, n_ports ):
      s.in_ = [ InPort( Type ) for _ in range(n_ports) ]
      s.sel = InPort( mk_bits( clog2(n_ports) ) )
      s.out = OutPort( Type )
      @s.update
      def add_upblk():
        s.out = s.in_[ s.sel ]
    def line_trace( s ): return "out = " + str( s.out )
  test_vector = []
  for _ in range(10):
    _tmp = []
    for i in range(n_ports):
      _tmp.append( randint(-255, 255) )
    _tmp.append( randint(0, n_ports-1) )
    test_vector.append( _tmp )
  a = A( Type, n_ports )
  a._test_vector = test_vector
  a._tv_in = tv_in
  do_test( a )
