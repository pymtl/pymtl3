#=========================================================================
# SVStructuralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 2 SystemVerilog structural translator."""

import pytest

from pymtl3.passes.backends.sverilog.util.test_utility import check_eq
from pymtl3.passes.backends.sverilog.util.utility import sverilog_reserved

from ....testcases import (
    CaseConnectArrayStructAttrToOutComp,
    CaseConnectConstStructAttrToOutComp,
    CaseConnectLiteralStructComp,
    CaseConnectNestedStructPackedArrayComp,
)
from ..SVStructuralTranslatorL2 import SVStructuralTranslatorL2


def run_test( case, m ):
  m.elaborate()
  SVStructuralTranslatorL2.is_sverilog_reserved = lambda s, x: x in sverilog_reserved
  tr = SVStructuralTranslatorL2( m )
  tr.clear( m )
  tr.translate_structural( m )

  ports = tr.structural.decl_ports[m]
  wires = tr.structural.decl_wires[m]
  structs = tr.structural.decl_type_struct
  conns = tr.structural.connections[m]

  check_eq( ports, case.REF_PORT )
  check_eq( wires, case.REF_WIRE )
  check_eq( conns, case.REF_CONN )
  assert structs[-1][0] == case.REF_STRUCT[0]
  check_eq( structs[-1][1]['def'], case.REF_STRUCT[1] )

@pytest.mark.parametrize(
  'case', [
    CaseConnectConstStructAttrToOutComp,
    CaseConnectLiteralStructComp,
    CaseConnectArrayStructAttrToOutComp,
    CaseConnectNestedStructPackedArrayComp,
  ]
)
def test_sverilog_structural_L2( case ):
  run_test( case, case.DUT() )
