#=========================================================================
# YosysTranslator_L3_cases_test.py
#=========================================================================
"""Test the yosys-SystemVerilog translator."""

import pytest

from pymtl3.passes.backends.verilog.util.test_utility import check_eq
from pymtl3.passes.rtlir.util.test_utility import get_parameter

from ..behavioral.test.YosysBehavioralTranslatorL4_test import test_yosys_behavioral_L4
from ..structural.test.YosysStructuralTranslatorL3_test import test_yosys_structural_L3
from ..YosysTranslator import YosysTranslator


def run_test( case, m ):
  m.elaborate()
  tr = YosysTranslator( m )
  tr.translate( m )
  check_eq( tr.hierarchy.src, case.REF_SRC )

@pytest.mark.parametrize(
  'case', get_parameter('case', test_yosys_behavioral_L4) + \
          get_parameter('case', test_yosys_structural_L3)
)
def test_yosys_L3( case ):
  run_test( case, case.DUT() )
