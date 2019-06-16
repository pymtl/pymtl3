#=========================================================================
# SVTranslator_L2_cases_test.py
#=========================================================================
"""Test the SystemVerilog translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits1, Bits32, Bits96, BitStruct, concat
from pymtl3.dsl import Component, InPort, OutPort, Wire
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

def test_if( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        if Bits1(1):
          s.out = s.in_1
        else:
          s.out = s.in_2
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_1,
  input logic [31:0] in_2,
  output logic [31:0] out,
  input logic [0:0] reset
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   if Bits1(1):
  //     s.out = s.in_1
  //   else:
  //     s.out = s.in_2
  
  always_comb begin : upblk
    if ( 1'd1 ) begin
      out = in_1;
    end
    else
      out = in_2;
  end

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_if_dangling_else_inner( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        if Bits1(1):
          if Bits1(0):
            s.out = s.in_1
          else:
            s.out = s.in_2
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_1,
  input logic [31:0] in_2,
  output logic [31:0] out,
  input logic [0:0] reset
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   if Bits1(1):
  //     if Bits1(0):
  //       s.out = s.in_1
  //     else:
  //       s.out = s.in_2
  
  always_comb begin : upblk
    if ( 1'd1 ) begin
      if ( 1'd0 ) begin
        out = in_1;
      end
      else
        out = in_2;
    end
  end

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_if_dangling_else_outter( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        if Bits1(1):
          if Bits1(0):
            s.out = s.in_1
        else:
          s.out = s.in_2
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_1,
  input logic [31:0] in_2,
  output logic [31:0] out,
  input logic [0:0] reset
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   if Bits1(1):
  //     if Bits1(0):
  //       s.out = s.in_1
  //   else:
  //     s.out = s.in_2
  
  always_comb begin : upblk
    if ( 1'd1 ) begin
      if ( 1'd0 ) begin
        out = in_1;
      end
    end
    else
      out = in_2;
  end

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_if_branches( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.in_3 = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        if Bits1(1):
          s.out = s.in_1
        elif Bits1(0):
          s.out = s.in_2
        else:
          s.out = s.in_3
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_1,
  input logic [31:0] in_2,
  input logic [31:0] in_3,
  output logic [31:0] out,
  input logic [0:0] reset
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   if Bits1(1):
  //     s.out = s.in_1
  //   elif Bits1(0):
  //     s.out = s.in_2
  //   else:
  //     s.out = s.in_3
  
  always_comb begin : upblk
    if ( 1'd1 ) begin
      out = in_1;
    end
    else if ( 1'd0 ) begin
      out = in_2;
    end
    else
      out = in_3;
  end

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_nested_if( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.in_3 = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        if Bits1(1):
          if Bits1(0):
            s.out = s.in_1
          else:
            s.out = s.in_2
        elif Bits1(0):
          if Bits1(1):
            s.out = s.in_2
          else:
            s.out = s.in_3
        else:
          if Bits1(1):
            s.out = s.in_3
          else:
            s.out = s.in_1
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_1,
  input logic [31:0] in_2,
  input logic [31:0] in_3,
  output logic [31:0] out,
  input logic [0:0] reset
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   if Bits1(1):
  //     if Bits1(0):
  //       s.out = s.in_1
  //     else:
  //       s.out = s.in_2
  //   elif Bits1(0):
  //     if Bits1(1):
  //       s.out = s.in_2
  //     else:
  //       s.out = s.in_3
  //   else:
  //     if Bits1(1):
  //       s.out = s.in_3
  //     else:
  //       s.out = s.in_1
  
  always_comb begin : upblk
    if ( 1'd1 ) begin
      if ( 1'd0 ) begin
        out = in_1;
      end
      else
        out = in_2;
    end
    else if ( 1'd0 ) begin
      if ( 1'd1 ) begin
        out = in_2;
      end
      else
        out = in_3;
    end
    else if ( 1'd1 ) begin
      out = in_3;
    end
    else
      out = in_1;
  end

endmodule
"""
  a._ref_src_yosys = a._ref_src
  do_test( a )

def test_for_range_upper( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(2) ]
      s.out = [ OutPort( Bits32 ) for _ in range(2) ]
      @s.update
      def upblk():
        for i in range(2):
          s.out[i] = s.in_[i]
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_ [0:1],
  output logic [31:0] out [0:1],
  input logic [0:0] reset
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   for i in range(2):
  //     s.out[i] = s.in_[i]
  
  always_comb begin : upblk
    for ( int i = 0; i < 2; i += 1 )
      out[i] = in_[i];
  end

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_$__0,
  input logic [31:0] in_$__1,
  output logic [31:0] out$__0,
  output logic [31:0] out$__1,
  input logic [0:0] reset
);
  logic [31:0] in_ [0:1];
  logic [31:0] out [0:1];

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   for i in range(2):
  //     s.out[i] = s.in_[i]
  
  integer __loopvar_upblk$i;
  
  always_comb begin : upblk
    for ( __loopvar_upblk$i = 0; __loopvar_upblk$i < 2; __loopvar_upblk$i = __loopvar_upblk$i + 1 )
      out[__loopvar_upblk$i] = in_[__loopvar_upblk$i];
  end

  assign in_[0] = in_$__0;
  assign in_[1] = in_$__1;
  assign out$__0 = out[0];
  assign out$__1 = out[1];

endmodule
"""
  do_test( a )

def test_for_range_lower_upper( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(2) ]
      s.out = [ OutPort( Bits32 ) for _ in range(2) ]
      @s.update
      def upblk():
        for i in range(1, 2):
          s.out[i] = s.in_[i]
        s.out[0] = s.in_[0]
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_ [0:1],
  output logic [31:0] out [0:1],
  input logic [0:0] reset
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   for i in range(1, 2):
  //     s.out[i] = s.in_[i]
  //   s.out[0] = s.in_[0]
  
  always_comb begin : upblk
    for ( int i = 1; i < 2; i += 1 )
      out[i] = in_[i];
    out[0] = in_[0];
  end

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_$__0,
  input logic [31:0] in_$__1,
  output logic [31:0] out$__0,
  output logic [31:0] out$__1,
  input logic [0:0] reset
);
  logic [31:0] in_ [0:1];
  logic [31:0] out [0:1];

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   for i in range(1, 2):
  //     s.out[i] = s.in_[i]
  //   s.out[0] = s.in_[0]
  
  integer __loopvar_upblk$i;
  
  always_comb begin : upblk
    for ( __loopvar_upblk$i = 1; __loopvar_upblk$i < 2; __loopvar_upblk$i = __loopvar_upblk$i + 1 )
      out[__loopvar_upblk$i] = in_[__loopvar_upblk$i];
    out[0] = in_[0];
  end

  assign in_[0] = in_$__0;
  assign in_[1] = in_$__1;
  assign out$__0 = out[0];
  assign out$__1 = out[1];

endmodule
"""
  do_test( a )

def test_for_range_lower_upper_step( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @s.update
      def upblk():
        for i in range(0, 5, 2):
          s.out[i] = s.in_[i]
        for i in range(1, 5, 2):
          s.out[i] = s.in_[i]
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_ [0:4],
  output logic [31:0] out [0:4],
  input logic [0:0] reset
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   for i in range(0, 5, 2):
  //     s.out[i] = s.in_[i]
  //   for i in range(1, 5, 2):
  //     s.out[i] = s.in_[i]
  
  always_comb begin : upblk
    for ( int i = 0; i < 5; i += 2 )
      out[i] = in_[i];
    for ( int i = 1; i < 5; i += 2 )
      out[i] = in_[i];
  end

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_$__0,
  input logic [31:0] in_$__1,
  input logic [31:0] in_$__2,
  input logic [31:0] in_$__3,
  input logic [31:0] in_$__4,
  output logic [31:0] out$__0,
  output logic [31:0] out$__1,
  output logic [31:0] out$__2,
  output logic [31:0] out$__3,
  output logic [31:0] out$__4,
  input logic [0:0] reset
);
  logic [31:0] in_ [0:4];
  logic [31:0] out [0:4];

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   for i in range(0, 5, 2):
  //     s.out[i] = s.in_[i]
  //   for i in range(1, 5, 2):
  //     s.out[i] = s.in_[i]
  
  integer __loopvar_upblk$i;
  
  always_comb begin : upblk
    for ( __loopvar_upblk$i = 0; __loopvar_upblk$i < 5; __loopvar_upblk$i = __loopvar_upblk$i + 2 )
      out[__loopvar_upblk$i] = in_[__loopvar_upblk$i];
    for ( __loopvar_upblk$i = 1; __loopvar_upblk$i < 5; __loopvar_upblk$i = __loopvar_upblk$i + 2 )
      out[__loopvar_upblk$i] = in_[__loopvar_upblk$i];
  end

  assign in_[0] = in_$__0;
  assign in_[1] = in_$__1;
  assign in_[2] = in_$__2;
  assign in_[3] = in_$__3;
  assign in_[4] = in_$__4;
  assign out$__0 = out[0];
  assign out$__1 = out[1];
  assign out$__2 = out[2];
  assign out$__3 = out[3];
  assign out$__4 = out[4];

endmodule
"""
  do_test( a )

def test_if_exp_for( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @s.update
      def upblk():
        for i in range(5):
          s.out[i] = s.in_[i] if i == 1 else s.in_[0]
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_ [0:4],
  output logic [31:0] out [0:4],
  input logic [0:0] reset
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   for i in range(5):
  //     s.out[i] = s.in_[i] if i == 1 else s.in_[0]
  
  always_comb begin : upblk
    for ( int i = 0; i < 5; i += 1 )
      out[i] = ( i == 1 ) ? in_[i] : in_[0];
  end

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_$__0,
  input logic [31:0] in_$__1,
  input logic [31:0] in_$__2,
  input logic [31:0] in_$__3,
  input logic [31:0] in_$__4,
  output logic [31:0] out$__0,
  output logic [31:0] out$__1,
  output logic [31:0] out$__2,
  output logic [31:0] out$__3,
  output logic [31:0] out$__4,
  input logic [0:0] reset
);
  logic [31:0] in_ [0:4];
  logic [31:0] out [0:4];

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   for i in range(5):
  //     s.out[i] = s.in_[i] if i == 1 else s.in_[0]
  
  integer __loopvar_upblk$i;
  
  always_comb begin : upblk
    for ( __loopvar_upblk$i = 0; __loopvar_upblk$i < 5; __loopvar_upblk$i = __loopvar_upblk$i + 1 )
      out[__loopvar_upblk$i] = ( __loopvar_upblk$i == 1 ) ? in_[__loopvar_upblk$i] : in_[0];
  end

  assign in_[0] = in_$__0;
  assign in_[1] = in_$__1;
  assign in_[2] = in_$__2;
  assign in_[3] = in_$__3;
  assign in_[4] = in_$__4;
  assign out$__0 = out[0];
  assign out$__1 = out[1];
  assign out$__2 = out[2];
  assign out$__3 = out[3];
  assign out$__4 = out[4];

endmodule
"""
  do_test( a )

def test_if_exp_unary_op( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @s.update
      def upblk():
        for i in range(5):
          s.out[i] = (~s.in_[i]) if i == 1 else s.in_[0]
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_ [0:4],
  output logic [31:0] out [0:4],
  input logic [0:0] reset
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   for i in range(5):
  //     s.out[i] = (~s.in_[i]) if i == 1 else s.in_[0]
  
  always_comb begin : upblk
    for ( int i = 0; i < 5; i += 1 )
      out[i] = ( i == 1 ) ? ~in_[i] : in_[0];
  end

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_$__0,
  input logic [31:0] in_$__1,
  input logic [31:0] in_$__2,
  input logic [31:0] in_$__3,
  input logic [31:0] in_$__4,
  output logic [31:0] out$__0,
  output logic [31:0] out$__1,
  output logic [31:0] out$__2,
  output logic [31:0] out$__3,
  output logic [31:0] out$__4,
  input logic [0:0] reset
);
  logic [31:0] in_ [0:4];
  logic [31:0] out [0:4];

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   for i in range(5):
  //     s.out[i] = (~s.in_[i]) if i == 1 else s.in_[0]
  
  integer __loopvar_upblk$i;
  
  always_comb begin : upblk
    for ( __loopvar_upblk$i = 0; __loopvar_upblk$i < 5; __loopvar_upblk$i = __loopvar_upblk$i + 1 )
      out[__loopvar_upblk$i] = ( __loopvar_upblk$i == 1 ) ? ~in_[__loopvar_upblk$i] : in_[0];
  end

  assign in_[0] = in_$__0;
  assign in_[1] = in_$__1;
  assign in_[2] = in_$__2;
  assign in_[3] = in_$__3;
  assign in_[4] = in_$__4;
  assign out$__0 = out[0];
  assign out$__1 = out[1];
  assign out$__2 = out[2];
  assign out$__3 = out[3];
  assign out$__4 = out[4];

endmodule
"""
  do_test( a )

def test_if_bool_op( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @s.update
      def upblk():
        for i in range(5):
          if s.in_[i] and (s.in_[i+1] if i<5 else s.in_[4]):
            s.out[i] = s.in_[i]
          else:
            s.out[i] = Bits32(0)
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_ [0:4],
  output logic [31:0] out [0:4],
  input logic [0:0] reset
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   for i in range(5):
  //     if s.in_[i] and (s.in_[i+1] if i<5 else s.in_[4]):
  //       s.out[i] = s.in_[i]
  //     else:
  //       s.out[i] = Bits32(0)
  
  always_comb begin : upblk
    for ( int i = 0; i < 5; i += 1 )
      if ( in_[i] && ( ( i < 5 ) ? in_[i + 1] : in_[4] ) ) begin
        out[i] = in_[i];
      end
      else
        out[i] = 32'd0;
  end

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_$__0,
  input logic [31:0] in_$__1,
  input logic [31:0] in_$__2,
  input logic [31:0] in_$__3,
  input logic [31:0] in_$__4,
  output logic [31:0] out$__0,
  output logic [31:0] out$__1,
  output logic [31:0] out$__2,
  output logic [31:0] out$__3,
  output logic [31:0] out$__4,
  input logic [0:0] reset
);
  logic [31:0] in_ [0:4];
  logic [31:0] out [0:4];

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   for i in range(5):
  //     if s.in_[i] and (s.in_[i+1] if i<5 else s.in_[4]):
  //       s.out[i] = s.in_[i]
  //     else:
  //       s.out[i] = Bits32(0)
  
  integer __loopvar_upblk$i;
  
  always_comb begin : upblk
    for ( __loopvar_upblk$i = 0; __loopvar_upblk$i < 5; __loopvar_upblk$i = __loopvar_upblk$i + 1 )
      if ( in_[__loopvar_upblk$i] && ( ( __loopvar_upblk$i < 5 ) ? in_[__loopvar_upblk$i + 1] : in_[4] ) ) begin
        out[__loopvar_upblk$i] = in_[__loopvar_upblk$i];
      end
      else
        out[__loopvar_upblk$i] = 32'd0;
  end

  assign in_[0] = in_$__0;
  assign in_[1] = in_$__1;
  assign in_[2] = in_$__2;
  assign in_[3] = in_$__3;
  assign in_[4] = in_$__4;
  assign out$__0 = out[0];
  assign out$__1 = out[1];
  assign out$__2 = out[2];
  assign out$__3 = out[3];
  assign out$__4 = out[4];

endmodule
"""
  do_test( a )

def test_tmpvar( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @s.update
      def upblk():
        for i in range(5):
          if s.in_[i] and (s.in_[i+1] if i<5 else s.in_[4]):
            tmpvar = s.in_[i]
          else:
            tmpvar = Bits32(0)
          s.out[i] = tmpvar
  a = A()
  a._ref_src = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_ [0:4],
  output logic [31:0] out [0:4],
  input logic [0:0] reset
);
  logic [31:0] __tmpvar_upblk$tmpvar;

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   for i in range(5):
  //     if s.in_[i] and (s.in_[i+1] if i<5 else s.in_[4]):
  //       tmpvar = s.in_[i]
  //     else:
  //       tmpvar = Bits32(0)
  //     s.out[i] = tmpvar
  
  always_comb begin : upblk
    for ( int i = 0; i < 5; i += 1 ) begin
      if ( in_[i] && ( ( i < 5 ) ? in_[i + 1] : in_[4] ) ) begin
        __tmpvar_upblk$tmpvar = in_[i];
      end
      else
        __tmpvar_upblk$tmpvar = 32'd0;
      out[i] = __tmpvar_upblk$tmpvar;
    end
  end

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_$__0,
  input logic [31:0] in_$__1,
  input logic [31:0] in_$__2,
  input logic [31:0] in_$__3,
  input logic [31:0] in_$__4,
  output logic [31:0] out$__0,
  output logic [31:0] out$__1,
  output logic [31:0] out$__2,
  output logic [31:0] out$__3,
  output logic [31:0] out$__4,
  input logic [0:0] reset
);
  logic [31:0] in_ [0:4];
  logic [31:0] out [0:4];
  logic [31:0] __tmpvar_upblk$tmpvar;

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   for i in range(5):
  //     if s.in_[i] and (s.in_[i+1] if i<5 else s.in_[4]):
  //       tmpvar = s.in_[i]
  //     else:
  //       tmpvar = Bits32(0)
  //     s.out[i] = tmpvar
  
  integer __loopvar_upblk$i;
  
  always_comb begin : upblk
    for ( __loopvar_upblk$i = 0; __loopvar_upblk$i < 5; __loopvar_upblk$i = __loopvar_upblk$i + 1 ) begin
      if ( in_[__loopvar_upblk$i] && ( ( __loopvar_upblk$i < 5 ) ? in_[__loopvar_upblk$i + 1] : in_[4] ) ) begin
        __tmpvar_upblk$tmpvar = in_[__loopvar_upblk$i];
      end
      else
        __tmpvar_upblk$tmpvar = 32'd0;
      out[__loopvar_upblk$i] = __tmpvar_upblk$tmpvar;
    end
  end

  assign in_[0] = in_$__0;
  assign in_[1] = in_$__1;
  assign in_[2] = in_$__2;
  assign in_[3] = in_$__3;
  assign in_[4] = in_$__4;
  assign out$__0 = out[0];
  assign out$__1 = out[1];
  assign out$__2 = out[2];
  assign out$__3 = out[3];
  assign out$__4 = out[4];

endmodule
"""
  do_test( a )

def test_struct( do_test ):
  class B( BitStruct ):
    def __init__( s, foo=42 ):
      s.foo = Bits32(42)
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_.foo
  a = A()
  a._ref_src = \
"""
typedef struct packed {
  logic [31:0] foo;
} B;

module A
(
  input logic [0:0] clk,
  input B in_,
  output logic [31:0] out,
  input logic [0:0] reset
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out = s.in_.foo
  
  always_comb begin : upblk
    out = in_.foo;
  end

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_$foo,
  output logic [31:0] out,
  input logic [0:0] reset
);
  logic [31:0] in_;

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out = s.in_.foo
  
  always_comb begin : upblk
    out = in_$foo;
  end

  assign in_[31:0] = in_$foo;

endmodule
"""
  do_test( a )

def test_packed_array_concat( do_test ):
  class B( BitStruct ):
    def __init__( s, foo=42, bar=1 ):
      s.foo = Bits32(foo)
      s.bar = [ Bits32(bar) for _ in range(2) ]
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits96 )
      @s.update
      def upblk():
        s.out = concat( s.in_.bar[0], s.in_.bar[1], s.in_.foo )
  a = A()
  a._ref_src = \
"""
typedef struct packed {
  logic [1:0][31:0] bar;
  logic [31:0] foo;
} B;

module A
(
  input logic [0:0] clk,
  input B in_,
  output logic [95:0] out,
  input logic [0:0] reset
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out = concat( s.in_.bar[0], s.in_.bar[1], s.in_.foo )
  
  always_comb begin : upblk
    out = { in_.bar[0], in_.bar[1], in_.foo };
  end

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_$bar$__0,
  input logic [31:0] in_$bar$__1,
  input logic [31:0] in_$foo,
  output logic [95:0] out,
  input logic [0:0] reset
);
  logic [31:0] in_$bar [0:1];
  logic [95:0] in_;

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out = concat( s.in_.bar[0], s.in_.bar[1], s.in_.foo )
  
  always_comb begin : upblk
    out = { in_$bar[0], in_$bar[1], in_$foo };
  end

  assign in_$bar[0] = in_$bar$__0;
  assign in_$bar[1] = in_$bar$__1;
  assign in_[95:64] = in_$bar$__1;
  assign in_[63:32] = in_$bar$__0;
  assign in_[31:0] = in_$foo;

endmodule
"""
  do_test( a )

def test_nested_struct( do_test ):
  class C( BitStruct ):
    def __init__( s, woof=2 ):
      s.woof = Bits32(woof)
  class B( BitStruct ):
    def __init__( s, foo=42, bar=1 ):
      s.foo = Bits32(foo)
      s.bar = [ Bits32(bar) for _ in range(2) ]
      s.c = C()
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits96 )
      @s.update
      def upblk():
        s.out = concat( s.in_.bar[0], s.in_.c.woof, s.in_.foo )
  a = A()
  a._ref_src = \
"""
typedef struct packed {
  logic [31:0] woof;
} C;

typedef struct packed {
  logic [1:0][31:0] bar;
  C c;
  logic [31:0] foo;
} B;

module A
(
  input logic [0:0] clk,
  input B in_,
  output logic [95:0] out,
  input logic [0:0] reset
);

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out = concat( s.in_.bar[0], s.in_.c.woof, s.in_.foo )
  
  always_comb begin : upblk
    out = { in_.bar[0], in_.c.woof, in_.foo };
  end

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_$bar$__0,
  input logic [31:0] in_$bar$__1,
  input logic [31:0] in_$c$woof,
  input logic [31:0] in_$foo,
  output logic [95:0] out,
  input logic [0:0] reset
);
  logic [31:0] in_$bar [0:1];
  logic [31:0] in_$c;
  logic [127:0] in_;

  // PYMTL SOURCE:
  // 
  // @s.update
  // def upblk():
  //   s.out = concat( s.in_.bar[0], s.in_.c.woof, s.in_.foo )
  
  always_comb begin : upblk
    out = { in_$bar[0], in_$c$woof, in_$foo };
  end

  assign in_$bar[0] = in_$bar$__0;
  assign in_$bar[1] = in_$bar$__1;
  assign in_$c[31:0] = in_$c$woof;
  assign in_[127:96] = in_$bar$__1;
  assign in_[95:64] = in_$bar$__0;
  assign in_[63:32] = in_$c$woof;
  assign in_[31:0] = in_$foo;

endmodule
"""
  do_test( a )

#-------------------------------------------------------------------------
# Structural
#-------------------------------------------------------------------------

def test_struct_port( do_test ):
  class B( BitStruct ):
    def __init__( s, foo=42 ):
      s.foo = Bits32(foo)
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits32 )
      s.connect( s.out, s.in_.foo )
  a = A()
  a._ref_src = \
"""
typedef struct packed {
  logic [31:0] foo;
} B;

module A
(
  input logic [0:0] clk,
  input B in_,
  output logic [31:0] out,
  input logic [0:0] reset
);

  assign out = in_.foo;

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_$foo,
  output logic [31:0] out,
  input logic [0:0] reset
);
  logic [31:0] in_;

  assign in_[31:0] = in_$foo;
  assign out = in_$foo;

endmodule
"""
  do_test( a )

def test_nested_struct_port( do_test ):
  class C( BitStruct ):
    def __init__( s, bar=1 ):
      s.bar = Bits32(bar)
  class B( BitStruct ):
    def __init__( s, foo=42 ):
      s.foo = Bits32(foo)
      s.c = C()
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out_foo = OutPort( Bits32 )
      s.out_bar = OutPort( Bits32 )
      s.connect( s.out_foo, s.in_.foo )
      s.connect( s.out_bar, s.in_.c.bar )
  a = A()
  a._ref_src = \
"""
typedef struct packed {
  logic [31:0] bar;
} C;

typedef struct packed {
  C c;
  logic [31:0] foo;
} B;

module A
(
  input logic [0:0] clk,
  input B in_,
  output logic [31:0] out_bar,
  output logic [31:0] out_foo,
  input logic [0:0] reset
);

  assign out_foo = in_.foo;
  assign out_bar = in_.c.bar;

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_$c$bar,
  input logic [31:0] in_$foo,
  output logic [31:0] out_bar,
  output logic [31:0] out_foo,
  input logic [0:0] reset
);
  logic [31:0] in_$c;
  logic [63:0] in_;

  assign in_$c[31:0] = in_$c$bar;
  assign in_[63:32] = in_$c$bar;
  assign in_[31:0] = in_$foo;
  assign out_foo = in_$foo;
  assign out_bar = in_$c$bar;

endmodule
"""
  do_test( a )

def test_packed_array( do_test ):
  class B( BitStruct ):
    def __init__( s, foo=42 ):
      s.foo = [ Bits32(foo) for _ in range(2) ]
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out =  [ OutPort( Bits32 ) for _ in range(2) ]
      s.connect( s.out[0], s.in_.foo[0] )
      s.connect( s.out[1], s.in_.foo[1] )
  a = A()
  a._ref_src = \
"""
typedef struct packed {
  logic [1:0][31:0] foo;
} B;

module A
(
  input logic [0:0] clk,
  input B in_,
  output logic [31:0] out [0:1],
  input logic [0:0] reset
);

  assign out[0] = in_.foo[0];
  assign out[1] = in_.foo[1];

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_$foo$__0,
  input logic [31:0] in_$foo$__1,
  output logic [31:0] out$__0,
  output logic [31:0] out$__1,
  input logic [0:0] reset
);
  logic [31:0] in_$foo [0:1];
  logic [63:0] in_;
  logic [31:0] out [0:1];

  assign in_$foo[0] = in_$foo$__0;
  assign in_$foo[1] = in_$foo$__1;
  assign in_[63:32] = in_$foo$__1;
  assign in_[31:0] = in_$foo$__0;
  assign out$__0 = out[0];
  assign out$__1 = out[1];
  assign out[0] = in_$foo[0];
  assign out[1] = in_$foo[1];

endmodule
"""
  do_test( a )

def test_struct_packed_array( do_test ):
  class C( BitStruct ):
    def __init__( s, bar=1 ):
      s.bar = Bits32(bar)
  class B( BitStruct ):
    def __init__( s ):
      s.c = [ C() for _ in range(2) ]
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out =  [ OutPort( Bits32 ) for _ in range(2) ]
      s.connect( s.out[0], s.in_.c[0].bar )
      s.connect( s.out[1], s.in_.c[1].bar )
  a = A()
  a._ref_src = \
"""
typedef struct packed {
  logic [31:0] bar;
} C;

typedef struct packed {
  C [1:0] c;
} B;

module A
(
  input logic [0:0] clk,
  input B in_,
  output logic [31:0] out [0:1],
  input logic [0:0] reset
);

  assign out[0] = in_.c[0].bar;
  assign out[1] = in_.c[1].bar;

endmodule
"""
  a._ref_src_yosys = \
"""
module A
(
  input logic [0:0] clk,
  input logic [31:0] in_$c$__0$bar,
  input logic [31:0] in_$c$__1$bar,
  output logic [31:0] out$__0,
  output logic [31:0] out$__1,
  input logic [0:0] reset
);
  logic [31:0] in_$c$bar [0:1];
  logic [31:0] in_$c [0:1];
  logic [63:0] in_;
  logic [31:0] out [0:1];

  assign in_$c$bar[0] = in_$c$__0$bar;
  assign in_$c[0][31:0] = in_$c$__0$bar;
  assign in_$c$bar[1] = in_$c$__1$bar;
  assign in_$c[1][31:0] = in_$c$__1$bar;
  assign in_[63:32] = in_$c$__1$bar;
  assign in_[31:0] = in_$c$__0$bar;
  assign out$__0 = out[0];
  assign out$__1 = out[1];
  assign out[0] = in_$c$bar[0];
  assign out[1] = in_$c$bar[1];

endmodule
"""
  do_test( a )
