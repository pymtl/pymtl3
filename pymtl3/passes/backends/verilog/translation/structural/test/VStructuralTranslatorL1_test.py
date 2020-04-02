#=========================================================================
# VStructuralTranslatorL1_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 1 SystemVerilog structural translator."""

from collections import deque

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
from ..VStructuralTranslatorL1 import VStructuralTranslatorL1


def run_test( case, m ):
  m.elaborate()
  VStructuralTranslatorL1.is_verilog_reserved = lambda s, x: x in verilog_reserved
  tr = VStructuralTranslatorL1( m )
  tr.clear( m )
  tr._rtlir_tr_unpacked_q = deque()
  tr.translate_structural( m )

  ports = tr.structural.decl_ports[m]
  wires = tr.structural.decl_wires[m]
  consts = tr.structural.decl_consts[m]
  conns = tr.structural.connections[m]

  check_eq( ports,  case.REF_PORT  )
  check_eq( wires,  case.REF_WIRE  )
  check_eq( consts, case.REF_CONST )
  check_eq( conns,  case.REF_CONN  )

  try:
    placeholder_wrapper = tr.structural.placeholder_wrapper[m]
    check_eq( placeholder_wrapper, case.REF_PLACEHOLDER_WRAPPER )

    placeholder_dependency = tr.structural.placeholder_dependency[m]
    check_eq( placeholder_dependency, case.REF_PLACEHOLDER_DEPENDENCY )
  except AttributeError:
    pass

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
def test_verilog_structural_L1( case ):
  run_test( case, case.DUT() )
