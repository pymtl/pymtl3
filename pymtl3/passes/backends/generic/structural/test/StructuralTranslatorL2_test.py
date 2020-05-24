#=========================================================================
# StructuralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 21, 2019
"""Test the level 2 structural translators."""

import pytest

from ...testcases import (
    CaseNestedPackedArrayStructComp,
    CaseNestedStructPortOnly,
    CaseStructConstComp,
    CaseStructPortOnly,
    CaseStructWireDrivenComp,
    CaseStructx5PortOnly,
)
from ..StructuralTranslatorL2 import StructuralTranslatorL2
from .TestStructuralTranslator import mk_TestStructuralTranslator


def run_test( case, m ):
  m.elaborate()
  tr = mk_TestStructuralTranslator(StructuralTranslatorL2)(m)
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
    struct_types = tr.structural.decl_type_struct

    assert sorted(struct_types.items(), key=lambda x: str(x[1])) == case.REF_STRUCT
  except AttributeError:
    pass

@pytest.mark.parametrize(
  'case', [
    CaseStructPortOnly,
    CaseStructWireDrivenComp,
    CaseStructConstComp,
    CaseStructx5PortOnly,
    CaseNestedStructPortOnly,
    CaseNestedPackedArrayStructComp,
  ]
)
def test_generic_structural_L2( case ):
  run_test( case, case.DUT() )
