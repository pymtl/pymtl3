#=========================================================================
# YosysStructuralTranslatorL1_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 13, 2019
"""Test the level 1 yosys-SystemVerilog structural translator."""

import pytest

from pymtl3.passes.backends.verilog.util.test_utility import check_eq
from pymtl3.passes.backends.verilog.util.utility import verilog_reserved

from ....testcases import (
    CaseBitSelOverBitSelComp,
    CaseBitSelOverPartSelComp,
    CaseConnectBitsConstToOutComp,
    CaseConnectBitSelToOutComp,
    CaseConnectConstToOutComp,
    CaseConnectInToWireComp,
    CaseConnectSliceToOutComp,
    CasePartSelOverBitSelComp,
    CasePartSelOverPartSelComp,
)
from ..YosysStructuralTranslatorL1 import YosysStructuralTranslatorL1


def run_test( case, m ):
  m.elaborate()
  YosysStructuralTranslatorL1.is_verilog_reserved = lambda s, x: x in verilog_reserved
  tr = YosysStructuralTranslatorL1( m )
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
    CaseConnectInToWireComp,
    CaseConnectBitsConstToOutComp,
    CaseConnectConstToOutComp,
    CaseConnectBitSelToOutComp,
    CaseConnectSliceToOutComp,
    CaseBitSelOverBitSelComp,
    CaseBitSelOverPartSelComp,
    CasePartSelOverBitSelComp,
    CasePartSelOverPartSelComp,
  ]
)
def test_yosys_structural_L1( case ):
  run_test( case, case.DUT() )
