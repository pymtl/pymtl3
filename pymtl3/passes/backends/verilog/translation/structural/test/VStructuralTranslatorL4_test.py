#=========================================================================
# VStructuralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 4 SystemVerilog structural translator."""

from collections import deque

import pytest

from pymtl3.passes.backends.verilog import VerilogPlaceholderPass
from pymtl3.passes.backends.verilog.util.test_utility import check_eq
from pymtl3.passes.backends.verilog.util.utility import verilog_reserved

from ....testcases import (
    CaseBits32ArrayConnectSubCompAttrComp,
    CaseBits32ConnectSubCompAttrComp,
    CaseChildExplicitModuleName,
    CaseConnectArraySubCompArrayStructIfcComp,
    CaseHeteroCompArrayComp,
)
from ..VStructuralTranslatorL4 import VStructuralTranslatorL4


def run_test( case, m ):
  m.elaborate()
  VStructuralTranslatorL4.is_verilog_reserved = lambda s, x: x in verilog_reserved
  tr = VStructuralTranslatorL4( m )
  tr._placeholder_pass = VerilogPlaceholderPass
  tr.clear( m )
  tr._rtlir_tr_unpacked_q = deque()
  tr.translate_structural( m )
  subcomps = tr.structural.decl_subcomps

  check_eq( subcomps[m], case.REF_COMP )

@pytest.mark.parametrize(
  'case', [
    CaseBits32ConnectSubCompAttrComp,
    CaseConnectArraySubCompArrayStructIfcComp,
    CaseBits32ArrayConnectSubCompAttrComp,
    CaseHeteroCompArrayComp,
  ]
)
def test_verilog_structural_L4( case ):
  run_test( case, case.DUT() )

def test_verilog_structural_L4_child_explicit_module_name():
  run_test( CaseChildExplicitModuleName, CaseChildExplicitModuleName.DUT() )
