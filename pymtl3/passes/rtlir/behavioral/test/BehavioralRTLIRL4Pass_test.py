#=========================================================================
# BehavioralRTLIRL4Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 2, 2019
"""Test the level 4 behavioral RTLIR passes.

The L4 generation, L4 type check, and visualization passes are invoked. The
generation pass results are verified against a reference AST.
"""

from pymtl3.dsl.errors import VarNotDeclaredError
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIR import *
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRGenL4Pass import (
    BehavioralRTLIRGenL4Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL4Pass import (
    BehavioralRTLIRTypeCheckL4Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRVisualizationPass import (
    BehavioralRTLIRVisualizationPass,
)
from pymtl3.passes.rtlir.errors import PyMTLSyntaxError, PyMTLTypeError
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure
from pymtl3.passes.testcases import (
    CaseArrayInterfacesComp,
    CaseInterfaceAttributeComp,
    CaseInterfaceMissingAttributeComp,
)


def local_do_test( m ):
  """Check if generated behavioral RTLIR is the same as reference."""
  if isinstance(m, type):
    m = m.DUT()
  m.elaborate()
  m.apply( BehavioralRTLIRGenL4Pass( m ) )
  m.apply( BehavioralRTLIRTypeCheckL4Pass( m ) )
  m.apply( BehavioralRTLIRVisualizationPass() )

  try:
    ref = m._rtlir_test_ref
    for blk in m.get_update_blocks():
      upblk = m.get_metadata( BehavioralRTLIRGenL4Pass.rtlir_upblks )[ blk ]
      assert upblk == ref[ blk.__name__ ]
  except AttributeError:
    pass

#-------------------------------------------------------------------------
# Correct test cases
#-------------------------------------------------------------------------

def test_L4_interface_attr( do_test ):
  a = CaseInterfaceAttributeComp.DUT()
  a._rtlir_test_ref = { 'upblk' : CombUpblk( 'upblk', [ Assign(
      [Attribute( Base( a ), 'out' )], Attribute(
        Attribute( Base( a ), 'in_' ), 'foo' ), True ) ] ) }
  do_test( a )

def test_L4_interface_array_index( do_test ):
  a = CaseArrayInterfacesComp.DUT()
  a._rtlir_test_ref = { 'upblk' : CombUpblk( 'upblk', [ Assign(
      [Attribute( Base( a ), 'out' )], Attribute( Index(
        Attribute( Base( a ), 'in_' ), Number(2) ), 'foo' ), True ) ] ) }
  do_test( a )

#-------------------------------------------------------------------------
# PyMTL type errors
#-------------------------------------------------------------------------

def test_L4_interface_no_field( do_test ):
  with expected_failure( VarNotDeclaredError, 's.in_ does not have field "bar"' ):
    do_test( CaseInterfaceMissingAttributeComp )
