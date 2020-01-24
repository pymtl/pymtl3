#=========================================================================
# BehavioralTranslatorL1_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Test the level 1 behavioral translator."""

import pytest

from ...testcases import (
    CaseBits32ArrayClosureConstruct,
    CaseBits32ClosureConstruct,
    CaseTwoUpblksFreevarsComp,
    CaseTwoUpblksSliceComp,
)
from ..BehavioralTranslatorL1 import BehavioralTranslatorL1
from .TestBehavioralTranslator import mk_TestBehavioralTranslator


@pytest.mark.parametrize(
  'case', [
    CaseBits32ClosureConstruct,
    CaseBits32ArrayClosureConstruct,
    CaseTwoUpblksSliceComp,
    CaseTwoUpblksFreevarsComp,
  ]
)
def test_generic_behavioral_L1( case ):
  m = case.DUT()
  m.elaborate()
  tr = mk_TestBehavioralTranslator(BehavioralTranslatorL1)(m)
  tr.clear( m )
  tr.translate_behavioral( m )
  upblk_src = tr.behavioral.upblk_srcs[m]
  decl_freevars = tr.behavioral.decl_freevars[m]
  assert upblk_src == case.REF_UPBLK
  assert decl_freevars == case.REF_FREEVAR
