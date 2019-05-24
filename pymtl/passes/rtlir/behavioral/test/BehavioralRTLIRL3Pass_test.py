#=========================================================================
# BehavioralRTLIRL3Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 2, 2019
"""Test the level 3 behavioral RTLIR passes.

The L3 generation, L3 type check, and visualization passes are invoked. The
generation pass results are verified against a reference AST.
"""

from __future__ import absolute_import, division, print_function

import pytest

from pymtl import *
from pymtl.dsl.errors import VarNotDeclaredError
from pymtl.passes.rtlir.behavioral import BehavioralRTLIRVisualizationPass
from pymtl.passes.rtlir.behavioral.BehavioralRTLIR import *
from pymtl.passes.rtlir.behavioral.BehavioralRTLIRGenL3Pass import (
    BehavioralRTLIRGenL3Pass,
)
from pymtl.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL3Pass import (
    BehavioralRTLIRTypeCheckL3Pass,
)
from pymtl.passes.rtlir.errors import PyMTLSyntaxError, PyMTLTypeError
from pymtl.passes.rtlir.test.test_utility import do_test, expected_failure


def local_do_test( m ):
  """Check if generated behavioral RTLIR is the same as reference."""
  m.elaborate()
  m.apply( BehavioralRTLIRGenL3Pass() )
  m.apply( BehavioralRTLIRTypeCheckL3Pass() )
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

def test_L3_struct_attr( do_test ):
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = Bits32( foo )
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_.foo
  a = A()
  a._rtlir_test_ref = { 'upblk' : CombUpblk( 'upblk', [ Assign(
      Attribute( Base( a ), 'out' ), Attribute(
        Attribute( Base( a ), 'in_' ), 'foo' ) ) ] ) }
  do_test( a )

@pytest.mark.xfail( reason = "Behavioral RTLIR does not support struct instantiation yet" )
def test_L3_struct_inst( do_test ):
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = Bits32( foo )
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = B( foo = Bits32( 42 ) )
  a = A()
  a._rtlir_test_ref = { 'upblk' : CombUpblk( 'upblk', [ Assign(
      Attribute( Base( a ), 'out' ), StructInst(
        B, [ 'foo' ], [ SizeCast( 32, Number( 42 ) ) ] ) ) ] ) }
  do_test( a )

#-------------------------------------------------------------------------
# PyMTL type errors
#-------------------------------------------------------------------------

def test_L3_vector_attr( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = s.in_.foo
  with expected_failure( VarNotDeclaredError, 's.in_ does not have field "foo"' ):
    do_test( A() )

def test_L3_struct_no_field( do_test ):
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = Bits32( foo )
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = s.in_.bar
  with expected_failure( VarNotDeclaredError, 's.in_ does not have field "bar"' ):
    do_test( A() )

@pytest.mark.xfail( reason = "RTLIR conversion does not support const struct yet" )
def test_L3_const_struct( do_test ):
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = Bits32( foo )
  class A( Component ):
    def construct( s ):
      s.in_ = B()
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = s.in_.foo
  with expected_failure( PyMTLTypeError, "constant struct is not supported" ):
    do_test( A() )

#-------------------------------------------------------------------------
# PyMTL syntax errors
#-------------------------------------------------------------------------

@pytest.mark.xfail( reason = "StructInst is not supported yet" )
def test_L3_call_struct_inst( do_test ):
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = Bits32( foo )
  class A( Component ):
    def construct( s ):
      s.out = OutPort( B )
      @s.update
      def upblk():
        s.out = B( 42 )
  do_test( A() )
