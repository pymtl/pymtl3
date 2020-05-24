#=========================================================================
# YosysStructuralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 13, 2019
"""Test the level 2 yosys-SystemVerilog structural translator."""

import pytest

from pymtl3.passes.backends.verilog.util.test_utility import check_eq
from pymtl3.passes.backends.verilog.util.utility import verilog_reserved

from ....testcases import (
    CaseConnectArrayStructAttrToOutComp,
    CaseConnectConstStructAttrToOutComp,
    CaseConnectLiteralStructComp,
    CaseConnectNestedStructPackedArrayComp,
)
from ..YosysStructuralTranslatorL2 import YosysStructuralTranslatorL2


def run_test( case, m ):
  m.elaborate()
  YosysStructuralTranslatorL2.is_verilog_reserved = lambda s, x: x in verilog_reserved
  tr = YosysStructuralTranslatorL2( m )
  tr.clear( m )
  tr.translate_structural( m )

  ports = tr.structural.decl_ports[m]
  wires = tr.structural.decl_wires[m]
  conns = tr.structural.connections[m]

  check_eq( ports["port_decls"],  case.REF_PORTS_PORT )
  check_eq( ports["wire_decls"],  case.REF_PORTS_WIRE )
  check_eq( ports["connections"], case.REF_PORTS_CONN )
  check_eq( wires, case.REF_WIRE )
  check_eq( conns, case.REF_CONN )

@pytest.mark.parametrize(
  'case', [
    CaseConnectConstStructAttrToOutComp,
    CaseConnectLiteralStructComp,
    CaseConnectArrayStructAttrToOutComp,
    CaseConnectNestedStructPackedArrayComp,
  ]
)
def test_yosys_structural_L2( case ):
  run_test( case, case.DUT() )
