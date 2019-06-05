#=========================================================================
# SVTranslator_L3_cases_test.py
#=========================================================================
"""Test the SystemVerilog translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits1, Bits32
from pymtl3.dsl import Component, InPort, Interface, OutPort
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.SVTranslator import SVTranslator


def local_do_test( m ):
  m.elaborate()
  tr = SVTranslator( m )
  tr.translate()
  assert tr.hierarchy.src == m._ref_src

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
"""\
module A
(
  input logic [0:0] clk,
  input logic [0:0] reset,
  input logic [31:0] in__$msg,
  output logic [0:0] in__$rdy,
  input logic [0:0] in__$val,
  output logic [31:0] out_$msg,
  input logic [0:0] out_$rdy,
  output logic [0:0] out_$val
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out.val = s.in_.val
  //   s.out.msg = s.in_.msg
  //   s.in_.rdy = s.out.rdy
  
  always_comb begin : upblk
    out_$val = in__$val;
    out_$msg = in__$msg;
    in__$rdy = out_$rdy;
  end

endmodule
"""
  do_test( a )

def test_interface_index( do_test ):
  class Ifc( Interface ):
    def construct( s ):
      s.foo = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.in_ = [ Ifc() for _ in xrange(2) ]
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_[1].foo
  a = A()
  a._ref_src = \
"""\
module A
(
  input logic [0:0] clk,
  output logic [31:0] out,
  input logic [0:0] reset,
  output logic [31:0] in__$0_$foo,
  output logic [31:0] in__$1_$foo
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out = s.in_[1].foo
  
  always_comb begin : upblk
    out = in__$1_$foo;
  end

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
  output logic [31:0] ifc_$msg,
  input logic [0:0] ifc_$rdy,
  output logic [0:0] ifc_$val
);

  assign ifc_$msg = 32'd42;
  assign ifc_$val = 1'd1;

endmodule
"""
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
  input logic [31:0] in__$msg,
  output logic [0:0] in__$rdy,
  input logic [0:0] in__$val,
  output logic [31:0] out_$msg,
  input logic [0:0] out_$rdy,
  output logic [0:0] out_$val
);

  assign out_$msg = in__$msg;
  assign in__$rdy = out_$rdy;
  assign out_$val = in__$val;

endmodule
"""
  do_test( a )
