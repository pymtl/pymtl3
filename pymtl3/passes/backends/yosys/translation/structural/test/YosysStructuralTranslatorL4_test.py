#=========================================================================
# YosysStructuralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 13, 2019
"""Test the level 4 yosys-SystemVerilog structural translator."""

import pytest

from pymtl3.passes.backends.verilog.util.test_utility import check_eq
from pymtl3.passes.backends.verilog.util.utility import verilog_reserved

from ....testcases import (
    CaseBits32ArrayConnectSubCompAttrComp,
    CaseBits32ConnectSubCompAttrComp,
    CaseConnectArraySubCompArrayStructIfcComp,
)
from ..YosysStructuralTranslatorL4 import YosysStructuralTranslatorL4


def run_test( case, m ):
  m.elaborate()
  YosysStructuralTranslatorL4.is_verilog_reserved = lambda s, x: x in verilog_reserved
  tr = YosysStructuralTranslatorL4( m )
  tr.clear( m )
  tr.translate_structural( m )

  comps = tr.structural.decl_subcomps[m]

  check_eq( comps["port_decls"],  case.REF_COMP_PORT )
  check_eq( comps["wire_decls"],  case.REF_COMP_WIRE )
  check_eq( comps["connections"], case.REF_COMP_CONN )

@pytest.mark.parametrize(
  'case', [
    CaseBits32ConnectSubCompAttrComp,
    CaseConnectArraySubCompArrayStructIfcComp,
    CaseBits32ArrayConnectSubCompAttrComp,
  ]
)
def test_yosys_structural_L4( case ):
  run_test( case, case.DUT() )
