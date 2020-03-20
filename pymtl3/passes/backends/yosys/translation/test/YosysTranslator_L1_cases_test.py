#=========================================================================
# YosysTranslator_L1_cases_test.py
#=========================================================================
"""Test the yosys-SystemVerilog translator."""

import pytest

from pymtl3.passes.backends.verilog.util.test_utility import check_eq
from pymtl3.passes.rtlir.util.test_utility import get_parameter

from ..behavioral.test.YosysBehavioralTranslatorL1_test import test_yosys_behavioral_L1
from ..structural.test.YosysStructuralTranslatorL1_test import test_yosys_structural_L1
from ..YosysTranslator import YosysTranslator


def run_test( case, m ):
  m.elaborate()
  tr = YosysTranslator( m )
  tr.translate( m )
  check_eq( tr.hierarchy.src, case.REF_SRC )

@pytest.mark.parametrize(
  'case', get_parameter('case', test_yosys_behavioral_L1) + \
          get_parameter('case', test_yosys_structural_L1)
)
def test_yosys_L1( case ):
  run_test( case, case.DUT() )
