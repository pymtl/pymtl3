#=========================================================================
# SVTranslator_L1_cases_test.py
#=========================================================================
"""Test the SystemVerilog translator."""

from pymtl3.datatypes import Bits1, Bits4, Bits32, Bits64, concat, sext, zext
from pymtl3.dsl import Component, InPort, OutPort, Wire, connect
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

#-------------------------------------------------------------------------
# Behavioral
#-------------------------------------------------------------------------

def test_comb_assign( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [31:0] out,
  input logic [0:0] reset
);

  // @s.update
  // def upblk():
  //   s.out = s.in_

  always_comb begin : upblk
    out = in_;
  end

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_seq_assign( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update_ff
      def upblk():
        s.out <<= s.in_
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [31:0] out,
  input logic [0:0] reset
);

  // @s.update_ff
  // def upblk():
  //   s.out <<= s.in_

  always_ff @(posedge clk) begin : upblk
    out <= in_;
  end

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_concat( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = concat( s.in_1, s.in_2 )
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_1,
  input logic [31:0] in_2,
  output logic [63:0] out,
  input logic [0:0] reset
);

  // @s.update
  // def upblk():
  //   s.out = concat( s.in_1, s.in_2 )

  always_comb begin : upblk
    out = { in_1, in_2 };
  end

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_concat_constants( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = concat( Bits32(42), Bits32(0) )
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  output logic [63:0] out,
  input logic [0:0] reset
);

  // @s.update
  // def upblk():
  //   s.out = concat( Bits32(42), Bits32(0) )

  always_comb begin : upblk
    out = { 32'd42, 32'd0 };
  end

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_concat_mixed( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = concat( s.in_, Bits32(0) )
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [63:0] out,
  input logic [0:0] reset
);

  // @s.update
  // def upblk():
  //   s.out = concat( s.in_, Bits32(0) )

  always_comb begin : upblk
    out = { in_, 32'd0 };
  end

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_sext( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = sext( s.in_, 64 )
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [63:0] out,
  input logic [0:0] reset
);

  // @s.update
  // def upblk():
  //   s.out = sext( s.in_, 64 )

  always_comb begin : upblk
    out = { { 32 { in_[31] } }, in_ };
  end

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_zext( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = zext( s.in_, 64 )
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [63:0] out,
  input logic [0:0] reset
);

  // @s.update
  // def upblk():
  //   s.out = zext( s.in_, 64 )

  always_comb begin : upblk
    out = { { 32 { 1'b0 } }, in_ };
  end

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_freevar( do_test ):
  class A( Component ):
    def construct( s ):
      STATE_IDLE = Bits32(42)
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = concat( s.in_, STATE_IDLE )
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [63:0] out,
  input logic [0:0] reset
);
  localparam [31:0] __const__STATE_IDLE = 32'd42;

  // @s.update
  // def upblk():
  //   s.out = concat( s.in_, STATE_IDLE )

  always_comb begin : upblk
    out = { in_, __const__STATE_IDLE };
  end

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [63:0] out,
  input logic [0:0] reset
);

  // @s.update
  // def upblk():
  //   s.out = concat( s.in_, STATE_IDLE )

  always_comb begin : upblk
    out = { in_, 32'd42 };
  end

endmodule
"""
  do_test( a )

def test_unpacked_signal_index( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(2) ]
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = concat( s.in_[0], s.in_[1] )
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_ [0:1],
  output logic [63:0] out,
  input logic [0:0] reset
);

  // @s.update
  // def upblk():
  //   s.out = concat( s.in_[0], s.in_[1] )

  always_comb begin : upblk
    out = { in_[0], in_[1] };
  end

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in___0,
  input logic [31:0] in___1,
  output logic [63:0] out,
  input logic [0:0] reset
);
  logic [31:0] in_ [0:1];

  // @s.update
  // def upblk():
  //   s.out = concat( s.in_[0], s.in_[1] )

  always_comb begin : upblk
    out = { in_[0], in_[1] };
  end

  assign in_[0] = in___0;
  assign in_[1] = in___1;

endmodule
"""
  do_test( a )

def test_bit_selection( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = s.in_[1]
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [0:0] out,
  input logic [0:0] reset
);

  // @s.update
  // def upblk():
  //   s.out = s.in_[1]

  always_comb begin : upblk
    out = in_[1];
  end

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_part_selection( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits64 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_[4:36]
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [63:0] in_,
  output logic [31:0] out,
  input logic [0:0] reset
);

  // @s.update
  // def upblk():
  //   s.out = s.in_[4:36]

  always_comb begin : upblk
    out = in_[35:4];
  end

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

#-------------------------------------------------------------------------
# Structural
#-------------------------------------------------------------------------

def test_port_wire( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.wire_ = Wire( Bits32 )
      s.out = OutPort( Bits32 )
      connect( s.in_, s.wire_ )
      connect( s.wire_, s.out )
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [31:0] out,
  input logic [0:0] reset
);
  logic [31:0] wire_;

  assign wire_ = in_;
  assign out = wire_;

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_connect_constant( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      connect( 42, s.out )
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  output logic [31:0] out,
  input logic [0:0] reset
);

  assign out = 32'd42;

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_port_const_unaccessed( do_test ):
  class A( Component ):
    def construct( s ):
      s.STATE_IDLE = 42
      s.out = OutPort( Bits32 )
      connect( s.STATE_IDLE, s.out )
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  output logic [31:0] out,
  input logic [0:0] reset
);

  assign out = 32'd42;

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_port_const_accessed( do_test ):
  class A( Component ):
    def construct( s ):
      s.STATE_IDLE = 42
      s.out_1 = OutPort( Bits32 )
      s.out_2 = OutPort( Bits32 )
      connect( s.STATE_IDLE, s.out_1 )
      @s.update
      def upblk():
        s.out_2 = s.STATE_IDLE
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  output logic [31:0] out_1,
  output logic [31:0] out_2,
  input logic [0:0] reset
);
  localparam [31:0] STATE_IDLE = 32'd42;

  // @s.update
  // def upblk():
  //   s.out_2 = s.STATE_IDLE

  always_comb begin : upblk
    out_2 = STATE_IDLE;
  end

  assign out_1 = 32'd42;

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  output logic [31:0] out_1,
  output logic [31:0] out_2,
  input logic [0:0] reset
);

  // @s.update
  // def upblk():
  //   s.out_2 = s.STATE_IDLE

  always_comb begin : upblk
    out_2 = 32'd42;
  end

  assign out_1 = 32'd42;

endmodule
"""
  do_test( a )

def test_port_const_array( do_test ):
  class A( Component ):
    def construct( s ):
      s.STATES = [ 1, 2, 3, 4, 5 ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      s.tmp = OutPort( Bits32 )
      for i in range(5):
        connect( s.STATES[i], s.out[i] )
      @s.update
      def upblk():
        s.tmp = s.STATES[0]
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  output logic [31:0] out [0:4],
  input logic [0:0] reset,
  output logic [31:0] tmp
);
  localparam [31:0] STATES [0:4] = '{ 32'd1, 32'd2, 32'd3, 32'd4, 32'd5 };

  // @s.update
  // def upblk():
  //   s.tmp = s.STATES[0]

  always_comb begin : upblk
    tmp = STATES[0];
  end

  assign out[0] = 32'd1;
  assign out[1] = 32'd2;
  assign out[2] = 32'd3;
  assign out[3] = 32'd4;
  assign out[4] = 32'd5;

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  output logic [31:0] out__0,
  output logic [31:0] out__1,
  output logic [31:0] out__2,
  output logic [31:0] out__3,
  output logic [31:0] out__4,
  input logic [0:0] reset,
  output logic [31:0] tmp
);
  logic [31:0] out [0:4];

  // @s.update
  // def upblk():
  //   s.tmp = s.STATES[0]

  always_comb begin : upblk
    tmp = 32'd1;
  end

  assign out__0 = out[0];
  assign out__1 = out[1];
  assign out__2 = out[2];
  assign out__3 = out[3];
  assign out__4 = out[4];
  assign out[0] = 32'd1;
  assign out[1] = 32'd2;
  assign out[2] = 32'd3;
  assign out[3] = 32'd4;
  assign out[4] = 32'd5;

endmodule
"""
  do_test( a )

def test_port_bit_selection( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      connect( s.out, s.in_[2] )
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [0:0] out,
  input logic [0:0] reset
);

  assign out = in_[2:2];

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_port_part_selection( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits4 )
      connect( s.out, s.in_[2:6] )
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [3:0] out,
  input logic [0:0] reset
);

  assign out = in_[5:2];

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_port_wire_array_index( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      s.wire_ = [ Wire(Bits32) for _ in range(5) ]
      for i in range(5):
        connect( s.wire_[i], s.out[i] )
        connect( s.wire_[i], i )
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  output logic [31:0] out [0:4],
  input logic [0:0] reset
);
  logic [31:0] wire_ [0:4];

  assign out[0] = wire_[0];
  assign wire_[0] = 32'd0;
  assign out[1] = wire_[1];
  assign wire_[1] = 32'd1;
  assign out[2] = wire_[2];
  assign wire_[2] = 32'd2;
  assign out[3] = wire_[3];
  assign wire_[3] = 32'd3;
  assign out[4] = wire_[4];
  assign wire_[4] = 32'd4;

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  output logic [31:0] out__0,
  output logic [31:0] out__1,
  output logic [31:0] out__2,
  output logic [31:0] out__3,
  output logic [31:0] out__4,
  input logic [0:0] reset
);
  logic [31:0] out [0:4];
  logic [31:0] wire_ [0:4];

  assign out__0 = out[0];
  assign out__1 = out[1];
  assign out__2 = out[2];
  assign out__3 = out[3];
  assign out__4 = out[4];
  assign out[0] = wire_[0];
  assign wire_[0] = 32'd0;
  assign out[1] = wire_[1];
  assign wire_[1] = 32'd1;
  assign out[2] = wire_[2];
  assign wire_[2] = 32'd2;
  assign out[3] = wire_[3];
  assign wire_[3] = 32'd3;
  assign out[4] = wire_[4];
  assign wire_[4] = 32'd4;

endmodule
"""
  do_test( a )
