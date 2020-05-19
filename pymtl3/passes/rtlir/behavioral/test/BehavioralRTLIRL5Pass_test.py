#=========================================================================
# BehavioralRTLIRL5Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 2, 2019
"""Test the level 5 behavioral RTLIR passes.

The L5 generation, L5 type check, and visualization passes are invoked. The
generation pass results are verified against a reference AST.
"""

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
from pymtl3.passes.testcases import (
    CaseArrayBits32SubCompPassThroughComp,
    CaseBits32SubCompPassThroughComp,
    CaseCrossHierarchyAccessComp,
    CaseSubCompMissingAttributeComp,
)


def local_do_test( m ):
  """Check if generated behavioral RTLIR is the same as reference."""
  if isinstance(m, type):
    m = m.DUT()
  m.elaborate()
  m.apply( BehavioralRTLIRGenL5Pass( m ) )
  m.apply( BehavioralRTLIRTypeCheckL5Pass( m ) )
  m.apply( BehavioralRTLIRVisualizationPass() )

  try:
    ref = m._rtlir_test_ref
    for blk in m.get_update_blocks():
      upblk = m.get_metadata( BehavioralRTLIRGenL5Pass.rtlir_upblks )[ blk ]
      assert upblk == ref[ blk.__name__ ]
  except AttributeError:
    pass

#-------------------------------------------------------------------------
# Correct test cases
#-------------------------------------------------------------------------

def test_L5_component_attr( do_test ):
  a = CaseBits32SubCompPassThroughComp.DUT()
  a._rtlir_test_ref = { 'upblk' : CombUpblk( 'upblk', [ Assign(
      [Attribute( Base( a ), 'out' )], Attribute(
        Attribute( Base( a ), 'comp' ), 'out' ), True ) ] ) }
  do_test( a )

def test_L5_component_array_index( do_test ):
  a = CaseArrayBits32SubCompPassThroughComp.DUT()
  a._rtlir_test_ref = { 'upblk' : CombUpblk( 'upblk', [ Assign(
      [Attribute( Base( a ), 'out' )], Attribute( Index(
        Attribute( Base( a ), 'comp' ), Number(2) ), 'out' ), True ) ] ) }
  do_test( a )

#-------------------------------------------------------------------------
# PyMTL type errors
#-------------------------------------------------------------------------

def test_L5_component_no_field( do_test ):
  with expected_failure( VarNotDeclaredError, 's.comp does not have field "bar"' ):
    do_test( CaseSubCompMissingAttributeComp )

def test_L5_component_not_port( do_test ):
  with expected_failure( PyMTLTypeError, "comp is not a port of WrappedBits32OutComp subcomponent" ):
    do_test( CaseCrossHierarchyAccessComp )
