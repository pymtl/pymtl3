#=========================================================================
# SVTranslator_L4_cases_test.py
#=========================================================================
"""Test the SystemVerilog translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits32, Bits64, concat, sext, zext
from pymtl3.dsl import Component, InPort, OutPort
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.SVTranslator import SVTranslator

from .SVTranslator_L1_cases_test import trim


def local_do_test( m ):
  m.elaborate()
  tr = SVTranslator( m )
  tr.translate( m )
  assert trim( tr.hierarchy.src ) == m._ref_src

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

  // PYMTL SOURCE:
  // 
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
  logic [0:0] b$clk;
  logic [31:0] b$foo;
  logic [0:0] b$reset;

  B b
  (
    .clk( b$clk ),
    .foo( b$foo ),
    .reset( b$reset )
  );

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out = s.b.foo
  
  always_comb begin : upblk
    out = b$foo;
  end

  assign b$clk = clk;
  assign b$reset = reset;

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

  // PYMTL SOURCE:
  // 
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
  logic [0:0] b$clk;
  logic [31:0] b$out_b;
  logic [0:0] b$reset;

  B b
  (
    .clk( b$clk ),
    .out_b( b$out_b ),
    .reset( b$reset )
  );

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out = zext( s.b.out_b, 64 )
  
  always_comb begin : upblk
    out = { { 32 { 1'b0 } }, b$out_b };
  end

  assign b$clk = clk;
  assign b$reset = reset;

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
  logic [0:0] comp$__0$clk;
  logic [31:0] comp$__0$out;
  logic [0:0] comp$__0$reset;

  B comp$__0
  (
    .clk( comp$__0$clk ),
    .out( comp$__0$out ),
    .reset( comp$__0$reset )
  );

  logic [0:0] comp$__1$clk;
  logic [31:0] comp$__1$out;
  logic [0:0] comp$__1$reset;

  B comp$__1
  (
    .clk( comp$__1$clk ),
    .out( comp$__1$out ),
    .reset( comp$__1$reset )
  );

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out = s.comp[1].out
  
  always_comb begin : upblk
    out = comp$__1$out;
  end

  assign comp$__1$clk = clk;
  assign comp$__1$reset = reset;
  assign comp$__0$clk = clk;
  assign comp$__0$reset = reset;

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
  logic [0:0] comp$clk [0:1];
  logic [31:0] comp$out [0:1];
  logic [0:0] comp$reset [0:1];
  logic [0:0] comp$__0$clk;
  logic [31:0] comp$__0$out;
  logic [0:0] comp$__0$reset;

  B comp$__0
  (
    .clk( comp$__0$clk ),
    .out( comp$__0$out ),
    .reset( comp$__0$reset )
  );

  logic [0:0] comp$__1$clk;
  logic [31:0] comp$__1$out;
  logic [0:0] comp$__1$reset;

  B comp$__1
  (
    .clk( comp$__1$clk ),
    .out( comp$__1$out ),
    .reset( comp$__1$reset )
  );
  assign comp$__0$clk = comp$clk[0];
  assign comp$__1$clk = comp$clk[1];
  assign comp$out[0] = comp$__0$out;
  assign comp$out[1] = comp$__1$out;
  assign comp$__0$reset = comp$reset[0];
  assign comp$__1$reset = comp$reset[1];

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out = s.comp[1].out
  
  always_comb begin : upblk
    out = comp$out[1];
  end

  assign comp$clk[1] = clk;
  assign comp$reset[1] = reset;
  assign comp$clk[0] = clk;
  assign comp$reset[0] = reset;

endmodule
"""
  do_test( a )
