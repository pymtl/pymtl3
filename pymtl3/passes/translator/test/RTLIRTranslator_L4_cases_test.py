#=========================================================================
# RTLIRTranslator_L4_cases_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 23, 2019
"""Test the RTLIR transaltor."""
from __future__ import absolute_import, division, print_function

from pymtl.passes.rtlir.test.test_utility import do_test

from ..behavioral.test.BehavioralTranslatorL4_test import *
from ..structural.test.StructuralTranslatorL4_test import *
from .TestRTLIRTranslator import TestRTLIRTranslator


def local_do_test( m ):
  if not m._dsl.constructed:
    m.elaborate()
  tr = TestRTLIRTranslator(m)
  tr.translate()
  src = tr.hierarchy.src
  try:
    assert src == m._ref_src
  except AttributeError:
    pass
