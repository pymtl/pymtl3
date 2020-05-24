#=========================================================================
# BehavioralRTLIRL3Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 2, 2019
"""Test the level 3 behavioral RTLIR passes.

The L3 generation, L3 type check, and visualization passes are invoked. The
generation pass results are verified against a reference AST.
"""

from pymtl3.dsl.errors import VarNotDeclaredError
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIR import *
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRGenL3Pass import (
    BehavioralRTLIRGenL3Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL3Pass import (
    BehavioralRTLIRTypeCheckL3Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRVisualizationPass import (
    BehavioralRTLIRVisualizationPass,
)
from pymtl3.passes.rtlir.errors import PyMTLSyntaxError, PyMTLTypeError
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure
from pymtl3.passes.testcases import (
    Bits32Foo,
    CaseBits32FooInBits32OutComp,
    CaseBits32FooInstantiationComp,
    CaseBits32FooKwargComp,
    CaseBitsAttributeComp,
    CaseConstStructInstComp,
    CaseStructMissingAttributeComp,
)


def local_do_test( m ):
  """Check if generated behavioral RTLIR is the same as reference."""
  if isinstance(m, type):
    m = m.DUT()
  m.elaborate()
  m.apply( BehavioralRTLIRGenL3Pass( m ) )
  m.apply( BehavioralRTLIRTypeCheckL3Pass( m ) )
  m.apply( BehavioralRTLIRVisualizationPass() )

  try:
    ref = m._rtlir_test_ref
    for blk in m.get_update_blocks():
      upblk = m.get_metadata( BehavioralRTLIRGenL3Pass.rtlir_upblks )[ blk ]
      assert upblk == ref[ blk.__name__ ]
  except AttributeError:
    pass

#-------------------------------------------------------------------------
# Correct test cases
#-------------------------------------------------------------------------

def test_L3_struct_attr( do_test ):
  a = CaseBits32FooInBits32OutComp.DUT()
  a._rtlir_test_ref = { 'upblk' : CombUpblk( 'upblk', [ Assign(
      [Attribute( Base( a ), 'out' )], Attribute(
        Attribute( Base( a ), 'in_' ), 'foo' ), True ) ] ) }
  do_test( a )

def test_L3_struct_inst_kwargs( do_test ):
  a = CaseBits32FooKwargComp.DUT()
  a._rtlir_test_ref = { 'upblk' : CombUpblk( 'upblk', [ Assign(
      [Attribute( Base( a ), 'out' )], StructInst(
        Bits32Foo, [ SizeCast( 32, Number( 42 ) ) ] ), True ) ] ) }
  with expected_failure( PyMTLSyntaxError, 'keyword argument is not supported' ):
    do_test( a )

def test_L3_struct_inst( do_test ):
  a = CaseBits32FooInstantiationComp.DUT()
  a._rtlir_test_ref = { 'upblk' : CombUpblk( 'upblk', [ Assign(
      [Attribute( Base( a ), 'out' )], StructInst(
        Bits32Foo, [ Number( 42 ) ] ), True ) ] ) }
  do_test( a )

def test_L3_const_struct( do_test ):
  a = CaseConstStructInstComp.DUT()
  a._rtlir_test_ref = { 'upblk' : CombUpblk( 'upblk', [ Assign(
      [Attribute( Base( a ), 'out' )], SizeCast(32, Number(0)), True ) ] ) }
  do_test( a )

#-------------------------------------------------------------------------
# PyMTL type errors
#-------------------------------------------------------------------------

def test_L3_vector_attr( do_test ):
  with expected_failure( VarNotDeclaredError, 's.in_ does not have field "foo"' ):
    do_test( CaseBitsAttributeComp )

def test_L3_struct_no_field( do_test ):
  with expected_failure( VarNotDeclaredError, 's.in_ does not have field "bar"' ):
    do_test( CaseStructMissingAttributeComp )
