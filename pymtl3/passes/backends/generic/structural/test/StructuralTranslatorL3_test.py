#=========================================================================
# StructuralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 21, 2019
"""Test the level 3 structural translators."""

import pytest

from ...testcases import (
    CaseArrayBits32IfcInComp,
    CaseConnectArrayNestedIfcComp,
    CaseConnectValRdyIfcComp,
)
from ..StructuralTranslatorL3 import StructuralTranslatorL3
from .TestStructuralTranslator import mk_TestStructuralTranslator


def run_test( case, m ):
  m.elaborate()
  tr = mk_TestStructuralTranslator(StructuralTranslatorL3)(m)
  tr.clear( m )
  tr.translate_structural(m)
  try:
    decl_ifcs = tr.structural.decl_ifcs[m]
    assert decl_ifcs == case.REF_IFC
    connections = tr.structural.connections[m]
    assert connections == case.REF_CONN
  except AttributeError:
    pass

@pytest.mark.parametrize(
  'case', [
    CaseConnectValRdyIfcComp,
    CaseArrayBits32IfcInComp,
    CaseConnectArrayNestedIfcComp,
  ]
)
def test_generic_structural_L3( case ):
  run_test( case, case.DUT() )
