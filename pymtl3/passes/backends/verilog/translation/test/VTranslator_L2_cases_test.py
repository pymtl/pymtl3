#=========================================================================
# VTranslator_L2_cases_test.py
#=========================================================================
"""Test the SystemVerilog translator."""

import pytest

from pymtl3.passes.backends.verilog.errors import VerilogStructuralTranslationError
from pymtl3.passes.backends.verilog.util.test_utility import check_eq
from pymtl3.passes.rtlir.util.test_utility import expected_failure, get_parameter
from pymtl3.passes.testcases import CaseTypeNameAsFieldNameComp

from ...testcases import (
    CaseConnectPassThroughLongNameComp,
    ThisIsABitStructWithSuperLongName,
)
from ..behavioral.test.VBehavioralTranslatorL2_test import test_verilog_behavioral_L2
from ..behavioral.test.VBehavioralTranslatorL3_test import test_verilog_behavioral_L3
from ..structural.test.VStructuralTranslatorL2_test import test_verilog_structural_L2
from ..VTranslator import VTranslator


def run_test( case, m ):
  m.elaborate()
  tr = VTranslator( m )
  tr.translate( m )
  check_eq( tr.hierarchy.src, case.REF_SRC )

@pytest.mark.parametrize(
  'case', get_parameter('case', test_verilog_behavioral_L2) + \
          get_parameter('case', test_verilog_behavioral_L3) + \
          get_parameter('case', test_verilog_structural_L2)
)
def test_verilog_L2( case ):
  run_test( case, case.DUT() )

def test_long_component_name():
  args = [ThisIsABitStructWithSuperLongName]*7
  run_test( CaseConnectPassThroughLongNameComp, CaseConnectPassThroughLongNameComp.DUT(*args) )

def test_type_name_as_field_name():
  with expected_failure( VerilogStructuralTranslationError, 'same name as BitStruct type' ):
    run_test( CaseTypeNameAsFieldNameComp, CaseTypeNameAsFieldNameComp.DUT() )

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
  a.YOSYS_REF_SRC = \
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
