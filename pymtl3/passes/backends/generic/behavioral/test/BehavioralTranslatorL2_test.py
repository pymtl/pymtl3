#=========================================================================
# BehavioralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Test the level 2 behavioral translator."""

import pytest

from ...testcases import (
    CaseBits32ConstBitsToTmpVarComp,
    CaseBits32ConstIntToTmpVarComp,
    CaseBits32FreeVarToTmpVarComp,
    CaseBits32MultiTmpWireComp,
    CaseBits32TmpWireAliasComp,
    CaseBits32TmpWireComp,
)
from ..BehavioralTranslatorL2 import BehavioralTranslatorL2
from .TestBehavioralTranslator import mk_TestBehavioralTranslator


@pytest.mark.parametrize(
  'case', [
    CaseBits32TmpWireComp,
    CaseBits32TmpWireAliasComp,
    CaseBits32MultiTmpWireComp,
    CaseBits32FreeVarToTmpVarComp,
    CaseBits32ConstBitsToTmpVarComp,
    CaseBits32ConstIntToTmpVarComp,
  ]
)
def test_generic_behavioral_L2( case ):
  m = case.DUT()
  m.elaborate()
  tr = mk_TestBehavioralTranslator(BehavioralTranslatorL2)(m)
  tr.clear( m )
  tr.translate_behavioral( m )
  upblk_src = tr.behavioral.upblk_srcs[m]
  decl_freevars = tr.behavioral.decl_freevars[m]
  decl_tmpvars = tr.behavioral.decl_tmpvars[m]
  assert upblk_src == case.REF_UPBLK
  assert decl_freevars == case.REF_FREEVAR
  assert decl_tmpvars == case.REF_TMPVAR
