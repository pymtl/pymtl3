#=========================================================================
# SVBehavioralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 28, 2019
"""Test the SystemVerilog translator implementation."""

import pytest

from pymtl3.passes.backends.sverilog.util.utility import sverilog_reserved
from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass

from ....testcases import (
    CaseElifBranchComp,
    CaseFixedSizeSliceComp,
    CaseForRangeLowerUpperStepPassThroughComp,
    CaseIfBasicComp,
    CaseIfBoolOpInForStmtComp,
    CaseIfDanglingElseInnerComp,
    CaseIfDanglingElseOutterComp,
    CaseIfExpInForStmtComp,
    CaseIfExpUnaryOpInForStmtComp,
    CaseIfTmpVarInForStmtComp,
    CaseLambdaConnectComp,
    CaseLambdaConnectWithListComp,
    CaseNestedIfComp,
    CaseReducesInx3OutComp,
)
from ..SVBehavioralTranslatorL2 import BehavioralRTLIRToSVVisitorL2


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
      CaseFixedSizeSliceComp,
      CaseLambdaConnectComp,
      CaseLambdaConnectWithListComp,
    ]
)
def test_sverilog_behavioral_L2( case ):
  run_test( case, case.DUT() )

@pytest.mark.xfail(run=False, reason="TODO: resolving BitStructs according to name AND fields")
def test_struct_uniqueness():
  class A:
    @bitstruct
    class ST:
      a_foo: Bits16
      a_bar: Bits32

  class B:
    @bitstruct
    class ST:
      b_foo: Bits16
      b_bar: Bits32

  @bitstruct
  class COMB:
    fst: A.ST
    snd: B.ST

  class Top( Component ):
    def construct( s ):
      s.out = OutPort( COMB )
      connect( s.out, COMB(A.ST(1, 2), B.ST(3, 4)) )
  a = Top()
  a.REF_SRC = \
"""
typedef struct packed {
  logic [15:0] foo;
  logic [31:0] bar;
} ST;

typedef struct packed {
  ST fst;
  ST snd;
} COMB;

module Top
(
  input logic [0:0] clk,
  output COMB out,
  input logic [0:0] reset
);

  assign out = { { 16'd1, 32'd2 }, { 16'd3, 32'd4 } };

endmodule
"""
  run_test( a, Top() )
