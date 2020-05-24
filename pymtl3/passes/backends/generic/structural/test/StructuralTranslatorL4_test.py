#=========================================================================
# StructuralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 21, 2019
"""Test the level 3 structural translators."""

import pytest

from ...testcases import (
    CaseBits32ConnectSubCompAttrComp,
    CaseConnectSubCompIfcHierarchyComp,
)
from ..StructuralTranslatorL4 import StructuralTranslatorL4
from .TestStructuralTranslator import mk_TestStructuralTranslator


def run_test( case, m ):
  m.elaborate()
  tr = mk_TestStructuralTranslator(StructuralTranslatorL4)(m)
  tr.clear( m )
  tr.translate_structural(m)
  connections = tr.structural.connections[m]
  assert connections == case.REF_CONN
  decl_comp = tr.structural.decl_subcomps[m]
  assert decl_comp == case.REF_COMP

@pytest.mark.parametrize(
  'case', [
    CaseBits32ConnectSubCompAttrComp,
    CaseConnectSubCompIfcHierarchyComp,
  ]
)
def test_generic_structural_L4( case ):
  run_test( case, case.DUT() )
