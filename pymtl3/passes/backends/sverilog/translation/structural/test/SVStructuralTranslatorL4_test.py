#=========================================================================
# SVStructuralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 4 SystemVerilog structural translator."""

import pytest

from pymtl3.passes.backends.sverilog.util.test_utility import check_eq
from pymtl3.passes.backends.sverilog.util.utility import sverilog_reserved

from ....testcases import (
    CaseBits32ArrayConnectSubCompAttrComp,
    CaseBits32ConnectSubCompAttrComp,
    CaseConnectArraySubCompArrayStructIfcComp,
)
from ..SVStructuralTranslatorL4 import SVStructuralTranslatorL4


def run_test( case, m ):
  m.elaborate()
  SVStructuralTranslatorL4.is_sverilog_reserved = lambda s, x: x in sverilog_reserved
  tr = SVStructuralTranslatorL4( m )
  tr.clear( m )
  tr.translate_structural( m )
  subcomps = tr.structural.decl_subcomps

  check_eq( subcomps[m], case.REF_COMP )

@pytest.mark.parametrize(
  'case', [
    CaseBits32ConnectSubCompAttrComp,
    CaseConnectArraySubCompArrayStructIfcComp,
    CaseBits32ArrayConnectSubCompAttrComp,
  ]
)
def test_sverilog_structural_L4( case ):
  run_test( case, case.DUT() )
