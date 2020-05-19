#=========================================================================
# VBehavioralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 28, 2019
"""Test the SystemVerilog translator implementation."""

import pytest

from pymtl3.passes.backends.verilog.util.utility import verilog_reserved
from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass

from ....testcases import (
    CaseBits32FooInBits32OutComp,
    CaseBits32FooNoArgBehavioralComp,
    CaseBits32FooToBits32Comp,
    CaseBits32ToBits32FooComp,
    CaseConstStructInstComp,
    CaseIntToBits32FooComp,
    CaseNestedStructPackedArrayUpblkComp,
    CaseSizeCastPaddingStructPort,
    CaseStructPackedArrayUpblkComp,
    CaseStructUnique,
    CaseTypeBundle,
)
from ..VBehavioralTranslatorL3 import BehavioralRTLIRToVVisitorL3


def run_test( case, m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass( m ) )
  m.apply( BehavioralRTLIRTypeCheckPass( m ) )

  visitor = BehavioralRTLIRToVVisitorL3(lambda x: x in verilog_reserved)
  upblks = m.get_metadata( BehavioralRTLIRGenPass.rtlir_upblks )
  m_all_upblks = m.get_update_blocks()
  assert len(m_all_upblks) == 1

  for blk in m_all_upblks:
    upblk_src = visitor.enter( blk, upblks[blk] )
    upblk_src = "\n".join( upblk_src )
    assert upblk_src + '\n' == case.REF_UPBLK

@pytest.mark.parametrize(
    'case', [
      CaseBits32FooInBits32OutComp,
      CaseConstStructInstComp,
      CaseStructPackedArrayUpblkComp,
      CaseNestedStructPackedArrayUpblkComp,
      CaseSizeCastPaddingStructPort,
      CaseTypeBundle,
      CaseBits32FooToBits32Comp,
      CaseBits32ToBits32FooComp,
      CaseIntToBits32FooComp,
      CaseBits32FooNoArgBehavioralComp,
    CaseStructUnique,
    ]
)
def test_verilog_behavioral_L3( case ):
  run_test( case, case.DUT() )
