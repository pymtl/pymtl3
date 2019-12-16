#=========================================================================
# BehavioralTranslatorL5_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Test the level 5 ehavioral translator."""

import pytest

from ...testcases import CaseSubCompFreeVarDrivenComp, CaseSubCompTmpDrivenComp
from ..BehavioralTranslatorL5 import BehavioralTranslatorL5
from .TestBehavioralTranslator import mk_TestBehavioralTranslator


@pytest.mark.parametrize(
  'case', [
    CaseSubCompTmpDrivenComp,
    CaseSubCompFreeVarDrivenComp,
  ]
)
def test_generic_behavioral_L5( case ):
  m = case.DUT()
  m.elaborate()
  tr = mk_TestBehavioralTranslator(BehavioralTranslatorL5)(m)
  tr.clear( m )
  tr.translate_behavioral( m )
  upblk_src = tr.behavioral.upblk_srcs[m.subcomp]
  decl_freevars = tr.behavioral.decl_freevars[m.subcomp]
  decl_tmpvars = tr.behavioral.decl_tmpvars[m.subcomp]
  assert upblk_src == case.REF_UPBLK
  assert decl_freevars == case.REF_FREEVAR
  assert decl_tmpvars == case.REF_TMPVAR
