#=========================================================================
# RTLIRTranslator_L2_cases_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 23, 2019
"""Test the RTLIR transaltor."""

import pytest

from ..behavioral.test.BehavioralTranslatorL2_test import *
from ..structural.test.StructuralTranslatorL2_test import *
from .TestRTLIRTranslator import TestRTLIRTranslator


def local_do_test( m ):
  if not m._dsl.constructed:
    m.elaborate()
  tr = TestRTLIRTranslator(m)
  tr.translate( m )
  src = tr.hierarchy.src
  try:
    assert src == m._ref_src
  except AttributeError:
    pass
