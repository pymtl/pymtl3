#=========================================================================
# SVTranslator_L4_cases_test.py
#=========================================================================
"""Test the SystemVerilog translator."""

from pymtl3.datatypes import Bits32, Bits64, concat, sext, zext
from pymtl3.dsl import Component, InPort, OutPort, connect
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.structural.test.SVStructuralTranslatorL1_test import (
    check_eq,
)
from pymtl3.passes.sverilog.translation.SVTranslator import SVTranslator


def local_do_test( m ):
  m.elaborate()
  tr = SVTranslator( m )
  tr.translate( m )
  check_eq( tr.hierarchy.src, m._ref_src )

def test_subcomponent( do_test ):
  class B( Component ):
    def construct( s ):
      s.foo = OutPort( Bits32 )
      @s.update
      def upblk():
        s.foo = Bits32(42)
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      s.b = B()
      @s.update
      def upblk():
        s.out = s.b.foo
  a = A()
  a._ref_src = \
"""
module B
(
  input logic [0:0] clk,
  output logic [31:0] foo,
  input logic [0:0] reset
);

  // @s.update
  // def upblk():
  //   s.foo = Bits32(42)

  always_comb begin : upblk
    foo = 32'd42;
  end

endmodule


module A
(
  input logic [0:0] clk,
  output logic [31:0] out,
  input logic [0:0] reset
);
  logic [0:0] b__clk;
  logic [31:0] b__foo;
  logic [0:0] b__reset;

  B b
  (
    .clk( b__clk ),
    .foo( b__foo ),
    .reset( b__reset )
  );

  // @s.update
  // def upblk():
  //   s.out = s.b.foo

  always_comb begin : upblk
    out = b__foo;
  end

  assign b__clk = clk;
  assign b__reset = reset;

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

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
"""
module B
(
  input logic [0:0] clk,
  output logic [31:0] out_b,
  input logic [0:0] reset
);

  // @s.update
  // def upblk():
  //   s.out_b = Bits32(0)

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
  logic [0:0] b__clk;
  logic [31:0] b__out_b;
  logic [0:0] b__reset;

  B b
  (
    .clk( b__clk ),
    .out_b( b__out_b ),
    .reset( b__reset )
  );

  // @s.update
  // def upblk():
  //   s.out = zext( s.b.out_b, 64 )

  always_comb begin : upblk
    out = { { 32 { 1'b0 } }, b__out_b };
  end

  assign b__clk = clk;
  assign b__reset = reset;

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_subcomponent_index( do_test ):
  class B( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.comp = [ B() for _ in range(2) ]
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.comp[1].out
  a = A()
  a._ref_src = \
"""
module B
(
  input logic [0:0] clk,
  output logic [31:0] out,
  input logic [0:0] reset
);

endmodule


module A
(
  input logic [0:0] clk,
  output logic [31:0] out,
  input logic [0:0] reset
);
  logic [0:0] comp__0__clk;
  logic [31:0] comp__0__out;
  logic [0:0] comp__0__reset;

  B comp__0
  (
    .clk( comp__0__clk ),
    .out( comp__0__out ),
    .reset( comp__0__reset )
  );

  logic [0:0] comp__1__clk;
  logic [31:0] comp__1__out;
  logic [0:0] comp__1__reset;

  B comp__1
  (
    .clk( comp__1__clk ),
    .out( comp__1__out ),
    .reset( comp__1__reset )
  );

  // @s.update
  // def upblk():
  //   s.out = s.comp[1].out

  always_comb begin : upblk
    out = comp__1__out;
  end

  assign comp__0__clk = clk;
  assign comp__0__reset = reset;
  assign comp__1__clk = clk;
  assign comp__1__reset = reset;

endmodule
"""
  a._ref_src_yosys = \
"""
module B
(
  input logic [0:0] clk,
  output logic [31:0] out,
  input logic [0:0] reset
);

endmodule


module A
(
  input logic [0:0] clk,
  output logic [31:0] out,
  input logic [0:0] reset
);
  logic [0:0] comp__clk [0:1];
  logic [31:0] comp__out [0:1];
  logic [0:0] comp__reset [0:1];
  logic [0:0] comp__0__clk;
  logic [31:0] comp__0__out;
  logic [0:0] comp__0__reset;

  B comp__0
  (
    .clk( comp__0__clk ),
    .out( comp__0__out ),
    .reset( comp__0__reset )
  );

  logic [0:0] comp__1__clk;
  logic [31:0] comp__1__out;
  logic [0:0] comp__1__reset;

  B comp__1
  (
    .clk( comp__1__clk ),
    .out( comp__1__out ),
    .reset( comp__1__reset )
  );
  assign comp__0__clk = comp__clk[0];
  assign comp__1__clk = comp__clk[1];
  assign comp__out[0] = comp__0__out;
  assign comp__out[1] = comp__1__out;
  assign comp__0__reset = comp__reset[0];
  assign comp__1__reset = comp__reset[1];

  // @s.update
  // def upblk():
  //   s.out = s.comp[1].out

  always_comb begin : upblk
    out = comp__out[1];
  end

  assign comp__clk[0] = clk;
  assign comp__reset[0] = reset;
  assign comp__clk[1] = clk;
  assign comp__reset[1] = reset;

endmodule
"""
  do_test( a )
