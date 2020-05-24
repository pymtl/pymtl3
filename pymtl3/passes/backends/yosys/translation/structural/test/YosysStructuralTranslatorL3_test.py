#=========================================================================
# YosysStructuralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 13, 2019
"""Test the level 3 yosys-SystemVerilog structural translator."""

import pytest

from pymtl3.passes.backends.verilog.util.test_utility import check_eq
from pymtl3.passes.backends.verilog.util.utility import verilog_reserved

from ....testcases import (
    CaseConnectArrayBits32FooIfcComp,
    CaseConnectArrayNestedIfcComp,
    CaseConnectValRdyIfcComp,
)
from ..YosysStructuralTranslatorL3 import YosysStructuralTranslatorL3


def run_test( case, m ):
  m.elaborate()
  YosysStructuralTranslatorL3.is_verilog_reserved = lambda s, x: x in verilog_reserved
  tr = YosysStructuralTranslatorL3( m )
  tr.clear( m )
  tr.translate_structural( m )

  ports = tr.structural.decl_ifcs[m]
  conns = tr.structural.connections[m]

  check_eq( ports["port_decls"],  case.REF_IFC_PORT )
  check_eq( ports["wire_decls"],  case.REF_IFC_WIRE )
  check_eq( ports["connections"], case.REF_IFC_CONN )
  check_eq( conns, case.REF_CONN )

@pytest.mark.parametrize(
  'case', [
    CaseConnectValRdyIfcComp,
    CaseConnectArrayBits32FooIfcComp,
    CaseConnectArrayNestedIfcComp,
  ]
)
def test_yosys_structural_L3( case ):
  run_test( case, case.DUT() )
