#=========================================================================
# VStructuralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 3 SystemVerilog structural translator."""

from collections import deque

import pytest

from pymtl3.passes.backends.verilog.util.test_utility import check_eq
from pymtl3.passes.backends.verilog.util.utility import verilog_reserved

from ....testcases import (
    CaseConnectArrayBits32FooIfcComp,
    CaseConnectArrayNestedIfcComp,
    CaseConnectValRdyIfcComp,
)
from ..VStructuralTranslatorL3 import VStructuralTranslatorL3


def run_test( case, m ):
  m.elaborate()
  VStructuralTranslatorL3.is_verilog_reserved = lambda s, x: x in verilog_reserved
  tr = VStructuralTranslatorL3( m )
  tr.clear( m )
  tr._rtlir_tr_unpacked_q = deque()
  tr.translate_structural( m )

  ifcs = tr.structural.decl_ifcs[m]
  conns = tr.structural.connections[m]

  check_eq( ifcs,  case.REF_IFC  )
  check_eq( conns, case.REF_CONN )

@pytest.mark.parametrize(
  'case', [
    CaseConnectValRdyIfcComp,
    CaseConnectArrayBits32FooIfcComp,
    CaseConnectArrayNestedIfcComp,
  ]
)
def test_verilog_structural_L3( case ):
  run_test( case, case.DUT() )
