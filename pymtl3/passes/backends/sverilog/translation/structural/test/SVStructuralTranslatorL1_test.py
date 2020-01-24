#=========================================================================
# SVStructuralTranslatorL1_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 1 SystemVerilog structural translator."""

import pytest

from pymtl3.passes.backends.sverilog.util.test_utility import check_eq
from pymtl3.passes.backends.sverilog.util.utility import sverilog_reserved

from ....testcases import (
    CaseConnectBitsConstToOutComp,
    CaseConnectBitSelToOutComp,
    CaseConnectConstToOutComp,
    CaseConnectInToWireComp,
    CaseConnectSliceToOutComp,
)
from ..SVStructuralTranslatorL1 import SVStructuralTranslatorL1


def run_test( case, m ):
  m.elaborate()
  SVStructuralTranslatorL1.is_sverilog_reserved = lambda s, x: x in sverilog_reserved
  tr = SVStructuralTranslatorL1( m )
  tr.clear( m )
  tr.translate_structural( m )

  ports = tr.structural.decl_ports[m]
  wires = tr.structural.decl_wires[m]
  consts = tr.structural.decl_consts[m]
  conns = tr.structural.connections[m]

  check_eq( ports,  case.REF_PORT  )
  check_eq( wires,  case.REF_WIRE  )
  check_eq( consts, case.REF_CONST )
  check_eq( conns,  case.REF_CONN  )

@pytest.mark.parametrize(
  'case', [
    CaseConnectInToWireComp,
    CaseConnectBitsConstToOutComp,
    CaseConnectConstToOutComp,
    CaseConnectBitSelToOutComp,
    CaseConnectSliceToOutComp,
  ]
)
def test_sverilog_structural_L1( case ):
  run_test( case, case.DUT() )
