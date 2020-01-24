#=========================================================================
# SVStructuralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 3 SystemVerilog structural translator."""

import pytest

from pymtl3.passes.backends.sverilog.util.test_utility import check_eq
from pymtl3.passes.backends.sverilog.util.utility import sverilog_reserved

from ....testcases import (
    CaseConnectArrayBits32FooIfcComp,
    CaseConnectArrayNestedIfcComp,
    CaseConnectValRdyIfcComp,
)
from ..SVStructuralTranslatorL3 import SVStructuralTranslatorL3


def run_test( case, m ):
  m.elaborate()
  SVStructuralTranslatorL3.is_sverilog_reserved = lambda s, x: x in sverilog_reserved
  tr = SVStructuralTranslatorL3( m )
  tr.clear( m )
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
def test_sverilog_structural_L3( case ):
  run_test( case, case.DUT() )
