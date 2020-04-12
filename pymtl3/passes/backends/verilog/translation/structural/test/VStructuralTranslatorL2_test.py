#=========================================================================
# VStructuralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 2 SystemVerilog structural translator."""

from collections import deque

import pytest

from pymtl3.passes.backends.verilog.util.test_utility import check_eq
from pymtl3.passes.backends.verilog.util.utility import verilog_reserved

from ....testcases import (
    CaseConnectArrayStructAttrToOutComp,
    CaseConnectConstStructAttrToOutComp,
    CaseConnectLiteralStructComp,
    CaseConnectNestedStructPackedArrayComp,
)
from ..VStructuralTranslatorL2 import VStructuralTranslatorL2


def run_test( case, m ):
  m.elaborate()
  VStructuralTranslatorL2.is_verilog_reserved = lambda s, x: x in verilog_reserved
  tr = VStructuralTranslatorL2( m )
  tr.clear( m )
  tr._rtlir_tr_unpacked_q = deque()
  tr.translate_structural( m )

  ports = tr.structural.decl_ports[m]
  wires = tr.structural.decl_wires[m]
  structs = tr.structural.decl_type_struct
  conns = tr.structural.connections[m]

  check_eq( ports, case.REF_PORT )
  check_eq( wires, case.REF_WIRE )
  check_eq( conns, case.REF_CONN )

  assert list(structs.keys())[-1] == case.REF_STRUCT[0]
  check_eq( list(structs.values())[-1]['def'], case.REF_STRUCT[1] )

@pytest.mark.parametrize(
  'case', [
    CaseConnectConstStructAttrToOutComp,
    CaseConnectLiteralStructComp,
    CaseConnectArrayStructAttrToOutComp,
    CaseConnectNestedStructPackedArrayComp,
  ]
)
def test_verilog_structural_L2( case ):
  run_test( case, case.DUT() )
