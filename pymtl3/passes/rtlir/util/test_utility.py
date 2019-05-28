#=========================================================================
# test_utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 21, 2019
"""Test utilities used by RTLIR tests."""

from __future__ import absolute_import, division, print_function

from contextlib import contextmanager

import pytest

@pytest.fixture
def do_test( request ):
  """Call `local_do_test` of the requesting module."""
  return request.module.local_do_test

@contextmanager
def expected_failure( exception = Exception, msg = None ):
  """Mark one test case as should-fail.

  Not to be confused with pytest.xfail, which is commonly used to mark
  tests related to unimplemented functionality. This test only passes when
  it throws an expected exception.
  """
  try:
    yield
  except exception as e:
    if msg is None or e.args[0].find( msg ) != -1:
      return
    else:
      raise
  raise Exception( 'expected-to-fail test unexpectedly passed!' )

_rtlir_translators = {}

def gen_rtlir_translator( structural_level, behavioral_level ):
  """Return an RTLIR translators with given structural/behavioral level."""

  label = str( structural_level ) + str( behavioral_level )

  if label in _rtlir_translators: return _rtlir_translators[ label ]

  from pymtl3.passes.rtlir.behavioral import (
      MaxBehavioralRTLIRLevel,
      MinBehavioralRTLIRLevel,
  )
  from pymtl3.passes.rtlir.structural import (
      MaxStructuralRTLIRLevel,
      MinStructuralRTLIRLevel,
  )
  assert MinStructuralRTLIRLevel <= structural_level <= MaxStructuralRTLIRLevel
  assert MinBehavioralRTLIRLevel <= behavioral_level <= MaxBehavioralRTLIRLevel

  structural_tplt = \
    'from pymtl.passes.rtlir.translation.structural.StructuralTranslatorL{0} \
       import StructuralTranslatorL{0} as _StructuralTranslator'

  behavioral_tplt = \
    'from pymtl.passes.rtlir.translation.behavioral.BehavioralTranslatorL{0} \
       import BehavioralTranslatorL{0} as _BehavioralTranslator'

  exec(structural_tplt.format( structural_level ), globals(), locals())
  exec(behavioral_tplt.format( behavioral_level ), globals(), locals())

  from pymtl.passes.rtlir.translation.RTLIRTranslator import mk_RTLIRTranslator

  _rtlir_translators[ label ] = mk_RTLIRTranslator(
    _BehavioralTranslator, _StructuralTranslator
  )

  return _rtlir_translators[ label ]
