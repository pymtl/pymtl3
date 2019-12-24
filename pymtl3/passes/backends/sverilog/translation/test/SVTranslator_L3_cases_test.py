#=========================================================================
# SVTranslator_L3_cases_test.py
#=========================================================================
"""Test the SystemVerilog translator."""

import pytest

from pymtl3.passes.backends.sverilog.util.test_utility import check_eq
from pymtl3.passes.rtlir.util.test_utility import get_parameter

from ..behavioral.test.SVBehavioralTranslatorL4_test import test_sverilog_behavioral_L4
from ..structural.test.SVStructuralTranslatorL3_test import test_sverilog_structural_L3
from ..SVTranslator import SVTranslator


def run_test( case, m ):
  m.elaborate()
  tr = SVTranslator( m )
  tr.translate( m )
  check_eq( tr.hierarchy.src, case.REF_SRC )

@pytest.mark.parametrize(
  'case', get_parameter('case', test_sverilog_behavioral_L4) + \
          get_parameter('case', test_sverilog_structural_L3)
)
def test_sverilog_L3( case ):
  run_test( case, case.DUT() )
