#=========================================================================
# SVTranslator_L5_cases_test.py
#=========================================================================
"""Test the SystemVerilog translator."""

from __future__ import absolute_import, division, print_function

from pymtl import Bits32, Bits64, Component, InPort, OutPort, concat, sext, zext
from pymtl.passes.rtlir.test.test_utility import do_test
from pymtl.passes.sverilog.translation.SVTranslator import SVTranslator


def local_do_test( m ):
  m.elaborate()
  tr = SVTranslator( m )
  tr.translate()
  assert tr.hierarchy.src == m._ref_src

def test_sub_component_attr( do_test ):
  class B( Component ):
    def construct( s ):
      s.out_b = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out_b = Bits32(0)
  class A( Component ):
    def construct( s ):
      s.b = B()
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = zext( s.b.out_b, 64 )
  a = A()
  a._ref_src = \
"""\
module B
(
  input logic [0:0] clk,
  output logic [31:0] out_b,
  input logic [0:0] reset
);

  always_comb begin : upblk
    out_b = 32'd0;
  end

endmodule


module A
(
  input logic [0:0] clk,
  output logic [63:0] out,
  input logic [0:0] reset
);
  logic [0:0] b$clk;
  logic [31:0] b$out_b;
  logic [0:0] b$reset;

  B b (
    .clk( b$clk ),
    .out_b( b$out_b ),
    .reset( b$reset )
  );

  always_comb begin : upblk
    out = { { 32 { 1'b0 } }, b$out_b };
  end

  assign b$clk = clk;
  assign b$reset = reset;

endmodule
"""
  do_test( a )
