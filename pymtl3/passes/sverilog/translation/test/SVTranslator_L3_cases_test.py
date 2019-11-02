#=========================================================================
# SVTranslator_L3_cases_test.py
#=========================================================================
"""Test the SystemVerilog translator."""

from pymtl3.datatypes import Bits1, Bits32
from pymtl3.dsl import Component, InPort, Interface, OutPort, connect
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

def test_interface( do_test ):
  class InIfc( Interface ):
    def construct( s ):
      s.val = InPort( Bits1 )
      s.msg = InPort( Bits32 )
      s.rdy = OutPort( Bits1 )
  class OutIfc( Interface ):
    def construct( s ):
      s.val = OutPort( Bits1 )
      s.msg = OutPort( Bits32 )
      s.rdy = InPort( Bits1 )
  class A( Component ):
    def construct( s ):
      s.in_ = InIfc()
      s.out = OutIfc()
      @s.update
      def upblk():
        s.out.val = s.in_.val
        s.out.msg = s.in_.msg
        s.in_.rdy = s.out.rdy
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [0:0] reset,
  input logic [31:0] in___msg,
  output logic [0:0] in___rdy,
  input logic [0:0] in___val,
  output logic [31:0] out__msg,
  input logic [0:0] out__rdy,
  output logic [0:0] out__val
);

  // @s.update
  // def upblk():
  //   s.out.val = s.in_.val
  //   s.out.msg = s.in_.msg
  //   s.in_.rdy = s.out.rdy

  always_comb begin : upblk
    out__val = in___val;
    out__msg = in___msg;
    in___rdy = out__rdy;
  end

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_interface_index( do_test ):
  class Ifc( Interface ):
    def construct( s ):
      s.foo = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.in_ = [ Ifc() for _ in range(2) ]
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_[1].foo
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  output logic [31:0] out,
  input logic [0:0] reset,
  output logic [31:0] in___0__foo,
  output logic [31:0] in___1__foo
);

  // @s.update
  // def upblk():
  //   s.out = s.in_[1].foo

  always_comb begin : upblk
    out = in___1__foo;
  end

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  output logic [31:0] out,
  input logic [0:0] reset,
  output logic [31:0] in___0__foo,
  output logic [31:0] in___1__foo
);
  logic [31:0] in___foo [0:1];

  // @s.update
  // def upblk():
  //   s.out = s.in_[1].foo

  always_comb begin : upblk
    out = in___foo[1];
  end

  assign in___0__foo = in___foo[0];
  assign in___1__foo = in___foo[1];

endmodule
"""
  do_test( a )

#-------------------------------------------------------------------------
# Structural
#-------------------------------------------------------------------------

def test_ifc_decls( do_test ):
  class Ifc( Interface ):
    def construct( s ):
      s.msg = OutPort( Bits32 )
      s.val = OutPort( Bits1 )
      s.rdy = InPort( Bits1 )
  class A( Component ):
    def construct( s ):
      s.ifc = Ifc()
      # This 42 will be converted to Bits32(42) by DSL
      connect( s.ifc.msg, 42 )
      # This 1 will be converted to Bits1(1) by DSL
      connect( s.ifc.val, 1 )
  a = A()
  a._ref_src = \
"""\

module A
(
  input logic [0:0] clk,
  input logic [0:0] reset,
  output logic [31:0] ifc__msg,
  input logic [0:0] ifc__rdy,
  output logic [0:0] ifc__val
);

  assign ifc__msg = 32'd42;
  assign ifc__val = 1'd1;

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_multi_ifc_decls( do_test ):
  class InIfc( Interface ):
    def construct( s ):
      s.msg = InPort( Bits32 )
      s.val = InPort( Bits1 )
      s.rdy = OutPort( Bits1 )
  class OutIfc( Interface ):
    def construct( s ):
      s.msg = OutPort( Bits32 )
      s.val = OutPort( Bits1 )
      s.rdy = InPort( Bits1 )
  class A( Component ):
    def construct( s ):
      s.in_ = InIfc()
      s.out = OutIfc()
      connect( s.out, s.in_ )
  a = A()
  a._ref_src = \
"""\

module A
(
  input logic [0:0] clk,
  input logic [0:0] reset,
  input logic [31:0] in___msg,
  output logic [0:0] in___rdy,
  input logic [0:0] in___val,
  output logic [31:0] out__msg,
  input logic [0:0] out__rdy,
  output logic [0:0] out__val
);

  assign out__msg = in___msg;
  assign in___rdy = out__rdy;
  assign out__val = in___val;

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )
