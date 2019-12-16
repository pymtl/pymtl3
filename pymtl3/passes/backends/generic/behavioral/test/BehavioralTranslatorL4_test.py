#=========================================================================
# BehavioralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Test the level 4 behavioral translator."""

import pytest

from ...testcases import CaseBits32IfcTmpVarOutComp, CaseStructIfcTmpVarOutComp
from ..BehavioralTranslatorL4 import BehavioralTranslatorL4
from .TestBehavioralTranslator import mk_TestBehavioralTranslator


@pytest.mark.parametrize(
  'case', [
    CaseBits32IfcTmpVarOutComp,
    CaseStructIfcTmpVarOutComp,
  ]
)
def test_generic_behavioral_L4( case ):
  m = case.DUT()
  m.elaborate()
  tr = mk_TestBehavioralTranslator(BehavioralTranslatorL4)(m)
  tr.clear( m )
  tr.translate_behavioral( m )
  upblk_src = tr.behavioral.upblk_srcs[m]
  decl_freevars = tr.behavioral.decl_freevars[m]
  decl_tmpvars = tr.behavioral.decl_tmpvars[m]
  assert upblk_src == case.REF_UPBLK
  assert decl_freevars == case.REF_FREEVAR
  assert decl_tmpvars == case.REF_TMPVAR
