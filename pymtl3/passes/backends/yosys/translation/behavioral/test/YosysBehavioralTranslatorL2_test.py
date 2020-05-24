#=========================================================================
# YosysBehavioralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Test the YosysVerilog translator implementation."""

import pytest

from pymtl3.passes.backends.verilog.util.utility import verilog_reserved
from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass

from ....testcases import (
    CaseElifBranchComp,
    CaseFixedSizeSliceComp,
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
)
from ..YosysBehavioralTranslatorL2 import YosysBehavioralRTLIRToVVisitorL2


def run_test( case, m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass( m ) )
  m.apply( BehavioralRTLIRTypeCheckPass( m ) )

  visitor = YosysBehavioralRTLIRToVVisitorL2(lambda x: x in verilog_reserved)
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
      CaseForRangeLowerUpperStepPassThroughComp,
      CaseIfExpInForStmtComp,
      CaseIfExpBothImplicitComp,
      CaseIfBoolOpInForStmtComp,
      CaseIfTmpVarInForStmtComp,
      CaseFixedSizeSliceComp,
      CaseLambdaConnectComp,
      CaseLambdaConnectWithListComp,
    ]
)
def test_yosys_behavioral_L2( case ):
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
module Top
(
  input logic [0:0] clk,
  output logic [15:0] out__fst__foo,
  output logic [31:0] out__fst__bar,
  output logic [15:0] out__snd__foo,
  output logic [31:0] out__snd__bar,
  input logic [0:0] reset
);
  logic [47:0]  out__fst;
  logic [47:0]  out__snd;
  logic [95:0]  out;

  assign out__fst__foo = out__fst[47:32];
  assign out__fst__bar = out__fst[31:0];
  assign out__snd__foo = out__snd[47:32];
  assign out__snd__bar = out__snd[31:0];
  assign out__fst__foo = out[95:80];
  assign out__fst__bar = out[79:48];
  assign out__snd__foo = out[47:32];
  assign out__snd__bar = out[31:0];
  assign out = { { 16'd1, 32'd2 }, { 16'd3, 32'd4 } };

endmodule
"""
  run_test( a, Top() )
