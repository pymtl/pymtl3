#=========================================================================
# VTranslator_L1_cases_test.py
#=========================================================================
"""Test the SystemVerilog translator."""

import pytest

from pymtl3.passes.backends.verilog.util.test_utility import check_eq
from pymtl3.passes.rtlir.util.test_utility import get_parameter

from ..behavioral.test.VBehavioralTranslatorL1_test import test_verilog_behavioral_L1
from ..structural.test.VStructuralTranslatorL1_test import test_verilog_structural_L1
from ..VTranslator import VTranslator


def run_test( case, m ):
  m.elaborate()
  tr = VTranslator( m )
  tr.translate( m )
  check_eq( tr.hierarchy.src, case.REF_SRC )

@pytest.mark.parametrize(
  'case', get_parameter('case', test_verilog_structural_L1) + \
          get_parameter('case', test_verilog_behavioral_L1)
)
def test_verilog_L1( case ):
  run_test( case, case.DUT() )
