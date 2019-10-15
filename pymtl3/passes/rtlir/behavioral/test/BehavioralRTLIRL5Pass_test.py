#=========================================================================
# BehavioralRTLIRL5Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 2, 2019
"""Test the level 5 behavioral RTLIR passes.

The L5 generation, L5 type check, and visualization passes are invoked. The
generation pass results are verified against a reference AST.
"""

import pytest

from pymtl3.datatypes import Bits32
from pymtl3.dsl import Component, OutPort
from pymtl3.dsl.errors import VarNotDeclaredError
from pymtl3.passes.rtlir.behavioral import BehavioralRTLIRVisualizationPass
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIR import *
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRGenL5Pass import (
    BehavioralRTLIRGenL5Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL5Pass import (
    BehavioralRTLIRTypeCheckL5Pass,
)
from pymtl3.passes.rtlir.errors import PyMTLTypeError
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure


def local_do_test( m ):
  """Check if generated behavioral RTLIR is the same as reference."""
  m.elaborate()
  m.apply( BehavioralRTLIRGenL5Pass() )
  m.apply( BehavioralRTLIRTypeCheckL5Pass() )
  m.apply( BehavioralRTLIRVisualizationPass() )

  try:
    ref = m._rtlir_test_ref
    for blk in m.get_update_blocks():
      upblk = m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ]
      assert upblk == ref[ blk.__name__ ]
  except AttributeError:
    pass

#-------------------------------------------------------------------------
# Correct test cases
#-------------------------------------------------------------------------

def test_L5_component_attr( do_test ):
  class B( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.comp = B()
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.comp.out
  a = A()
  a._rtlir_test_ref = { 'upblk' : CombUpblk( 'upblk', [ Assign(
      Attribute( Base( a ), 'out' ), Attribute(
        Attribute( Base( a ), 'comp' ), 'out' ), True ) ] ) }
  do_test( a )

def test_L5_component_array_index( do_test ):
  class B( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.comp = [ B() for _ in range(4) ]
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.comp[2].out
  a = A()
  a._rtlir_test_ref = { 'upblk' : CombUpblk( 'upblk', [ Assign(
      Attribute( Base( a ), 'out' ), Attribute( Index(
        Attribute( Base( a ), 'comp' ), Number(2) ), 'out' ), True ) ] ) }
  do_test( a )

#-------------------------------------------------------------------------
# PyMTL type errors
#-------------------------------------------------------------------------

def test_L5_component_no_field( do_test ):
  class B( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.comp = B()
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.comp.bar
  with expected_failure( VarNotDeclaredError, 's.comp does not have field "bar"' ):
    do_test( A() )

def test_L5_component_not_port( do_test ):
  class C( Component ):
    def construct( s ):
      s.c_out = OutPort( Bits32 )
  class B( Component ):
    def construct( s ):
      s.comp = C()
      s.b_out = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.comp = B()
      s.a_out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.a_out = s.comp.comp.c_out
  with expected_failure( PyMTLTypeError, "comp is not a port of B subcomponent" ):
    do_test( A() )
