#=========================================================================
# SVTranslator_L5_cases_test.py
#=========================================================================
"""Test the SystemVerilog translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits32, Bits64, concat, sext, zext
from pymtl3.dsl import Component, InPort, OutPort
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.SVTranslator import SVTranslator


def local_do_test( m ):
  m.elaborate()
  tr = SVTranslator( m )
  tr.translate()
  assert tr.hierarchy.src == m._ref_src

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
"""\
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

  B b (
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
"""\
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

  B b (
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
  do_test( a )

def test_subcomponent_index( do_test ):
  class B( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.comp = [ B() for _ in xrange(2) ]
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.comp[1].out
  a = A()
  a._ref_src = \
"""\
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
  logic [0:0] comp_$0$clk;
  logic [31:0] comp_$0$out;
  logic [0:0] comp_$0$reset;

  B comp_$0 (
    .clk( comp_$0$clk ),
    .out( comp_$0$out ),
    .reset( comp_$0$reset )
  );

  logic [0:0] comp_$1$clk;
  logic [31:0] comp_$1$out;
  logic [0:0] comp_$1$reset;

  B comp_$1 (
    .clk( comp_$1$clk ),
    .out( comp_$1$out ),
    .reset( comp_$1$reset )
  );

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out = s.comp[1].out
  
  always_comb begin : upblk
    out = comp_$1$out;
  end

  assign comp_$1$clk = clk;
  assign comp_$1$reset = reset;
  assign comp_$0$clk = clk;
  assign comp_$0$reset = reset;

endmodule
"""
  do_test( a )
