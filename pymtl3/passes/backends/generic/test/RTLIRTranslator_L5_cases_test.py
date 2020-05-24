#=========================================================================
# RTLIRTranslator_L5_cases_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 23, 2019
"""Test the RTLIR translator."""

import pytest

from pymtl3.passes.rtlir.util.test_utility import get_parameter

from ..behavioral.test.BehavioralTranslatorL5_test import test_generic_behavioral_L5
from .TestRTLIRTranslator import TestRTLIRTranslator


def run_test( case, m ):
  if not m._dsl.constructed:
    m.elaborate()
  tr = TestRTLIRTranslator(m)
  tr.translate( m )
  src = tr.hierarchy.src
  assert src == case.REF_SRC

@pytest.mark.parametrize(
  'case', get_parameter('case', test_generic_behavioral_L5)
)
def test_generic_L5( case ):
  run_test( case, case.DUT() )
