#=========================================================================
# RTLIRTranslator_L4_cases_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 23, 2019
"""Test the RTLIR transaltor."""

import pytest

from pymtl3.passes.rtlir.util.test_utility import get_parameter

from .TestRTLIRTranslator import TestRTLIRTranslator
from ..behavioral.test.BehavioralTranslatorL4_test import \
    test_generic_behavioral_L4 as behavioral
from ..structural.test.StructuralTranslatorL4_test import \
    test_generic_structural_L4 as structural


def run_test( case, m ):
  if not m._dsl.constructed:
    m.elaborate()
  tr = TestRTLIRTranslator(m)
  tr.translate( m )
  src = tr.hierarchy.src
  assert src == case.REF_SRC

@pytest.mark.parametrize(
  'case', get_parameter('case', behavioral) + get_parameter('case', structural)
)
def test_generic_L4( case ):
  run_test( case, case.DUT() )
