#=========================================================================
# SVTranslator_L1_cases_test.py
#=========================================================================
"""Test the SystemVerilog translator."""

import pytest

from pymtl3.passes.backends.sverilog.util.test_utility import check_eq
from pymtl3.passes.rtlir.util.test_utility import get_parameter

from ..behavioral.test.SVBehavioralTranslatorL1_test import test_sverilog_behavioral_L1
from ..structural.test.SVStructuralTranslatorL1_test import test_sverilog_structural_L1
from ..SVTranslator import SVTranslator


def run_test( case, m ):
  m.elaborate()
  tr = SVTranslator( m )
  tr.translate( m )
  check_eq( tr.hierarchy.src, case.REF_SRC )

@pytest.mark.parametrize(
  'case', get_parameter('case', test_sverilog_structural_L1) + \
          get_parameter('case', test_sverilog_behavioral_L1)
)
def test_sverilog_L1( case ):
  run_test( case, case.DUT() )
