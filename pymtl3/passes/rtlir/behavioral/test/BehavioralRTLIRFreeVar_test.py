#=========================================================================
# BehavioralRTLIRFreeVar_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Test the free variable generation of behavioral RTLIR passes."""

from pymtl3.datatypes import Bits32, bitstruct
from pymtl3.dsl import Component, InPort, OutPort
from pymtl3.passes.rtlir.behavioral import (
    BehavioralRTLIRGenPass,
    BehavioralRTLIRTypeCheckPass,
)
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure
from pymtl3.passes.testcases import (
    CaseBits32ClosureConstruct,
    CaseBits32ClosureGlobal,
    CaseStructClosureGlobal,
    pymtl_Bits_global_freevar,
)


def local_do_test( m ):
  """Check if generated behavioral RTLIR is the same as reference."""
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )
  ref = m._rtlir_freevar_ref
  ns = m._pass_behavioral_rtlir_type_check

  for fvar_name in ref.keys():
    assert fvar_name in ns.rtlir_freevars
    assert ns.rtlir_freevars[fvar_name] == ref[ fvar_name ]

def test_pymtl_Bits_closure_construct( do_test ):
  a = CaseBits32ClosureConstruct.DUT()
  a.elaborate()
  a._rtlir_freevar_ref = { 'foo' : a.fvar_ref }
  do_test( a )

def test_pymtl_Bits_global( do_test ):
  a = CaseBits32ClosureGlobal.DUT()
  a.elaborate()
  a._rtlir_freevar_ref = \
    { 'pymtl_Bits_global_freevar' : pymtl_Bits_global_freevar }
  do_test( a )

def test_pymtl_struct_closure( do_test ):
  a = CaseStructClosureGlobal.DUT()
  a.elaborate()
  a._rtlir_freevar_ref = { 'foo' : a._foo }
  do_test( a )
