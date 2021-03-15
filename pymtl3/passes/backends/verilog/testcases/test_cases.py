"""
=========================================================================
test_cases.py
=========================================================================
Centralized test case repository for the SystemVerilog backend.

Author : Peitian Pan
Date   : Dec 16, 2019
"""
from os.path import dirname
from textwrap import dedent

from pymtl3 import *
from pymtl3.passes.backends.verilog import *
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.testcases import (
    Bits32Foo,
    Bits32x5Foo,
    CaseArrayBits32IfcInUpblkComp,
    CaseBehavioralArraySubCompArrayStructIfcComp,
    CaseBits32ArrayConnectSubCompAttrComp,
    CaseBits32ArraySubCompAttrUpblkComp,
    CaseBits32BitSelUpblkComp,
    CaseBits32ConnectSubCompAttrComp,
    CaseBits32FooInBits32OutComp,
    CaseBits32FooNoArgBehavioralComp,
    CaseBits32FooToBits32Comp,
    CaseBits32SubCompAttrUpblkComp,
    CaseBits32ToBits32FooComp,
    CaseBits32x2ConcatComp,
    CaseBits32x2ConcatConstComp,
    CaseBits32x2ConcatFreeVarComp,
    CaseBits32x2ConcatMixedComp,
    CaseBits32x2ConcatUnpackedSignalComp,
    CaseBits64PartSelUpblkComp,
    CaseBits64SextInComp,
    CaseBits64TruncInComp,
    CaseBits64ZextInComp,
    CaseBitSelOverBitSelComp,
    CaseBitSelOverPartSelComp,
    CaseBoolTmpVarComp,
    CaseChildExplicitModuleName,
    CaseConnectArrayBits32FooIfcComp,
    CaseConnectArrayNestedIfcComp,
    CaseConnectArrayStructAttrToOutComp,
    CaseConnectArraySubCompArrayStructIfcComp,
    CaseConnectBitsConstToOutComp,
    CaseConnectBitSelToOutComp,
    CaseConnectConstStructAttrToOutComp,
    CaseConnectConstToOutComp,
    CaseConnectInToWireComp,
    CaseConnectLiteralStructComp,
    CaseConnectNestedStructPackedArrayComp,
    CaseConnectPassThroughLongNameComp,
    CaseConnectSliceToOutComp,
    CaseConnectValRdyIfcComp,
    CaseConnectValRdyIfcUpblkComp,
    CaseConstStructInstComp,
    CaseDefaultBitsComp,
    CaseElifBranchComp,
    CaseFixedSizeSliceComp,
    CaseForLoopEmptySequenceComp,
    CaseForRangeLowerUpperStepPassThroughComp,
    CaseHeteroCompArrayComp,
    CaseIfBasicComp,
    CaseIfBoolOpInForStmtComp,
    CaseIfDanglingElseInnerComp,
    CaseIfDanglingElseOutterComp,
    CaseIfExpBothImplicitComp,
    CaseIfExpInForStmtComp,
    CaseIfExpUnaryOpInForStmtComp,
    CaseIfTmpVarInForStmtComp,
    CaseInterfaceArrayNonStaticIndexComp,
    CaseIntToBits32FooComp,
    CaseLambdaConnectComp,
    CaseLambdaConnectWithListComp,
    CaseNestedIfComp,
    CaseNestedStructPackedArrayUpblkComp,
    CasePartSelOverBitSelComp,
    CasePartSelOverPartSelComp,
    CasePassThroughComp,
    CasePythonClassAttr,
    CaseReducesInx3OutComp,
    CaseSequentialPassThroughComp,
    CaseSizeCastPaddingStructPort,
    CaseStructPackedArrayUpblkComp,
    CaseStructUnique,
    CaseTmpVarInUpdateffComp,
    CaseTypeBundle,
    CaseVerilogReservedComp,
    NestedStructPackedPlusScalar,
    ThisIsABitStructWithSuperLongName,
    set_attributes,
)
from pymtl3.passes.testcases.test_cases import _check, _set

# Verilog test cases

class Bits32VRegComp( VerilogPlaceholder, Component ):
  def construct( s ):
    s.d = InPort( Bits32 )
    s.q = OutPort( Bits32 )
    s.set_metadata( VerilogPlaceholderPass.src_file, dirname(__file__)+'/VReg.v' )
    s.set_metadata( VerilogPlaceholderPass.top_module, 'VReg' )

class Bits32VRegPassThroughComp( VerilogPlaceholder, Component ):
  def construct( s ):
    s.d = InPort( Bits32 )
    s.q = OutPort( Bits32 )
    s.set_metadata( VerilogPlaceholderPass.src_file, dirname(__file__)+'/VRegPassThrough.v' )
    s.set_metadata( VerilogPlaceholderPass.top_module, 'VRegPassThrough' )
    s.set_metadata( VerilogPlaceholderPass.v_include, [dirname(__file__)] )

class CasePlaceholderTranslationVReg:
  DUT = Bits32VRegComp
  TV_IN = \
  _set( 'd', Bits32, 0 )
  TV_OUT = \
  _check( 'q', Bits32, 1 )
  TV = \
  [
      [  1,  0 ],
      [  2,  1 ],
      [ 42,  2 ],
      [ -1, 42 ],
      [  0, -1 ],
  ]

class CasePlaceholderTranslationRegIncr:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.reg_ = Bits32VRegComp()
      s.reg_.d //= s.in_
      s.out //= lambda: s.reg_.q + Bits32(1)
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits32, 1 )
  TV = \
  [
      [  1,  1 ],
      [  2,  2 ],
      [ 42,  3 ],
      [ -1, 43 ],
      [  0,  0 ],
  ]

class CaseVIncludePopulation:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.reg_ = Bits32VRegPassThroughComp()
      s.reg_.d //= s.in_
      s.reg_.q //= s.out
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits32, 1 )
  TV = \
  [
      [  1,  0 ],
      [  2,  1 ],
      [ 42,  2 ],
      [ -1, 42 ],
      [  0, -1 ],
  ]

class CaseVLibsTranslation:
  class DUT( VerilogPlaceholder, Component ):
    def construct( s ):
      s.d = InPort( Bits32 )
      s.q = OutPort( Bits32 )
      s.set_metadata( VerilogPlaceholderPass.src_file, dirname(__file__)+'/VRegPassThrough.v' )
      s.set_metadata( VerilogPlaceholderPass.top_module, 'VRegPassThrough' )
      s.set_metadata( VerilogPlaceholderPass.v_libs, [dirname(__file__)+'/VReg.v'] )
  TV_IN = \
  _set( 'd', Bits32, 0 )
  TV_OUT = \
  _check( 'q', Bits32, 1 )
  TV = \
  [
      [  1,  0 ],
      [  2,  1 ],
      [ 42,  2 ],
      [ -1, 42 ],
      [  0, -1 ],
  ]

class CaseMultiPlaceholderImport:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.a_reg = Bits32VRegComp()
      s.b_reg = Bits32VRegComp()
      s.a_reg.d //= s.in_
      s.a_reg.q //= s.b_reg.d
      s.b_reg.q //= s.out
  TV_IN  = _set( 'in_', Bits32, 0 )
  TV_OUT = _check( 'out', Bits32, 1 )
  TV = \
  [
      [  1,  0 ],
      [  2,  0 ],
      [ 42,  1 ],
      [ -1,  2 ],
      [  0, 42 ],
      [  0, -1 ],
  ]

class CasePlaceholderTranslationRegIncr:
  class DUT( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      s.reg_ = Bits32VRegComp()
      s.reg_.d //= s.in_
      s.out //= lambda: s.reg_.q + Bits32(1)
  TV_IN = \
  _set( 'in_', Bits32, 0 )
  TV_OUT = \
  _check( 'out', Bits32, 1 )
  TV = \
  [
      [  1,  1 ],
      [  2,  2 ],
      [ 42,  3 ],
      [ -1, 43 ],
      [  0,  0 ],
  ]

CaseSizeCastPaddingStructPort = set_attributes( CaseSizeCastPaddingStructPort,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = 64'( in_ );
        end
    ''',
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [31:0] foo;
        } Bits32Foo__foo_32;

        module DUT_noparam
        (
          input logic [0:0] clk,
          input Bits32Foo__foo_32 in_,
          output logic [63:0] out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = 64'( in_ );
          end

        endmodule
    '''
)

CasePassThroughComp = set_attributes( CasePassThroughComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
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
    '''
)

CaseSequentialPassThroughComp = set_attributes( CaseSequentialPassThroughComp,
    'REF_UPBLK',
    '''\
        always_ff @(posedge clk) begin : upblk
          out <= in_;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
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
    '''
)

CaseConnectPassThroughLongNameComp = set_attributes( CaseConnectPassThroughLongNameComp,
    'REF_PORT',
    '''\
        input logic [0:0] clk,
        input logic [31:0] in_,
        output logic [31:0] out,
        input logic [0:0] reset
    ''',
    'REF_WIRE',
    '''\
    ''',
    'REF_CONN',
    '''\
        assign out = in_;
    ''',
    'REF_SRC',
    '''\
        module DUT__2ae3b6d12e9855d1
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          assign out = in_;

        endmodule
    ''',
    'REF_STRUCT',
    '''\
    ''',
)

CaseLambdaConnectComp = set_attributes( CaseLambdaConnectComp,
    'REF_UPBLK',
    '''\
        always_comb begin : _lambda__s_out
          out = in_ + 32'd42;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          always_comb begin : _lambda__s_out
            out = in_ + 32'd42;
          end

        endmodule
    '''
)

CaseLambdaConnectWithListComp = set_attributes( CaseLambdaConnectWithListComp,
    'REF_UPBLK',
    '''\
        always_comb begin : _lambda__s_out_1_
          out[1'd1] = in_ + 32'd42;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [31:0] out [0:1],
          input logic [0:0] reset
        );

          always_comb begin : _lambda__s_out_1_
            out[1'd1] = in_ + 32'd42;
          end

        endmodule
    '''
)

CaseBits32x2ConcatComp = set_attributes( CaseBits32x2ConcatComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_1, in_2 };
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
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
    '''
)

CaseBits32x2ConcatConstComp = set_attributes( CaseBits32x2ConcatConstComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { 32'd42, 32'd0 };
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [63:0] out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = { 32'd42, 32'd0 };
          end

        endmodule
    '''
)

CaseBits32x2ConcatMixedComp = set_attributes( CaseBits32x2ConcatMixedComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_, 32'd0 };
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
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
    '''
)

CaseBits64SextInComp = set_attributes( CaseBits64SextInComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { { 32 { in_[31] } }, in_ };
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
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
    '''
)

CaseBits64ZextInComp = set_attributes( CaseBits64ZextInComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { { 32 { 1'b0 } }, in_ };
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [63:0] out,
          input logic [0:0] reset
        );

          // @update
          // def upblk():
          //   s.out = zext( s.in_, 64 )

          always_comb begin : upblk
            out = { { 32 { 1'b0 } }, in_ };
          end

        endmodule
    '''
)

CaseBits64TruncInComp = set_attributes( CaseBits64TruncInComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = 8'(in_);
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [7:0] out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = 8'(in_);
          end

        endmodule
    '''
)

CaseBits32x2ConcatFreeVarComp = set_attributes( CaseBits32x2ConcatFreeVarComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_, 1'( __const__STATE_IDLE ) };
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [32:0] out,
          input logic [0:0] reset
        );
          localparam logic [0:0] __const__STATE_IDLE = 1'd0;

          always_comb begin : upblk
            out = { in_, 1'( __const__STATE_IDLE ) };
          end

        endmodule
    '''
)

CaseBits32x2ConcatUnpackedSignalComp = set_attributes( CaseBits32x2ConcatUnpackedSignalComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_[1'd0], in_[1'd1] };
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_ [0:1],
          output logic [63:0] out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = { in_[1'd0], in_[1'd1] };
          end

        endmodule
    '''
)

CaseBits32BitSelUpblkComp = set_attributes( CaseBits32BitSelUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_[5'd1];
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [0:0] out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = in_[5'd1];
          end

        endmodule
    '''
)

CaseBits64PartSelUpblkComp = set_attributes( CaseBits64PartSelUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_[6'd35:6'd4];
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [63:0] in_,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = in_[6'd35:6'd4];
          end

        endmodule
    '''
)

CaseStructUnique = set_attributes( CaseStructUnique,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          ST_A_wire = { 16'd1, 32'd2 };
          ST_B_wire = { 16'd3, 32'd4 };
          out = ST_A_wire.a_bar + ST_B_wire.b_bar;
        end
    ''',
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [15:0] a_foo;
          logic [31:0] a_bar;
        } ST__a_foo_16__a_bar_32;

        typedef struct packed {
          logic [15:0] b_foo;
          logic [31:0] b_bar;
        } ST__b_foo_16__b_bar_32;

        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          ST__a_foo_16__a_bar_32 ST_A_wire;
          ST__b_foo_16__b_bar_32 ST_B_wire;

          always_comb begin : upblk
            ST_A_wire = { 16'd1, 32'd2 };
            ST_B_wire = { 16'd3, 32'd4 };
            out = ST_A_wire.a_bar + ST_B_wire.b_bar;
          end

        endmodule
    '''
)

CasePythonClassAttr = set_attributes( CasePythonClassAttr,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out1 = 32'd42;
          out2 = 32'd1;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out1,
          output logic [31:0] out2,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out1 = 32'd42;
            out2 = 32'd1;
          end

        endmodule
    '''
)

CaseTypeBundle = set_attributes( CaseTypeBundle,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out1 = 32'd42;
          out2 = 32'd1;
          out3 = 32'd1;
        end
    ''',
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [31:0] foo;
        } Bits32Foo__foo_32;

        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out1,
          output Bits32Foo__foo_32 out2,
          output Bits32Foo__foo_32 out3,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out1 = 32'd42;
            out2 = 32'd1;
            out3 = 32'd1;
          end

        endmodule
    '''
)

CaseTmpVarInUpdateffComp = set_attributes( CaseTmpVarInUpdateffComp,
    'REF_UPBLK',
    '''\
        always_ff @(posedge clk) begin : upblk
          if ( ~reset ) begin
            __tmpvar__upblk_val_next = 32'd42;
            out <= __tmpvar__upblk_val_next;
          end
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          logic [31:0] __tmpvar__upblk_val_next;

          always_ff @(posedge clk) begin : upblk
            if ( ~reset ) begin
              __tmpvar__upblk_val_next = 32'd42;
              out <= __tmpvar__upblk_val_next;
            end
          end

        endmodule
    '''
)

CaseBoolTmpVarComp = set_attributes( CaseBoolTmpVarComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          __tmpvar__upblk_matched = in_ == 32'd0;
          if ( __tmpvar__upblk_matched ) begin
            out = 32'd1;
          end
          else
            out = 32'd0;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [31:0] out,
          input logic [0:0] reset
        );
          logic [0:0] __tmpvar__upblk_matched;

          always_comb begin : upblk
            __tmpvar__upblk_matched = in_ == 32'd0;
            if ( __tmpvar__upblk_matched ) begin
              out = 32'd1;
            end
            else
              out = 32'd0;
          end

        endmodule
    '''
)

CaseDefaultBitsComp = set_attributes( CaseDefaultBitsComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = 32'd0;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = 32'd0;
          end

        endmodule
    '''
)


CaseBits32FooToBits32Comp = set_attributes( CaseBits32FooToBits32Comp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_;
        end
    ''',
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [31:0] foo;
        } Bits32Foo__foo_32;

        module DUT_noparam
        (
          input logic [0:0] clk,
          input Bits32Foo__foo_32 in_,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = in_;
          end

        endmodule
    '''
)

CaseBits32ToBits32FooComp = set_attributes( CaseBits32ToBits32FooComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_;
        end
    ''',
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [31:0] foo;
        } Bits32Foo__foo_32;

        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output Bits32Foo__foo_32 out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = in_;
          end

        endmodule
    '''
)

CaseIntToBits32FooComp = set_attributes( CaseIntToBits32FooComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = 32'd42;
        end
    ''',
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [31:0] foo;
        } Bits32Foo__foo_32;

        module DUT_noparam
        (
          input logic [0:0] clk,
          output Bits32Foo__foo_32 out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = 32'd42;
          end

        endmodule
    '''
)

CaseReducesInx3OutComp = set_attributes( CaseReducesInx3OutComp,
    'REF_UPBLK',
    '''\
        always_comb begin : v_reduce
          out = ( ( & in_1 ) & ( | in_2 ) ) | ( ^ in_3 );
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_1,
          input logic [31:0] in_2,
          input logic [31:0] in_3,
          output logic [0:0] out,
          input logic [0:0] reset
        );

          always_comb begin : v_reduce
            out = ( ( & in_1 ) & ( | in_2 ) ) | ( ^ in_3 );
          end

        endmodule
    '''
)

CaseIfBasicComp = set_attributes( CaseIfBasicComp,
    'REF_UPBLK',
    '''\
        always_comb begin : if_basic
          if ( in_[4'd7:4'd0] == 8'd255 ) begin
            out = in_[4'd15:4'd8];
          end
          else
            out = 8'd0;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [15:0] in_,
          output logic [7:0] out,
          input logic [0:0] reset
        );

          always_comb begin : if_basic
            if ( in_[4'd7:4'd0] == 8'd255 ) begin
              out = in_[4'd15:4'd8];
            end
            else
              out = 8'd0;
          end

        endmodule
    '''
)

CaseIfDanglingElseInnerComp = set_attributes( CaseIfDanglingElseInnerComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          if ( 1'd1 ) begin
            if ( 1'd0 ) begin
              out = in_1;
            end
            else
              out = in_2;
          end
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_1,
          input logic [31:0] in_2,
          output logic [31:0] out,
          input logic [0:0] reset
        );

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
    '''
)

CaseIfDanglingElseOutterComp = set_attributes( CaseIfDanglingElseOutterComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          if ( 1'd1 ) begin
            if ( 1'd0 ) begin
              out = in_1;
            end
          end
          else
            out = in_2;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_1,
          input logic [31:0] in_2,
          output logic [31:0] out,
          input logic [0:0] reset
        );

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
    '''
)

CaseElifBranchComp = set_attributes( CaseElifBranchComp,
    'REF_UPBLK',
    '''\
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
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_1,
          input logic [31:0] in_2,
          input logic [31:0] in_3,
          output logic [31:0] out,
          input logic [0:0] reset
        );

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
    '''
)

CaseNestedIfComp = set_attributes( CaseNestedIfComp,
    'REF_UPBLK',
    '''\
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
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_1,
          input logic [31:0] in_2,
          input logic [31:0] in_3,
          output logic [31:0] out,
          input logic [0:0] reset
        );

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
    '''
)

CaseForLoopEmptySequenceComp = set_attributes( CaseForLoopEmptySequenceComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = 4'd15;
          for ( int unsigned i = 1'd0; i < 1'd0; i += 1'd1 )
            out[2'(i)] = 1'd0;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [3:0] out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = 4'd15;
            for ( int unsigned i = 1'd0; i < 1'd0; i += 1'd1 )
              out[2'(i)] = 1'd0;
          end

        endmodule
    '''
)

CaseForRangeLowerUpperStepPassThroughComp = set_attributes( CaseForRangeLowerUpperStepPassThroughComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int unsigned i = 1'd0; i < 3'd5; i += 2'd2 )
            out[3'(i)] = in_[3'(i)];
          for ( int unsigned i = 1'd1; i < 3'd5; i += 2'd2 )
            out[3'(i)] = in_[3'(i)];
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_ [0:4],
          output logic [31:0] out [0:4],
          input logic [0:0] reset
        );

          always_comb begin : upblk
            for ( int unsigned i = 1'd0; i < 3'd5; i += 2'd2 )
              out[3'(i)] = in_[3'(i)];
            for ( int unsigned i = 1'd1; i < 3'd5; i += 2'd2 )
              out[3'(i)] = in_[3'(i)];
          end

        endmodule
    '''
)

CaseIfExpBothImplicitComp = set_attributes( CaseIfExpBothImplicitComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_ ? 32'd1 : 32'd0;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = in_ ? 32'd1 : 32'd0;
          end

        endmodule
    '''
)

CaseIfExpInForStmtComp = set_attributes( CaseIfExpInForStmtComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int unsigned i = 1'd0; i < 3'd5; i += 1'd1 )
            out[3'(i)] = ( 3'(i) == 3'd1 ) ? in_[3'(i)] : in_[3'd0];
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_ [0:4],
          output logic [31:0] out [0:4],
          input logic [0:0] reset
        );

          always_comb begin : upblk
            for ( int unsigned i = 1'd0; i < 3'd5; i += 1'd1 )
              out[3'(i)] = ( 3'(i) == 3'd1 ) ? in_[3'(i)] : in_[3'd0];
          end

        endmodule
    '''
)

CaseIfExpUnaryOpInForStmtComp = set_attributes( CaseIfExpUnaryOpInForStmtComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int unsigned i = 0; i < 5; i += 1 )
            out[i] = ( i == 1 ) ? ~in_[i] : in_[0];
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_ [0:4],
          output logic [31:0] out [0:4],
          input logic [0:0] reset
        );

          always_comb begin : upblk
            for ( int unsigned i = 0; i < 5; i += 1 )
              out[i] = ( i == 1 ) ? ~in_[i] : in_[0];
          end

        endmodule
    '''
)

CaseIfBoolOpInForStmtComp = set_attributes( CaseIfBoolOpInForStmtComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int unsigned i = 1'd0; i < 3'd5; i += 1'd1 )
            if ( ( in_[3'(i)] != 32'd0 ) & ( ( 3'(i) < 3'd4 ) ? in_[3'(i) + 3'd1] != 32'd0 : in_[3'd4] != 32'd0 ) ) begin
              out[3'(i)] = in_[3'(i)];
            end
            else
              out[3'(i)] = 32'd0;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_ [0:4],
          output logic [31:0] out [0:4],
          input logic [0:0] reset
        );

          always_comb begin : upblk
            for ( int unsigned i = 1'd0; i < 3'd5; i += 1'd1 )
              if ( ( in_[3'(i)] != 32'd0 ) & ( ( 3'(i) < 3'd4 ) ? in_[3'(i) + 3'd1] != 32'd0 : in_[3'd4] != 32'd0 ) ) begin
                out[3'(i)] = in_[3'(i)];
              end
              else
                out[3'(i)] = 32'd0;
          end

        endmodule
    '''
)

CaseIfTmpVarInForStmtComp = set_attributes( CaseIfTmpVarInForStmtComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int unsigned i = 1'd0; i < 3'd5; i += 1'd1 ) begin
            if ( ( in_[3'(i)] != 32'd0 ) & ( ( 3'(i) < 3'd4 ) ? in_[3'(i) + 3'd1] != 32'd0 : in_[3'd4] != 32'd0 ) ) begin
              __tmpvar__upblk_tmpvar = in_[3'(i)];
            end
            else
              __tmpvar__upblk_tmpvar = 32'd0;
            out[3'(i)] = __tmpvar__upblk_tmpvar;
          end
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_ [0:4],
          output logic [31:0] out [0:4],
          input logic [0:0] reset
        );
          logic [31:0] __tmpvar__upblk_tmpvar;

          always_comb begin : upblk
            for ( int unsigned i = 1'd0; i < 3'd5; i += 1'd1 ) begin
              if ( ( in_[3'(i)] != 32'd0 ) & ( ( 3'(i) < 3'd4 ) ? in_[3'(i) + 3'd1] != 32'd0 : in_[3'd4] != 32'd0 ) ) begin
                __tmpvar__upblk_tmpvar = in_[3'(i)];
              end
              else
                __tmpvar__upblk_tmpvar = 32'd0;
              out[3'(i)] = __tmpvar__upblk_tmpvar;
            end
          end

        endmodule
    '''
)

CaseInterfaceArrayNonStaticIndexComp = set_attributes( CaseInterfaceArrayNonStaticIndexComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in___foo[in___foo[1'd0][5'd0]];
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset,
          input logic [31:0] in___foo [0:1]
        );

          always_comb begin : upblk
            out = in___foo[in___foo[1'd0][5'd0]];
          end

        endmodule
    '''
)

CaseFixedSizeSliceComp = set_attributes( CaseFixedSizeSliceComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int unsigned i = 1'd0; i < 2'd2; i += 1'd1 )
            out[1'(i)] = in_[4'(i) * 4'd8 +: 8];
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [15:0] in_,
          output logic [7:0] out [0:1],
          input logic [0:0] reset
        );

          always_comb begin : upblk
            for ( int unsigned i = 1'd0; i < 2'd2; i += 1'd1 )
              out[1'(i)] = in_[4'(i) * 4'd8 +: 8];
          end

        endmodule
    '''
)

CaseBits32FooInBits32OutComp = set_attributes( CaseBits32FooInBits32OutComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_.foo;
        end
    ''',
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [31:0] foo;
        } Bits32Foo__foo_32;

        module DUT_noparam
        (
          input logic [0:0] clk,
          input Bits32Foo__foo_32 in_,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = in_.foo;
          end

        endmodule
    '''
)

CaseConstStructInstComp = set_attributes( CaseConstStructInstComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = 32'd0;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = 32'd0;
          end

        endmodule
    '''
)

CaseStructPackedArrayUpblkComp = set_attributes( CaseStructPackedArrayUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_.foo[3'd0], in_.foo[3'd1], in_.foo[3'd2] };
        end
    ''',
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [4:0][31:0] foo;
        } Bits32x5Foo__foo_32x5;

        module DUT_noparam
        (
          input logic [0:0] clk,
          input Bits32x5Foo__foo_32x5 in_,
          output logic [95:0] out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = { in_.foo[3'd0], in_.foo[3'd1], in_.foo[3'd2] };
          end

        endmodule
    '''
)

CaseNestedStructPackedArrayUpblkComp = set_attributes( CaseNestedStructPackedArrayUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_.bar[1'd0], in_.woo.foo, in_.foo };
        end
    ''',
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [31:0] foo;
        } Bits32Foo__foo_32;

        typedef struct packed {
          logic [31:0] foo;
          logic [1:0][31:0] bar;
          Bits32Foo__foo_32 woo;
        } NestedStructPackedPlusScalar__c467caf2a4dfbfb2;

        module DUT_noparam
        (
          input logic [0:0] clk,
          input NestedStructPackedPlusScalar__c467caf2a4dfbfb2 in_,
          output logic [95:0] out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = { in_.bar[1'd0], in_.woo.foo, in_.foo };
          end

        endmodule
    '''
)

CaseConnectValRdyIfcUpblkComp = set_attributes( CaseConnectValRdyIfcUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out__val = in___val;
          out__msg = in___msg;
          in___rdy = out__rdy;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
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

          always_comb begin : upblk
            out__val = in___val;
            out__msg = in___msg;
            in___rdy = out__rdy;
          end

        endmodule
    '''
)

CaseArrayBits32IfcInUpblkComp = set_attributes( CaseArrayBits32IfcInUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in___foo[3'd1];
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset,
          input logic [31:0] in___foo [0:4]
        );

          always_comb begin : upblk
            out = in___foo[3'd1];
          end

        endmodule
    '''
)

CaseBits32SubCompAttrUpblkComp = set_attributes( CaseBits32SubCompAttrUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = b__out;
        end
    ''',
    'REF_SRC',
    '''\
        module Bits32OutDrivenComp_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          assign out = 32'd42;

        endmodule

        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );
          logic [0:0] b__clk;
          logic [31:0] b__out;
          logic [0:0] b__reset;

          Bits32OutDrivenComp_noparam b
          (
            .clk( b__clk ),
            .out( b__out ),
            .reset( b__reset )
          );

          always_comb begin : upblk
            out = b__out;
          end

          assign b__clk = clk;
          assign b__reset = reset;

        endmodule
    '''
)

CaseBits32ArraySubCompAttrUpblkComp = set_attributes( CaseBits32ArraySubCompAttrUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = b__out[3'd1];
        end
    ''',
    'REF_SRC',
    '''\
        module Bits32OutDrivenComp_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          assign out = 32'd42;

        endmodule

        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          logic [0:0] b__clk [0:4] ;
          logic [31:0] b__out [0:4] ;
          logic [0:0] b__reset [0:4] ;

          Bits32OutDrivenComp_noparam b__0
          (
            .clk( b__clk[0] ),
            .out( b__out[0] ),
            .reset( b__reset[0] )
          );

          Bits32OutDrivenComp_noparam b__1
          (
            .clk( b__clk[1] ),
            .out( b__out[1] ),
            .reset( b__reset[1] )
          );

          Bits32OutDrivenComp_noparam b__2
          (
            .clk( b__clk[2] ),
            .out( b__out[2] ),
            .reset( b__reset[2] )
          );

          Bits32OutDrivenComp_noparam b__3
          (
            .clk( b__clk[3] ),
            .out( b__out[3] ),
            .reset( b__reset[3] )
          );

          Bits32OutDrivenComp_noparam b__4
          (
            .clk( b__clk[4] ),
            .out( b__out[4] ),
            .reset( b__reset[4] )
          );

          always_comb begin : upblk
            out = b__out[3'd1];
          end

          assign b__clk[0] = clk;
          assign b__reset[0] = reset;
          assign b__clk[1] = clk;
          assign b__reset[1] = reset;
          assign b__clk[2] = clk;
          assign b__reset[2] = reset;
          assign b__clk[3] = clk;
          assign b__reset[3] = reset;
          assign b__clk[4] = clk;
          assign b__reset[4] = reset;

        endmodule
    '''
)

CaseConnectInToWireComp = set_attributes( CaseConnectInToWireComp,
    'REF_PORT',
    '''\
        input logic [0:0] clk,
        input logic [31:0] in_ [0:4],
        output logic [31:0] out,
        input logic [0:0] reset
    ''',
    'REF_WIRE',
    '''\
        logic [31:0] wire_ [0:4];
    ''',
    'REF_CONST',
    '',
    'REF_CONN',
    '''\
        assign out = wire_[2];
        assign wire_[0] = in_[0];
        assign wire_[1] = in_[1];
        assign wire_[2] = in_[2];
        assign wire_[3] = in_[3];
        assign wire_[4] = in_[4];
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_ [0:4],
          output logic [31:0] out,
          input logic [0:0] reset
        );
          logic [31:0] wire_ [0:4];

          assign out = wire_[2];
          assign wire_[0] = in_[0];
          assign wire_[1] = in_[1];
          assign wire_[2] = in_[2];
          assign wire_[3] = in_[3];
          assign wire_[4] = in_[4];

        endmodule
    '''
)

CaseConnectBitsConstToOutComp = set_attributes( CaseConnectBitsConstToOutComp,
    'REF_PORT',
    '''\
        input logic [0:0] clk,
        output logic [31:0] out,
        input logic [0:0] reset
    ''',
    'REF_WIRE',
    '',
    'REF_CONST',
    '',
    'REF_CONN',
    '''\
        assign out = 32'd0;
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          assign out = 32'd0;

        endmodule
    '''
)

CaseConnectConstToOutComp = set_attributes( CaseConnectConstToOutComp,
    'REF_PORT',
    '''\
        input logic [0:0] clk,
        output logic [31:0] out,
        input logic [0:0] reset
    ''',
    'REF_WIRE',
    '',
    'REF_CONST',
    '''\
        localparam logic [5:0] const_ [0:4] = '{ 6'd42, 6'd42, 6'd42, 6'd42, 6'd42 };
    ''',
    'REF_CONN',
    '''\
        assign out = 32'd42;
    ''',
    'REF_SRC',
    # const_ is not used in upblks so will be optimized away
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          assign out = 32'd42;

        endmodule
    '''
)

CaseConnectBitSelToOutComp = set_attributes( CaseConnectBitSelToOutComp,
    'REF_PORT',
    '''\
        input logic [0:0] clk,
        input logic [31:0] in_,
        output logic [0:0] out,
        input logic [0:0] reset
    ''',
    'REF_WIRE',
    '',
    'REF_CONST',
    '',
    'REF_CONN',
    '''\
        assign out = in_[0:0];
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [0:0] out,
          input logic [0:0] reset
        );

          assign out = in_[0:0];

        endmodule
    '''
)

CaseConnectSliceToOutComp = set_attributes( CaseConnectSliceToOutComp,
    'REF_PORT',
    '''\
        input logic [0:0] clk,
        input logic [31:0] in_,
        output logic [3:0] out,
        input logic [0:0] reset
    ''',
    'REF_WIRE',
    '',
    'REF_CONST',
    '',
    'REF_CONN',
    '''\
        assign out = in_[7:4];
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [3:0] out,
          input logic [0:0] reset
        );

          assign out = in_[7:4];

        endmodule
    '''
)

CaseBitSelOverBitSelComp = set_attributes( CaseBitSelOverBitSelComp,
    'REF_PORT',
    '''\
        input logic [0:0] clk,
        input logic [31:0] in_,
        output logic [0:0] out,
        input logic [0:0] reset
    ''',
    'REF_WIRE',
    '',
    'REF_CONST',
    '',
    'REF_CONN',
    '''\
        assign out = in_[1:1];
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [0:0] out,
          input logic [0:0] reset
        );

          assign out = in_[1:1];

        endmodule
    '''
)

CaseBitSelOverPartSelComp = set_attributes( CaseBitSelOverPartSelComp,
    'REF_PORT',
    '''\
        input logic [0:0] clk,
        input logic [31:0] in_,
        output logic [0:0] out,
        input logic [0:0] reset
    ''',
    'REF_WIRE',
    '',
    'REF_CONST',
    '',
    'REF_CONN',
    '''\
        assign out = in_[0:0];
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [0:0] out,
          input logic [0:0] reset
        );

          assign out = in_[0:0];

        endmodule
    '''
)

CasePartSelOverBitSelComp = set_attributes( CasePartSelOverBitSelComp,
    'REF_PORT',
    '''\
        input logic [0:0] clk,
        input logic [31:0] in_,
        output logic [0:0] out,
        input logic [0:0] reset
    ''',
    'REF_WIRE',
    '',
    'REF_CONST',
    '',
    'REF_CONN',
    '''\
        assign out = in_[1:1];
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [0:0] out,
          input logic [0:0] reset
        );

          assign out = in_[1:1];

        endmodule
    '''
)

CasePartSelOverPartSelComp = set_attributes( CasePartSelOverPartSelComp,
    'REF_PORT',
    '''\
        input logic [0:0] clk,
        input logic [31:0] in_,
        output logic [0:0] out,
        input logic [0:0] reset
    ''',
    'REF_WIRE',
    '',
    'REF_CONST',
    '',
    'REF_CONN',
    '''\
        assign out = in_[0:0];
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [0:0] out,
          input logic [0:0] reset
        );

          assign out = in_[0:0];

        endmodule
    '''
)

CaseConnectConstStructAttrToOutComp = set_attributes( CaseConnectConstStructAttrToOutComp,
    'REF_PORT',
    '''\
        input logic [0:0] clk,
        output logic [31:0] out,
        input logic [0:0] reset
    ''',
    'REF_WIRE',
    '',
    'REF_CONN',
    '''\
        assign out = 32'd42;
    ''',
    'REF_STRUCT',
    (
        rdt.Struct(Bits32Foo, {'foo':rdt.Vector(32)}),
        dedent('''\
                  typedef struct packed {
                    logic [31:0] foo;
                  } Bits32Foo__foo_32;
               ''')
    ),
    'REF_SRC',
    # struct definition will be eliminated because it's not used
    # in an upblk
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          assign out = 32'd42;

        endmodule
    '''
)

CaseConnectLiteralStructComp = set_attributes( CaseConnectLiteralStructComp,
    'REF_PORT',
    '''\
        input logic [0:0] clk,
        output NestedStructPackedPlusScalar__c467caf2a4dfbfb2 out,
        input logic [0:0] reset
    ''',
    'REF_WIRE',
    '',
    'REF_CONN',
    '''\
        assign out = { 32'd42, { { 32'd2, 32'd1 } }, { 32'd3 } };
    ''',
    'REF_STRUCT',
    (
        rdt.Struct(NestedStructPackedPlusScalar, {
          'foo':rdt.Vector(32),
          'bar':rdt.PackedArray([2], rdt.Vector(32)),
          'woo':rdt.Struct(Bits32Foo, {'foo':rdt.Vector(32)}),
        }),
        dedent('''\
                  typedef struct packed {
                    logic [31:0] foo;
                    logic [1:0][31:0] bar;
                    Bits32Foo__foo_32 woo;
                  } NestedStructPackedPlusScalar__c467caf2a4dfbfb2;
               ''')
    ),
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [31:0] foo;
        } Bits32Foo__foo_32;

        typedef struct packed {
          logic [31:0] foo;
          logic [1:0][31:0] bar;
          Bits32Foo__foo_32 woo;
        } NestedStructPackedPlusScalar__c467caf2a4dfbfb2;

        module DUT_noparam
        (
          input logic [0:0] clk,
          output NestedStructPackedPlusScalar__c467caf2a4dfbfb2 out,
          input logic [0:0] reset
        );

          assign out = { 32'd42, { { 32'd2, 32'd1 } }, { 32'd3 } };

        endmodule
    '''
)

CaseConnectArrayStructAttrToOutComp = set_attributes( CaseConnectArrayStructAttrToOutComp,
    'REF_PORT',
    '''\
        input logic [0:0] clk,
        input Bits32x5Foo__foo_32x5 in_,
        output logic [31:0] out,
        input logic [0:0] reset
    ''',
    'REF_WIRE',
    '',
    'REF_CONN',
    '''\
        assign out = in_.foo[1];
    ''',
    'REF_STRUCT',
    (
        rdt.Struct(Bits32x5Foo, {'foo':rdt.PackedArray([5], rdt.Vector(32))}),
        dedent('''\
                  typedef struct packed {
                    logic [4:0][31:0] foo;
                  } Bits32x5Foo__foo_32x5;
               ''')
    ),
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [4:0][31:0] foo;
        } Bits32x5Foo__foo_32x5;

        module DUT_noparam
        (
          input logic [0:0] clk,
          input Bits32x5Foo__foo_32x5 in_,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          assign out = in_.foo[1];

        endmodule
    '''
)

CaseConnectNestedStructPackedArrayComp = set_attributes( CaseConnectNestedStructPackedArrayComp,
    'REF_PORT',
    '''\
        input logic [0:0] clk,
        input NestedStructPackedPlusScalar__c467caf2a4dfbfb2 in_,
        output logic [95:0] out,
        input logic [0:0] reset
    ''',
    'REF_WIRE',
    '',
    'REF_CONN',
    '''\
        assign out[31:0] = in_.foo;
        assign out[63:32] = in_.woo.foo;
        assign out[95:64] = in_.bar[0];
    ''',
    'REF_STRUCT',
    (
        rdt.Struct(NestedStructPackedPlusScalar, {
          'foo':rdt.Vector(32),
          'bar':rdt.PackedArray([2], rdt.Vector(32)),
          'woo':rdt.Struct(Bits32Foo, {'foo':rdt.Vector(32)}),
        }),
        dedent('''\
                  typedef struct packed {
                    logic [31:0] foo;
                    logic [1:0][31:0] bar;
                    Bits32Foo__foo_32 woo;
                  } NestedStructPackedPlusScalar__c467caf2a4dfbfb2;
               ''')
    ),
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [31:0] foo;
        } Bits32Foo__foo_32;

        typedef struct packed {
          logic [31:0] foo;
          logic [1:0][31:0] bar;
          Bits32Foo__foo_32 woo;
        } NestedStructPackedPlusScalar__c467caf2a4dfbfb2;

        module DUT_noparam
        (
          input logic [0:0] clk,
          input NestedStructPackedPlusScalar__c467caf2a4dfbfb2 in_,
          output logic [95:0] out,
          input logic [0:0] reset
        );

          assign out[31:0] = in_.foo;
          assign out[63:32] = in_.woo.foo;
          assign out[95:64] = in_.bar[0];

        endmodule
    '''
)

CaseConnectValRdyIfcComp = set_attributes( CaseConnectValRdyIfcComp,
    'REF_IFC',
    '''\
        input  logic [31:0] in___msg,
        output logic [0:0]  in___rdy,
        input  logic [0:0]  in___val,
        output logic [31:0] out__msg,
        input  logic [0:0]  out__rdy,
        output logic [0:0]  out__val
    ''',
    'REF_CONN',
    '''\
        assign out__msg = in___msg;
        assign in___rdy = out__rdy;
        assign out__val = in___val;
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
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
    '''
)

CaseConnectArrayBits32FooIfcComp = set_attributes( CaseConnectArrayBits32FooIfcComp,
    'REF_IFC',
    '''\
        input Bits32Foo__foo_32  in___foo [0:1],
        output Bits32Foo__foo_32  out__foo [0:1]
    ''',
    'REF_CONN',
    '''\
        assign out__foo[0] = in___foo[0];
        assign out__foo[1] = in___foo[1];
    ''',
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [31:0] foo;
        } Bits32Foo__foo_32;

        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [0:0] reset,
          input Bits32Foo__foo_32 in___foo [0:1],
          output Bits32Foo__foo_32 out__foo [0:1]
        );

          assign out__foo[0] = in___foo[0];
          assign out__foo[1] = in___foo[1];

        endmodule
    '''
)

CaseConnectArrayNestedIfcComp = set_attributes( CaseConnectArrayNestedIfcComp,
    'REF_IFC',
    '''\
        input  logic [0:0]  in___ctrl_foo [0:1],
        input  logic [31:0] in___memifc__msg [0:1],
        output logic [0:0]  in___memifc__rdy [0:1],
        input  logic [0:0]  in___memifc__val [0:1],

        output  logic [0:0]  out__ctrl_foo [0:1],
        output  logic [31:0] out__memifc__msg [0:1],
        input   logic [0:0]  out__memifc__rdy [0:1],
        output  logic [0:0]  out__memifc__val [0:1]
    ''',
    'REF_CONN',
    '''\
        assign out__ctrl_foo[0] = in___ctrl_foo[0];
        assign out__memifc__msg[0] = in___memifc__msg[0];
        assign in___memifc__rdy[0] = out__memifc__rdy[0];
        assign out__memifc__val[0] = in___memifc__val[0];
        assign out__ctrl_foo[1] = in___ctrl_foo[1];
        assign out__memifc__msg[1] = in___memifc__msg[1];
        assign in___memifc__rdy[1] = out__memifc__rdy[1];
        assign out__memifc__val[1] = in___memifc__val[1];
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [0:0] reset,
          input logic [0:0] in___ctrl_foo [0:1],
          input logic [31:0] in___memifc__msg [0:1],
          output logic [0:0] in___memifc__rdy [0:1],
          input logic [0:0] in___memifc__val [0:1],
          output logic [0:0] out__ctrl_foo [0:1],
          output logic [31:0] out__memifc__msg [0:1],
          input logic [0:0] out__memifc__rdy [0:1],
          output logic [0:0] out__memifc__val [0:1]
        );

          assign out__ctrl_foo[0] = in___ctrl_foo[0];
          assign out__memifc__msg[0] = in___memifc__msg[0];
          assign in___memifc__rdy[0] = out__memifc__rdy[0];
          assign out__memifc__val[0] = in___memifc__val[0];
          assign out__ctrl_foo[1] = in___ctrl_foo[1];
          assign out__memifc__msg[1] = in___memifc__msg[1];
          assign in___memifc__rdy[1] = out__memifc__rdy[1];
          assign out__memifc__val[1] = in___memifc__val[1];

        endmodule
    '''
)

CaseBits32ConnectSubCompAttrComp = set_attributes( CaseBits32ConnectSubCompAttrComp,
    'REF_COMP',
    '''\
        logic [0:0] b__clk;
        logic [31:0] b__out;
        logic [0:0] b__reset;

        Bits32OutDrivenComp_noparam b
        (
          .clk( b__clk ),
          .out( b__out ),
          .reset( b__reset )
        );
    ''',
    'REF_SRC',
    '''\
        module Bits32OutDrivenComp_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          assign out = 32'd42;

        endmodule

        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );
          logic [0:0] b__clk;
          logic [31:0] b__out;
          logic [0:0] b__reset;

          Bits32OutDrivenComp_noparam b
          (
            .clk( b__clk ),
            .out( b__out ),
            .reset( b__reset )
          );

          assign b__clk = clk;
          assign b__reset = reset;
          assign out = b__out;

        endmodule
    '''
)

CaseConnectArraySubCompArrayStructIfcComp = set_attributes( CaseConnectArraySubCompArrayStructIfcComp,
    'REF_COMP',
    '''\
      logic [0:0] b__clk [0:0] ;
      logic [31:0] b__out [0:0] ;
      logic [0:0] b__reset [0:0] ;
      Bits32Foo__foo_32 b__ifc__foo [0:0][0:0][0:0] ;

      Bits32ArrayStructIfcComp_noparam b__0
      (
        .clk( b__clk[0] ),
        .out( b__out[0] ),
        .reset( b__reset[0] ),
        .ifc__foo( b__ifc__foo[0] )
      );
    ''',
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [31:0] foo ;
        } Bits32Foo__foo_32;

        module Bits32ArrayStructIfcComp_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset,
          input Bits32Foo__foo_32 ifc__foo [0:0][0:0]
        );

          assign out = ifc__foo[0][0].foo;

        endmodule

        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          logic [0:0] b__clk [0:0] ;
          logic [31:0] b__out [0:0] ;
          logic [0:0] b__reset [0:0] ;
          Bits32Foo__foo_32 b__ifc__foo [0:0][0:0][0:0] ;

          Bits32ArrayStructIfcComp_noparam b__0
          (
            .clk( b__clk[0] ),
            .out( b__out[0] ),
            .reset( b__reset[0] ),
            .ifc__foo( b__ifc__foo[0] )
          );

          assign b__clk[0] = clk;
          assign b__reset[0] = reset;
          assign b__ifc__foo[0][0][0].foo = in_;
          assign out = b__out[0];

        endmodule
    '''
)

CaseBits32ArrayConnectSubCompAttrComp = set_attributes( CaseBits32ArrayConnectSubCompAttrComp,
    'REF_COMP',
    '''\
      logic [0:0] b__clk [0:4] ;
      logic [31:0] b__out [0:4] ;
      logic [0:0] b__reset [0:4] ;

      Bits32OutDrivenComp_noparam b__0
      (
        .clk( b__clk[0] ),
        .out( b__out[0] ),
        .reset( b__reset[0] )
      );

      Bits32OutDrivenComp_noparam b__1
      (
        .clk( b__clk[1] ),
        .out( b__out[1] ),
        .reset( b__reset[1] )
      );

      Bits32OutDrivenComp_noparam b__2
      (
        .clk( b__clk[2] ),
        .out( b__out[2] ),
        .reset( b__reset[2] )
      );

      Bits32OutDrivenComp_noparam b__3
      (
        .clk( b__clk[3] ),
        .out( b__out[3] ),
        .reset( b__reset[3] )
      );

      Bits32OutDrivenComp_noparam b__4
      (
        .clk( b__clk[4] ),
        .out( b__out[4] ),
        .reset( b__reset[4] )
      );
    ''',
    'REF_SRC',
    '''\
        module Bits32OutDrivenComp_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          assign out = 32'd42;

        endmodule

        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          logic [0:0] b__clk [0:4] ;
          logic [31:0] b__out [0:4] ;
          logic [0:0] b__reset [0:4] ;

          Bits32OutDrivenComp_noparam b__0
          (
            .clk( b__clk[0] ),
            .out( b__out[0] ),
            .reset( b__reset[0] )
          );

          Bits32OutDrivenComp_noparam b__1
          (
            .clk( b__clk[1] ),
            .out( b__out[1] ),
            .reset( b__reset[1] )
          );

          Bits32OutDrivenComp_noparam b__2
          (
            .clk( b__clk[2] ),
            .out( b__out[2] ),
            .reset( b__reset[2] )
          );

          Bits32OutDrivenComp_noparam b__3
          (
            .clk( b__clk[3] ),
            .out( b__out[3] ),
            .reset( b__reset[3] )
          );

          Bits32OutDrivenComp_noparam b__4
          (
            .clk( b__clk[4] ),
            .out( b__out[4] ),
            .reset( b__reset[4] )
          );

          assign b__clk[0] = clk;
          assign b__reset[0] = reset;
          assign b__clk[1] = clk;
          assign b__reset[1] = reset;
          assign b__clk[2] = clk;
          assign b__reset[2] = reset;
          assign b__clk[3] = clk;
          assign b__reset[3] = reset;
          assign b__clk[4] = clk;
          assign b__reset[4] = reset;
          assign out = b__out[1];

        endmodule
    '''
)

CasePlaceholderTranslationVReg = set_attributes( CasePlaceholderTranslationVReg,
    'REF_PORT',
    '''\
        input logic [0:0] clk,
        output logic [31:0] d,
        input logic [31:0] q,
        input logic [0:0] reset
    ''',
    'REF_WIRE',
    '''\
    ''',
    'REF_CONST',
    '''\
    ''',
    'REF_CONN',
    '''\
    ''',
    'REF_PLACEHOLDER_WRAPPER',
    '''\
        // This is a top-level module that wraps a parametrized module
        // This file is generated by PyMTL SystemVerilog import pass
        module placeholder_VReg
        (
          input logic [1-1:0] clk,
          output logic [32-1:0] d,
          input logic [32-1:0] q,
          input logic [1-1:0] reset
        );
          VReg
          #(
          ) v
          (
            .clk( clk ),
            .d( d ),
            .q( q ),
            .reset( reset )
          );
        endmodule
    ''',
    'REF_PLACEHOLDER_DEPENDENCY',
    '''\
        `line 1 "VReg.v" 0
        module VReg(
          input  logic          clk,
          input  logic          reset,
          output logic [32-1:0] q,
          input  logic [32-1:0] d
        );
          always_ff @(posedge clk) begin
            q <= d;
          end

        endmodule
    ''',
    'REF_SRC',
    '''\
        // PyMTL Placeholder Bits32VRegComp Definition

        // Here are the modules that Bits32VRegComp depends on
        `line 1 "VReg.v" 0
        module VReg(
          input  logic          clk,
          input  logic          reset,
          output logic [32-1:0] q,
          input  logic [32-1:0] d
        );
          always_ff @(posedge clk) begin
            q <= d;
          end

        endmodule

        // Here is the wrapper of the Verilog module backing the
        // placeholder
        module placeholder_VReg
        (
          input logic [1-1:0] clk,
          output logic [32-1:0] d,
          input logic [32-1:0] q,
          input logic [1-1:0] reset
        );
          VReg
          #(
          ) v
          (
            .clk( clk ),
            .d( d ),
            .q( q ),
            .reset( reset )
          );
        endmodule
    ''',
)

CasePlaceholderTranslationRegIncr = set_attributes( CasePlaceholderTranslationRegIncr,
    'REF_PORT',
    '''\
    ''',
    'REF_WIRE',
    '''\
    ''',
    'REF_CONST',
    '''\
    ''',
    'REF_CONN',
    '''\
    ''',
    'REF_PLACEHOLDER_WRAPPER',
    '''\
    ''',
    'REF_PLACEHOLDER_DEPENDENCY',
    '''\
    ''',
)

CaseHeteroCompArrayComp = set_attributes( CaseHeteroCompArrayComp,
    'REF_COMP',
    '''\
        logic [0:0] comps__clk [0:1] ;
        logic [31:0] comps__in_ [0:1] ;
        logic [31:0] comps__out [0:1] ;
        logic [0:0] comps__reset [0:1] ;

        Bits32DummyFooComp_noparam comps__0
        (
          .clk( comps__clk[0] ),
          .in_( comps__in_[0] ),
          .out( comps__out[0] ),
          .reset( comps__reset[0] )
        );

        Bits32DummyBarComp_noparam comps__1
        (
          .clk( comps__clk[1] ),
          .in_( comps__in_[1] ),
          .out( comps__out[1] ),
          .reset( comps__reset[1] )
        );
    ''',
    'REF_SRC',
    '''\
        module Bits32DummyFooComp_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [31:0] out,
          input logic [0:0] reset
        );
          assign out = in_;
        endmodule

        module Bits32DummyBarComp_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [31:0] out,
          input logic [0:0] reset
        );
          always_comb begin : upblk
            out = in_ + 32'd42;
          end
        endmodule

        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_1,
          input logic [31:0] in_2,
          output logic [31:0] out_1,
          output logic [31:0] out_2,
          input logic [0:0] reset
        );
          logic [0:0] comps__clk [0:1] ;
          logic [31:0] comps__in_ [0:1] ;
          logic [31:0] comps__out [0:1] ;
          logic [0:0] comps__reset [0:1] ;

          Bits32DummyFooComp_noparam comps__0
          (
            .clk( comps__clk[0] ),
            .in_( comps__in_[0] ),
            .out( comps__out[0] ),
            .reset( comps__reset[0] )
          );

          Bits32DummyBarComp_noparam comps__1
          (
            .clk( comps__clk[1] ),
            .in_( comps__in_[1] ),
            .out( comps__out[1] ),
            .reset( comps__reset[1] )
          );

          assign comps__clk[0] = clk;
          assign comps__reset[0] = reset;
          assign comps__clk[1] = clk;
          assign comps__reset[1] = reset;
          assign comps__in_[0] = in_1;
          assign comps__in_[1] = in_2;
          assign out_1 = comps__out[0];
          assign out_2 = comps__out[1];

        endmodule
    '''
)

CaseChildExplicitModuleName = set_attributes( CaseChildExplicitModuleName,
    'REF_COMP',
    '''\
        logic [0:0] child__clk ;
        logic [31:0] child__in_ ;
        logic [0:0] child__reset ;

        NewChildDUTName child
        (
          .clk( child__clk ),
          .in_( child__in_ ),
          .reset( child__reset )
        );
    ''',
)

CaseBehavioralArraySubCompArrayStructIfcComp = set_attributes( CaseBehavioralArraySubCompArrayStructIfcComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int unsigned i = 1'd0; i < 2'd2; i += 1'd1 )
            for ( int unsigned j = 1'd0; j < 1'd1; j += 1'd1 )
              b__ifc__foo[1'(i)][1'(j)][1'd0].foo = in_;
          out = b__out[1'd1];
        end
    ''',
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [31:0] foo ;
        } Bits32Foo__foo_32;

        module Bits32ArrayStructIfcComp_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out,
          input logic [0:0] reset,
          input Bits32Foo__foo_32 ifc__foo [0:0][0:0]
        );

          assign out = ifc__foo[0][0].foo;

        endmodule

        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [31:0] out,
          input logic [0:0] reset
        );
          logic [0:0] b__clk [0:1] ;
          logic [31:0] b__out [0:1] ;
          logic [0:0] b__reset [0:1] ;
          Bits32Foo__foo_32 b__ifc__foo [0:1][0:0][0:0] ;

          Bits32ArrayStructIfcComp_noparam b__0
          (
            .clk( b__clk[0] ),
            .out( b__out[0] ),
            .reset( b__reset[0] ),
            .ifc__foo( b__ifc__foo[0] )
          );

          Bits32ArrayStructIfcComp_noparam b__1
          (
            .clk( b__clk[1] ),
            .out( b__out[1] ),
            .reset( b__reset[1] ),
            .ifc__foo( b__ifc__foo[1] )
          );

          always_comb begin : upblk
            for ( int unsigned i = 1'd0; i < 2'd2; i += 1'd1 )
              for ( int unsigned j = 1'd0; j < 1'd1; j += 1'd1 )
                b__ifc__foo[1'(i)][1'(j)][1'd0].foo = in_;
            out = b__out[1'd1];
          end

          assign b__clk[0] = clk;
          assign b__reset[0] = reset;
          assign b__clk[1] = clk;
          assign b__reset[1] = reset;

        endmodule
    '''
)

CaseBits32FooNoArgBehavioralComp = set_attributes( CaseBits32FooNoArgBehavioralComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = 32'd0;
        end
    ''',
    'REF_SRC',
    '''\
        typedef struct packed {
          logic [31:0] foo ;
        } Bits32Foo__foo_32;

        module DUT_noparam
        (
          input logic [0:0] clk,
          output Bits32Foo__foo_32 out,
          input logic [0:0] reset
        );

          always_comb begin : upblk
            out = 32'd0;
          end

        endmodule
    '''
)
