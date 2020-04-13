#=========================================================================
# StructuralTranslatorL1_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 21, 2019
"""Test the level 1 structural translators."""

import pytest

from pymtl3 import Bits4, Bits16
from pymtl3.passes.rtlir.errors import RTLIRConversionError
from pymtl3.passes.rtlir.util.test_utility import expected_failure

from ...testcases import (
    CaseBits32ArrayClosureConstruct,
    CaseBits32ClosureConstruct,
    CaseBits32PortOnly,
    CaseBits32Wirex5DrivenComp,
    CaseBits32x5PortOnly,
    CaseComponentArgsComp,
    CaseComponentDefaultArgsComp,
    CaseConnectBitSelToOutComp,
    CaseConnectConstToOutComp,
    CaseConnectInToWireComp,
    CaseConnectPortIndexComp,
    CaseConnectSliceToOutComp,
    CaseDoubleStarArgComp,
    CaseMixedDefaultArgsComp,
    CaseStarArgComp,
    CaseWiresDrivenComp,
)
from ..StructuralTranslatorL1 import StructuralTranslatorL1
from .TestStructuralTranslator import mk_TestStructuralTranslator


def run_test( case, m ):
  m.elaborate()
  tr = mk_TestStructuralTranslator(StructuralTranslatorL1)(m)
  tr.clear( m )
  tr.translate_structural(m)
  try:
    name = tr.structural.component_unique_name[m]
    assert name == case.REF_NAME
    decl_ports = tr.structural.decl_ports[m]
    assert decl_ports == case.REF_PORT
    decl_wires = tr.structural.decl_wires[m]
    assert decl_wires == case.REF_WIRE
    decl_consts = tr.structural.decl_consts[m]
    assert decl_consts == case.REF_CONST
    connections = tr.structural.connections[m]
    assert connections == case.REF_CONN
    vector_types = tr.structural.decl_type_vector

    assert list(vector_types.items()) == case.REF_VECTOR
  except AttributeError:
    pass

def test_component_args():
  case = CaseComponentArgsComp
  run_test( case, case.DUT( Bits4(0), Bits16(42) ))

def test_component_default_args():
  case = CaseComponentDefaultArgsComp
  run_test( case, case.DUT( Bits4(0) ) )

def test_component_kw_args():
  case = CaseComponentArgsComp
  run_test( case, case.DUT( foo = Bits4(0), bar = Bits16(42) ) )

def test_component_star_args():
  args = [ Bits4(0), Bits16(42) ]
  case = CaseStarArgComp
  with expected_failure( RTLIRConversionError, "varargs are not allowed" ):
    run_test( case, case.DUT( *args ) )

def test_component_star_args_ungroup():
  args = [ Bits4(0), Bits16(42) ]
  case = CaseComponentArgsComp
  run_test( case, case.DUT( *args ) )

def test_component_double_star_args():
  kwargs = { 'foo':Bits4(0), 'bar':Bits16(42) }
  case = CaseDoubleStarArgComp
  with expected_failure( RTLIRConversionError, "keyword args are not allowed" ):
    run_test( case, case.DUT( **kwargs ) )

def test_component_double_star_args_ungroup():
  kwargs = { 'foo':Bits4(0), 'bar':Bits16(42) }
  case = CaseComponentArgsComp
  run_test( case, case.DUT( **kwargs ) )

def test_component_mixed_kw_args():
  case = CaseMixedDefaultArgsComp
  run_test( case, case.DUT( Bits4(0), bar = Bits16(42) ) )

@pytest.mark.parametrize(
  'case', [
    CaseBits32PortOnly,
    CaseBits32x5PortOnly,
    CaseWiresDrivenComp,
    CaseBits32Wirex5DrivenComp,
    CaseBits32ClosureConstruct,
    CaseBits32ArrayClosureConstruct,
    CaseConnectBitSelToOutComp,
    CaseConnectSliceToOutComp,
    CaseConnectPortIndexComp,
    CaseConnectInToWireComp,
    CaseConnectConstToOutComp,
  ]
)
def test_generic_structural_L1( case ):
  run_test( case, case.DUT() )
