#=========================================================================
# BehavioralRTLIRTmpVar_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Test the temporary variable generation of behavioral RTLIR passes."""

from pymtl3.passes.rtlir.behavioral import (
    BehavioralRTLIRGenPass,
    BehavioralRTLIRTypeCheckPass,
    BehavioralRTLIRVisualizationPass,
)
from pymtl3.passes.rtlir.errors import PyMTLTypeError
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.rtlir.rtype import RTLIRType as rt
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure
from pymtl3.passes.testcases import (
    Bits32Foo,
    CaseBits32TmpWireComp,
    CaseScopeTmpWireOverwriteConflictComp,
    CaseStructTmpWireComp,
    CaseTmpWireOverwriteConflictComp,
)


def local_do_test( m ):
  """Check if generated behavioral RTLIR is the same as reference."""
  m.apply( BehavioralRTLIRGenPass( m ) )
  m.apply( BehavioralRTLIRTypeCheckPass( m ) )
  m.apply( BehavioralRTLIRVisualizationPass() )
  ref = m._rtlir_tmpvar_ref
  rtlir_tmpvars = m.get_metadata( BehavioralRTLIRTypeCheckPass.rtlir_tmpvars )

  for tvar_name in ref.keys():
    assert tvar_name in rtlir_tmpvars
    assert rtlir_tmpvars[tvar_name] == ref[tvar_name]

def test_tmp_wire( do_test ):
  a = CaseBits32TmpWireComp.DUT()
  a.elaborate()
  a._rtlir_tmpvar_ref = {('u', 'upblk') : rt.Wire(rdt.Vector(32))}
  do_test( a )

def test_tmp_wire_struct( do_test ):
  a = CaseStructTmpWireComp.DUT()
  a.elaborate()
  a._rtlir_tmpvar_ref = \
    {('u', 'upblk') : rt.Wire(rdt.Struct(Bits32Foo, {'foo':rdt.Vector(32)}))}
  do_test( a )

def test_tmp_wire_overwrite_conflict_type( do_test ):
  a = CaseTmpWireOverwriteConflictComp.DUT()
  a.elaborate()
  with expected_failure( PyMTLTypeError, "conflicting type" ):
    do_test( a )

def test_tmp_scope_conflict_type( do_test ):
  a = CaseScopeTmpWireOverwriteConflictComp.DUT()
  a.elaborate()
  with expected_failure( PyMTLTypeError, "conflicting type" ):
    do_test( a )
