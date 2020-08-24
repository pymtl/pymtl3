#=========================================================================
# VBehavioralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 28, 2019
"""Test the SystemVerilog translator implementation."""

import pytest

from pymtl3 import *
from pymtl3.passes.backends.verilog.util.utility import verilog_reserved
from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass

from ....testcases import (
    CaseBoolTmpVarComp,
    CaseElifBranchComp,
    CaseFixedSizeSliceComp,
    CaseForLoopEmptySequenceComp,
    CaseForRangeLowerUpperStepPassThroughComp,
    CaseIfBasicComp,
    CaseIfBoolOpInForStmtComp,
    CaseIfDanglingElseInnerComp,
    CaseIfDanglingElseOutterComp,
    CaseIfExpBothImplicitComp,
    CaseIfExpInForStmtComp,
    CaseIfExpUnaryOpInForStmtComp,
    CaseIfTmpVarInForStmtComp,
    CaseLambdaConnectComp,
    CaseLambdaConnectWithListComp,
    CaseNestedIfComp,
    CaseReducesInx3OutComp,
    CaseTmpVarInUpdateffComp,
)
from ..VBehavioralTranslatorL2 import BehavioralRTLIRToVVisitorL2


def run_test( case, m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass( m ) )
  m.apply( BehavioralRTLIRTypeCheckPass( m ) )

  visitor = BehavioralRTLIRToVVisitorL2(lambda x: x in verilog_reserved)
  upblks = m.get_metadata( BehavioralRTLIRGenPass.rtlir_upblks )
  m_all_upblks = m.get_update_blocks()
  assert len(m_all_upblks) == 1

  for blk in m_all_upblks:
    upblk_src = visitor.enter( blk, upblks[blk] )
    upblk_src = "\n".join( upblk_src )
    assert upblk_src + '\n' == case.REF_UPBLK

@pytest.mark.parametrize(
    'case', [
      CaseReducesInx3OutComp,
      CaseIfBasicComp,
      CaseIfDanglingElseInnerComp,
      CaseIfDanglingElseOutterComp,
      CaseElifBranchComp,
      CaseNestedIfComp,
      CaseForLoopEmptySequenceComp,
      CaseForRangeLowerUpperStepPassThroughComp,
      CaseIfExpInForStmtComp,
      CaseIfExpBothImplicitComp,
      CaseIfBoolOpInForStmtComp,
      CaseIfTmpVarInForStmtComp,
      CaseFixedSizeSliceComp,
      CaseLambdaConnectComp,
      CaseLambdaConnectWithListComp,
      CaseBoolTmpVarComp,
      CaseTmpVarInUpdateffComp,
    ]
)
def test_verilog_behavioral_L2( case ):
  run_test( case, case.DUT() )
