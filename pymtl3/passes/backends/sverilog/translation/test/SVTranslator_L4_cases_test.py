#=========================================================================
# SVTranslator_L4_cases_test.py
#=========================================================================
"""Test the SystemVerilog translator."""

import pytest

from pymtl3.passes.backends.sverilog.util.test_utility import check_eq
from pymtl3.passes.rtlir.util.test_utility import get_parameter

from ..behavioral.test.SVBehavioralTranslatorL5_test import (
    test_sverilog_behavioral_L5 as behavioral,
)
from ..structural.test.SVStructuralTranslatorL4_test import (
    test_sverilog_structural_L4 as structural,
)
from ..SVTranslator import SVTranslator


def run_test( case, m ):
  m.elaborate()
  tr = SVTranslator( m )
  tr.translate( m )
  check_eq( tr.hierarchy.src, case.REF_SRC )

@pytest.mark.parametrize(
  'case', get_parameter('case', behavioral) + get_parameter('case', structural)
)
def test_sverilog_L4( case ):
  run_test( case, case.DUT() )
