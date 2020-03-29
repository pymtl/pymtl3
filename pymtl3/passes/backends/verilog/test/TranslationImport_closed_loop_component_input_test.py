#=========================================================================
# TranslationImport_closed_loop_component_input_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 6, 2019
"""Closed-loop test cases for translation-import with component and input."""

from random import randint, seed

import pytest

from pymtl3.datatypes import Bits1, Bits16, Bits32, clog2, mk_bits
from pymtl3.dsl import Component, InPort, Interface, OutPort, update, update_ff
from pymtl3.passes.rtlir.util.test_utility import do_test

from ..util.test_utility import closed_loop_component_input_test

seed( 0xdeadebeef )

def local_do_test( m ):
  closed_loop_component_input_test( m, m._tvs, m._tv_in )

@pytest.mark.parametrize( "Type", [ Bits16, Bits32 ] )
def test_adder( do_test, Type ):
  def tv_in( model, tv ):
    model.in_1 @= tv[0]
    model.in_2 @= tv[1]
  class A( Component ):
    def construct( s, Type ):
      s.in_1 = InPort( Type )
      s.in_2 = InPort( Type )
      s.out = OutPort( Type )
      @update
      def add_upblk():
        s.out @= s.in_1 + s.in_2
    def line_trace( s ): return "sum = " + str( s.out )
  a = A( Type )
  a._tvs = [ (randint(-255, 255), randint(-255, 255)) for _ in range(10) ]
  a._tv_in = tv_in
  do_test( a )

@pytest.mark.parametrize("Type, n_ports",
  [ (Bits16, 2), (Bits16, 3), (Bits16, 4),
    (Bits32, 2), (Bits32, 3), (Bits32, 4) ]
)
def test_mux( do_test, Type, n_ports ):
  def tv_in( model, tv ):
    for i in range(n_ports):
      model.in_[i] @= tv[i]
    model.sel @= tv[n_ports]
  class A( Component ):
    def construct( s, Type, n_ports ):
      s.in_ = [ InPort( Type ) for _ in range(n_ports) ]
      s.sel = InPort( mk_bits( clog2(n_ports) ) )
      s.out = OutPort( Type )
      @update
      def add_upblk():
        s.out @= s.in_[ s.sel ]
    def line_trace( s ): return "out = " + str( s.out )
  tvs = []
  for _ in range(10):
    _tmp = []
    for i in range(n_ports):
      _tmp.append( randint(-255, 255) )
    _tmp.append( randint(0, n_ports-1) )
    tvs.append( _tmp )
  a = A( Type, n_ports )
  a._tvs = tvs
  a._tv_in = tv_in
  do_test( a )
