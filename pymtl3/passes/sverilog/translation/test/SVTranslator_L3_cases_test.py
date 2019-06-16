#=========================================================================
# SVTranslator_L3_cases_test.py
#=========================================================================
"""Test the SystemVerilog translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits1, Bits32
from pymtl3.dsl import Component, InPort, Interface, OutPort
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.SVTranslator import SVTranslator

from .SVTranslator_L1_cases_test import trim


def local_do_test( m ):
  m.elaborate()
  tr = SVTranslator( m )
  tr.translate( m )
  assert trim( tr.hierarchy.src ) == m._ref_src

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
  input logic [31:0] in_$msg,
  output logic [0:0] in_$rdy,
  input logic [0:0] in_$val,
  output logic [31:0] out$msg,
  input logic [0:0] out$rdy,
  output logic [0:0] out$val
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out.val = s.in_.val
  //   s.out.msg = s.in_.msg
  //   s.in_.rdy = s.out.rdy
  
  always_comb begin : upblk
    out$val = in_$val;
    out$msg = in_$msg;
    in_$rdy = out$rdy;
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
  output logic [31:0] in_$__0$foo,
  output logic [31:0] in_$__1$foo
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out = s.in_[1].foo
  
  always_comb begin : upblk
    out = in_$__1$foo;
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
  output logic [31:0] in_$__0$foo,
  output logic [31:0] in_$__1$foo
);
  logic [31:0] in_$foo [0:1];

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out = s.in_[1].foo
  
  always_comb begin : upblk
    out = in_$foo[1];
  end

  assign in_$__0$foo = in_$foo[0];
  assign in_$__1$foo = in_$foo[1];

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
      s.connect( s.ifc.msg, 42 )
      # This 1 will be converted to Bits1(1) by DSL
      s.connect( s.ifc.val, 1 )
  a = A()
  a._ref_src = \
"""\

module A
(
  input logic [0:0] clk,
  input logic [0:0] reset,
  output logic [31:0] ifc$msg,
  input logic [0:0] ifc$rdy,
  output logic [0:0] ifc$val
);

  assign ifc$msg = 32'd42;
  assign ifc$val = 1'd1;

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
      s.connect( s.out, s.in_ )
  a = A()
  a._ref_src = \
"""\

module A
(
  input logic [0:0] clk,
  input logic [0:0] reset,
  input logic [31:0] in_$msg,
  output logic [0:0] in_$rdy,
  input logic [0:0] in_$val,
  output logic [31:0] out$msg,
  input logic [0:0] out$rdy,
  output logic [0:0] out$val
);

  assign out$msg = in_$msg;
  assign in_$rdy = out$rdy;
  assign out$val = in_$val;

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )
