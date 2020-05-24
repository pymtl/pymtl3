#=========================================================================
# RTLIRTranslator_L3_cases_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 23, 2019
"""Test the RTLIR translator."""

import pytest

from pymtl3.passes.rtlir.util.test_utility import get_parameter

from ..behavioral.test.BehavioralTranslatorL3_test import test_generic_behavioral_L3
from ..structural.test.StructuralTranslatorL3_test import test_generic_structural_L3
from .TestRTLIRTranslator import TestRTLIRTranslator


def run_test( case, m ):
  if not m._dsl.constructed:
    m.elaborate()
  tr = TestRTLIRTranslator(m)
  tr.translate( m )
  src = tr.hierarchy.src
  assert src == case.REF_SRC

@pytest.mark.parametrize(
  'case', get_parameter('case', test_generic_behavioral_L3) + \
          get_parameter('case', test_generic_structural_L3)
)
def test_generic_L3( case ):
  run_test( case, case.DUT() )
