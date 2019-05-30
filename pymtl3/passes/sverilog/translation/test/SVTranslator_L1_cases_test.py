#=========================================================================
# SVTranslator_L1_cases_test.py
#=========================================================================
"""Test the SystemVerilog translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits1, Bits32, Bits64, concat, sext, zext
from pymtl3.dsl import Component, InPort, OutPort
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.SVTranslator import SVTranslator


def local_do_test( m ):
  m.elaborate()
  tr = SVTranslator( m )
  tr.translate()
  assert tr.hierarchy.src == m._ref_src

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
"""\
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [31:0] out,
  input logic [0:0] reset
);

  always_comb begin : upblk
    out = in_;
  end

endmodule
"""
  do_test( a )

def test_seq_assign( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update_on_edge
      def upblk():
        s.out = s.in_
  a = A()
  a._ref_src = \
"""\
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [31:0] out,
  input logic [0:0] reset
);

  always_ff @(posedge clk) begin : upblk
    out <= in_;
  end

endmodule
"""
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
"""\
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_1,
  input logic [31:0] in_2,
  output logic [63:0] out,
  input logic [0:0] reset
);

  always_comb begin : upblk
    out = { in_1, in_2 };
  end

endmodule
"""
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
"""\
module A
(
  input logic [0:0] clk,
  output logic [63:0] out,
  input logic [0:0] reset
);

  always_comb begin : upblk
    out = { 32'd42, 32'd0 };
  end

endmodule
"""
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
"""\
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [63:0] out,
  input logic [0:0] reset
);

  always_comb begin : upblk
    out = { in_, 32'd0 };
  end

endmodule
"""
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
"""\
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [63:0] out,
  input logic [0:0] reset
);

  always_comb begin : upblk
    out = { { 32 { in_[31] } }, in_ };
  end

endmodule
"""
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
"""\
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [63:0] out,
  input logic [0:0] reset
);

  always_comb begin : upblk
    out = { { 32 { 1'b0 } }, in_ };
  end

endmodule
"""
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
"""\
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [63:0] out,
  input logic [0:0] reset
);
  localparam [31:0] _fvar_STATE_IDLE = 32'd42;

  always_comb begin : upblk
    out = { in_, _fvar_STATE_IDLE };
  end

endmodule
"""
  do_test( a )

def test_unpacked_signal_index( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange(2) ]
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = concat( s.in_[0], s.in_[1] )
  a = A()
  a._ref_src = \
"""\
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_ [0:1],
  output logic [63:0] out,
  input logic [0:0] reset
);

  always_comb begin : upblk
    out = { in_[0], in_[1] };
  end

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
"""\
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [0:0] out,
  input logic [0:0] reset
);

  always_comb begin : upblk
    out = in_[1];
  end

endmodule
"""
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
"""\
module A
(
  input logic [0:0] clk,
  input logic [63:0] in_,
  output logic [31:0] out,
  input logic [0:0] reset
);

  always_comb begin : upblk
    out = in_[35:4];
  end

endmodule
"""
  do_test( a )
