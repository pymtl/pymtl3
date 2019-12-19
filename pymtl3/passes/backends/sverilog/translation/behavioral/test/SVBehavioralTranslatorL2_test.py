#=========================================================================
# SVBehavioralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 28, 2019
"""Test the SystemVerilog translator implementation."""

import pytest

from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl3.passes.backends.sverilog.util.utility import sverilog_reserved

from ..SVBehavioralTranslatorL2 import BehavioralRTLIRToSVVisitorL2
from ....testcases import \
      CaseReducesInx3OutComp, CaseIfBasicComp, CaseIfDanglingElseInnerComp, \
      CaseIfDanglingElseOutterComp, CaseElifBranchComp, CaseNestedIfComp, \
      CaseForRangeLowerUpperStepPassThroughComp, CaseIfExpInForStmtComp, \
      CaseIfBoolOpInForStmtComp, CaseIfTmpVarInForStmtComp, CaseFixedSizeSliceComp, \
      CaseIfExpUnaryOpInForStmtComp


def run_test( case, m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )

  visitor = BehavioralRTLIRToSVVisitorL2(lambda x: x in sverilog_reserved)
  upblks = m._pass_behavioral_rtlir_gen.rtlir_upblks
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
      CaseForRangeLowerUpperStepPassThroughComp,
      CaseIfExpInForStmtComp,
      CaseIfBoolOpInForStmtComp,
      CaseIfTmpVarInForStmtComp,
      CaseFixedSizeSliceComp
    ]
)
def test_sv_behavioral_L2( case ):
  run_test( case, case.DUT() )
