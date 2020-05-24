#=========================================================================
# BehavioralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Test the level 3 behavioral translator."""

import pytest

from ...testcases import CaseStructTmpWireComp, CaseTwoUpblksStructTmpWireComp
from ..BehavioralTranslatorL3 import BehavioralTranslatorL3
from .TestBehavioralTranslator import mk_TestBehavioralTranslator


@pytest.mark.parametrize(
  'case', [
    CaseStructTmpWireComp,
    CaseTwoUpblksStructTmpWireComp,
  ]
)
def test_generic_behavioral_L3( case ):
  m = case.DUT()
  m.elaborate()
  tr = mk_TestBehavioralTranslator(BehavioralTranslatorL3)(m)
  tr.clear( m )
  tr.translate_behavioral( m )
  upblk_src = tr.behavioral.upblk_srcs[m]
  decl_freevars = tr.behavioral.decl_freevars[m]
  decl_tmpvars = tr.behavioral.decl_tmpvars[m]
  assert upblk_src == case.REF_UPBLK
  assert decl_freevars == case.REF_FREEVAR
  assert decl_tmpvars == case.REF_TMPVAR
