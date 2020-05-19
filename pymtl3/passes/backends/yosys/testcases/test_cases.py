"""
=========================================================================
test_cases.py
=========================================================================
Centralized test case repository for the YosysVerilog backend.

Author : Peitian Pan
Date   : Dec 20, 2019
"""

from pymtl3.passes.backends.verilog.testcases import (
    Bits32Foo,
    Bits32x5Foo,
    CaseArrayBits32IfcInUpblkComp,
    CaseBehavioralArraySubCompArrayStructIfcComp,
    CaseBits32ArrayConnectSubCompAttrComp,
    CaseBits32ArraySubCompAttrUpblkComp,
    CaseBits32BitSelUpblkComp,
    CaseBits32ConnectSubCompAttrComp,
    CaseBits32FooInBits32OutComp,
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
    CaseBits64ZextInComp,
    CaseBitSelOverBitSelComp,
    CaseBitSelOverPartSelComp,
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
    CaseForRangeLowerUpperStepPassThroughComp,
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
    CaseTypeBundle,
    CaseVerilogReservedComp,
    NestedStructPackedPlusScalar,
    ThisIsABitStructWithSuperLongName,
    set_attributes,
)

CaseSizeCastPaddingStructPort = set_attributes( CaseSizeCastPaddingStructPort,
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
          input logic [31:0] in___foo,
          output logic [63:0] out,
          input logic [0:0] reset
        );
          logic [31:0] in_;

          always_comb begin : upblk
            out = { { 32 { 1'b0 } }, in_ };
          end

          assign in_[31:0] = in___foo;

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
          output logic [31:0] out__0,
          output logic [31:0] out__1,
          input logic [0:0] reset
        );
          logic [31:0] out [0:1];

          always_comb begin : _lambda__s_out_1_
            out[1'd1] = in_ + 32'd42;
          end

          assign out__0 = out[0];
          assign out__1 = out[1];

        endmodule
    '''
)

CaseBits32x2ConcatFreeVarComp = set_attributes( CaseBits32x2ConcatFreeVarComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_, 1'd0 };
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

          always_comb begin : upblk
            out = { in_, 1'd0 };
          end

        endmodule
    '''
)

CaseBits32x2ConcatUnpackedSignalComp = set_attributes( CaseBits32x2ConcatUnpackedSignalComp,
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in___0,
          input logic [31:0] in___1,
          output logic [63:0] out,
          input logic [0:0] reset
        );
          logic [31:0] in_ [0:1];

          always_comb begin : upblk
            out = { in_[1'd0], in_[1'd1] };
          end

          assign in_[0] = in___0;
          assign in_[1] = in___1;

        endmodule
    '''
)

CaseConnectConstToOutComp = set_attributes( CaseConnectConstToOutComp,
    'REF_SRC',
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

CaseForRangeLowerUpperStepPassThroughComp = set_attributes( CaseForRangeLowerUpperStepPassThroughComp,
    'REF_UPBLK',
    '''\
        integer __loopvar__upblk_i;

        always_comb begin : upblk
          for ( __loopvar__upblk_i = 1'd0; __loopvar__upblk_i < 3'd5; __loopvar__upblk_i = __loopvar__upblk_i + 2'd2 )
            out[3'(__loopvar__upblk_i)] = in_[3'(__loopvar__upblk_i)];
          for ( __loopvar__upblk_i = 1'd1; __loopvar__upblk_i < 3'd5; __loopvar__upblk_i = __loopvar__upblk_i + 2'd2 )
            out[3'(__loopvar__upblk_i)] = in_[3'(__loopvar__upblk_i)];
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in___0,
          input logic [31:0] in___1,
          input logic [31:0] in___2,
          input logic [31:0] in___3,
          input logic [31:0] in___4,
          output logic [31:0] out__0,
          output logic [31:0] out__1,
          output logic [31:0] out__2,
          output logic [31:0] out__3,
          output logic [31:0] out__4,
          input logic [0:0] reset
        );
          logic [31:0] in_ [0:4];
          logic [31:0] out [0:4];

          integer __loopvar__upblk_i;

          always_comb begin : upblk
            for ( __loopvar__upblk_i = 1'd0; __loopvar__upblk_i < 3'd5; __loopvar__upblk_i = __loopvar__upblk_i + 2'd2 )
              out[3'(__loopvar__upblk_i)] = in_[3'(__loopvar__upblk_i)];
            for ( __loopvar__upblk_i = 1'd1; __loopvar__upblk_i < 3'd5; __loopvar__upblk_i = __loopvar__upblk_i + 2'd2 )
              out[3'(__loopvar__upblk_i)] = in_[3'(__loopvar__upblk_i)];
          end

          assign in_[0] = in___0;
          assign in_[1] = in___1;
          assign in_[2] = in___2;
          assign in_[3] = in___3;
          assign in_[4] = in___4;
          assign out__0 = out[0];
          assign out__1 = out[1];
          assign out__2 = out[2];
          assign out__3 = out[3];
          assign out__4 = out[4];

        endmodule
    '''
)

CaseIfExpInForStmtComp = set_attributes( CaseIfExpInForStmtComp,
    'REF_UPBLK',
    '''\
        integer __loopvar__upblk_i;

        always_comb begin : upblk
          for ( __loopvar__upblk_i = 1'd0; __loopvar__upblk_i < 3'd5; __loopvar__upblk_i = __loopvar__upblk_i + 1'd1 )
            out[3'(__loopvar__upblk_i)] = ( 3'(__loopvar__upblk_i) == 3'd1 ) ? in_[3'(__loopvar__upblk_i)] : in_[3'd0];
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in___0,
          input logic [31:0] in___1,
          input logic [31:0] in___2,
          input logic [31:0] in___3,
          input logic [31:0] in___4,
          output logic [31:0] out__0,
          output logic [31:0] out__1,
          output logic [31:0] out__2,
          output logic [31:0] out__3,
          output logic [31:0] out__4,
          input logic [0:0] reset
        );
          logic [31:0] in_ [0:4];
          logic [31:0] out [0:4];

          integer __loopvar__upblk_i;

          always_comb begin : upblk
            for ( __loopvar__upblk_i = 1'd0; __loopvar__upblk_i < 3'd5; __loopvar__upblk_i = __loopvar__upblk_i + 1'd1 )
              out[3'(__loopvar__upblk_i)] = ( 3'(__loopvar__upblk_i) == 3'd1 ) ? in_[3'(__loopvar__upblk_i)] : in_[3'd0];
          end

          assign in_[0] = in___0;
          assign in_[1] = in___1;
          assign in_[2] = in___2;
          assign in_[3] = in___3;
          assign in_[4] = in___4;
          assign out__0 = out[0];
          assign out__1 = out[1];
          assign out__2 = out[2];
          assign out__3 = out[3];
          assign out__4 = out[4];

        endmodule
    '''
)

CaseIfExpUnaryOpInForStmtComp = set_attributes( CaseIfExpUnaryOpInForStmtComp,
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in___0,
          input logic [31:0] in___1,
          input logic [31:0] in___2,
          input logic [31:0] in___3,
          input logic [31:0] in___4,
          output logic [31:0] out__0,
          output logic [31:0] out__1,
          output logic [31:0] out__2,
          output logic [31:0] out__3,
          output logic [31:0] out__4,
          input logic [0:0] reset
        );
          logic [31:0] in_ [0:4];
          logic [31:0] out [0:4];

          integer __loopvar__upblk_i;

          always_comb begin : upblk
            for ( __loopvar__upblk_i = 1'd0; __loopvar__upblk_i < 3'd5; __loopvar__upblk_i = __loopvar__upblk_i + 1'd1 )
              out[3'(__loopvar__upblk_i)] = ( 3'(__loopvar__upblk_i) == 3'd1 ) ? ~in_[3'(__loopvar__upblk_i)] : in_[3'd0];
          end

          assign in_[0] = in___0;
          assign in_[1] = in___1;
          assign in_[2] = in___2;
          assign in_[3] = in___3;
          assign in_[4] = in___4;
          assign out__0 = out[0];
          assign out__1 = out[1];
          assign out__2 = out[2];
          assign out__3 = out[3];
          assign out__4 = out[4];

        endmodule
    '''
)

CaseIfBoolOpInForStmtComp = set_attributes( CaseIfBoolOpInForStmtComp,
    'REF_UPBLK',
    '''\
        integer __loopvar__upblk_i;

        always_comb begin : upblk
          for ( __loopvar__upblk_i = 1'd0; __loopvar__upblk_i < 3'd5; __loopvar__upblk_i = __loopvar__upblk_i + 1'd1 )
            if ( ( in_[3'(__loopvar__upblk_i)] != 32'd0 ) & ( ( 3'(__loopvar__upblk_i) < 3'd4 ) ? in_[3'(__loopvar__upblk_i) + 3'd1] != 32'd0 : in_[3'd4] != 32'd0 ) ) begin
              out[3'(__loopvar__upblk_i)] = in_[3'(__loopvar__upblk_i)];
            end
            else
              out[3'(__loopvar__upblk_i)] = 32'd0;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input  logic [0:0]    clk,
          input  logic [31:0]   in___0,
          input  logic [31:0]   in___1,
          input  logic [31:0]   in___2,
          input  logic [31:0]   in___3,
          input  logic [31:0]   in___4,
          output logic [31:0]   out__0,
          output logic [31:0]   out__1,
          output logic [31:0]   out__2,
          output logic [31:0]   out__3,
          output logic [31:0]   out__4,
          input  logic [0:0]    reset
        );
          // Struct/Array ports in the form of wires
          logic [31:0]   in_ [0:4];
          logic [31:0]   out [0:4];

          integer __loopvar__upblk_i;

          always_comb begin : upblk
            for ( __loopvar__upblk_i = 1'd0; __loopvar__upblk_i < 3'd5; __loopvar__upblk_i = __loopvar__upblk_i + 1'd1 )
              if ( ( in_[3'(__loopvar__upblk_i)] != 32'd0 ) & ( ( 3'(__loopvar__upblk_i) < 3'd4 ) ? in_[3'(__loopvar__upblk_i) + 3'd1] != 32'd0 : in_[3'd4] != 32'd0 ) ) begin
                out[3'(__loopvar__upblk_i)] = in_[3'(__loopvar__upblk_i)];
              end
              else
                out[3'(__loopvar__upblk_i)] = 32'd0;
          end

          // Connections
          assign in_[0] = in___0;
          assign in_[1] = in___1;
          assign in_[2] = in___2;
          assign in_[3] = in___3;
          assign in_[4] = in___4;
          assign out__0 = out[0];
          assign out__1 = out[1];
          assign out__2 = out[2];
          assign out__3 = out[3];
          assign out__4 = out[4];

        endmodule
    '''
)

CaseIfTmpVarInForStmtComp = set_attributes( CaseIfTmpVarInForStmtComp,
    'REF_UPBLK',
    '''\
        integer __loopvar__upblk_i;

        always_comb begin : upblk
          for ( __loopvar__upblk_i = 1'd0; __loopvar__upblk_i < 3'd5; __loopvar__upblk_i = __loopvar__upblk_i + 1'd1 ) begin
            if ( ( in_[3'(__loopvar__upblk_i)] != 32'd0 ) & ( ( 3'(__loopvar__upblk_i) < 3'd4 ) ? in_[3'(__loopvar__upblk_i) + 3'd1] != 32'd0 : in_[3'd4] != 32'd0 ) ) begin
              __tmpvar__upblk_tmpvar = in_[3'(__loopvar__upblk_i)];
            end
            else
              __tmpvar__upblk_tmpvar = 32'd0;
            out[3'(__loopvar__upblk_i)] = __tmpvar__upblk_tmpvar;
          end
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input  logic [0:0]    clk,
          input  logic [31:0]   in___0,
          input  logic [31:0]   in___1,
          input  logic [31:0]   in___2,
          input  logic [31:0]   in___3,
          input  logic [31:0]   in___4,
          output logic [31:0]   out__0,
          output logic [31:0]   out__1,
          output logic [31:0]   out__2,
          output logic [31:0]   out__3,
          output logic [31:0]   out__4,
          input  logic [0:0]    reset
        );
          // Struct/Array ports in the form of wires
          logic [31:0]   in_ [0:4];
          logic [31:0]   out [0:4];

          // Temporary wire definitions
          logic [31:0]   __tmpvar__upblk_tmpvar;

          integer __loopvar__upblk_i;

          always_comb begin : upblk
            for ( __loopvar__upblk_i = 1'd0; __loopvar__upblk_i < 3'd5; __loopvar__upblk_i = __loopvar__upblk_i + 1'd1 ) begin
              if ( ( in_[3'(__loopvar__upblk_i)] != 32'd0 ) & ( ( 3'(__loopvar__upblk_i) < 3'd4 ) ? in_[3'(__loopvar__upblk_i) + 3'd1] != 32'd0 : in_[3'd4] != 32'd0 ) ) begin
                __tmpvar__upblk_tmpvar = in_[3'(__loopvar__upblk_i)];
              end
              else
                __tmpvar__upblk_tmpvar = 32'd0;
              out[3'(__loopvar__upblk_i)] = __tmpvar__upblk_tmpvar;
            end
          end

          // Connections
          assign in_[0] = in___0;
          assign in_[1] = in___1;
          assign in_[2] = in___2;
          assign in_[3] = in___3;
          assign in_[4] = in___4;
          assign out__0 = out[0];
          assign out__1 = out[1];
          assign out__2 = out[2];
          assign out__3 = out[3];
          assign out__4 = out[4];

        endmodule
    '''
)

CaseFixedSizeSliceComp = set_attributes( CaseFixedSizeSliceComp,
    'REF_UPBLK',
    '''\
        integer __loopvar__upblk_i;

        always_comb begin : upblk
          for ( __loopvar__upblk_i = 1'd0; __loopvar__upblk_i < 2'd2; __loopvar__upblk_i = __loopvar__upblk_i + 1'd1 )
            out[1'(__loopvar__upblk_i)] = in_[4'(__loopvar__upblk_i) * 4'd8 +: 8];
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input  logic [0:0]    clk,
          input  logic [15:0]   in_,
          output logic [7:0]    out__0,
          output logic [7:0]    out__1,
          input  logic [0:0]    reset
        );
          // Struct/Array ports in the form of wires
          logic [7:0]    out [0:1];

          integer __loopvar__upblk_i;

          always_comb begin : upblk
            for ( __loopvar__upblk_i = 1'd0; __loopvar__upblk_i < 2'd2; __loopvar__upblk_i = __loopvar__upblk_i + 1'd1 )
              out[1'(__loopvar__upblk_i)] = in_[4'(__loopvar__upblk_i) * 4'd8 +: 8];
          end

          // Connections
          assign out__0 = out[0];
          assign out__1 = out[1];

        endmodule
    '''
)

CaseBits32FooInBits32OutComp = set_attributes( CaseBits32FooInBits32OutComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in___foo;
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in___foo,
          output logic [31:0] out,
          input logic [0:0] reset
        );
          logic [31:0] in_;

          always_comb begin : upblk
            out = in___foo;
          end

          assign in_[31:0] = in___foo;

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
          input  logic [0:0]    clk,
          output logic [31:0]   out,
          input  logic [0:0]    reset
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
          out = { in___foo[3'd0], in___foo[3'd1], in___foo[3'd2] };
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input  logic [0:0]    clk,
          input  logic [31:0]   in___foo__0,
          input  logic [31:0]   in___foo__1,
          input  logic [31:0]   in___foo__2,
          input  logic [31:0]   in___foo__3,
          input  logic [31:0]   in___foo__4,
          output logic [95:0]   out,
          input  logic [0:0]    reset
        );
          // Struct/Array ports in the form of wires
          logic [31:0]   in___foo [0:4];
          logic [159:0]  in_;

          always_comb begin : upblk
            out = { in___foo[3'd0], in___foo[3'd1], in___foo[3'd2] };
          end

          // Connections
          assign in___foo[0] = in___foo__0;
          assign in___foo[1] = in___foo__1;
          assign in___foo[2] = in___foo__2;
          assign in___foo[3] = in___foo__3;
          assign in___foo[4] = in___foo__4;
          assign in_[159:128] = in___foo__4;
          assign in_[127:96] = in___foo__3;
          assign in_[95:64] = in___foo__2;
          assign in_[63:32] = in___foo__1;
          assign in_[31:0] = in___foo__0;

        endmodule
    '''
)

CaseNestedStructPackedArrayUpblkComp = set_attributes( CaseNestedStructPackedArrayUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in___bar[1'd0], in___woo__foo, in___foo };
        end
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input  logic [0:0]    clk,
          input  logic [31:0]   in___foo,
          input  logic [31:0]   in___bar__0,
          input  logic [31:0]   in___bar__1,
          input  logic [31:0]   in___woo__foo,
          output logic [95:0]   out,
          input  logic [0:0]    reset
        );
          // Struct/Array ports in the form of wires
          logic [31:0]   in___bar [0:1];
          logic [31:0]   in___woo;
          logic [127:0]  in_;

          always_comb begin : upblk
            out = { in___bar[1'd0], in___woo__foo, in___foo };
          end

          // Connections
          assign in___bar[0] = in___bar__0;
          assign in___bar[1] = in___bar__1;
          assign in___woo[31:0] = in___woo__foo;
          assign in_[127:96] = in___foo;
          assign in_[95:64] = in___bar__1;
          assign in_[63:32] = in___bar__0;
          assign in_[31:0] = in___woo__foo;

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
          input  logic [0:0]    clk,
          output logic [31:0]   out,
          input  logic [0:0]    reset,
          input  logic [31:0]   in___0__foo,
          input  logic [31:0]   in___1__foo,
          input  logic [31:0]   in___2__foo,
          input  logic [31:0]   in___3__foo,
          input  logic [31:0]   in___4__foo
        );
          // Struct/Array ports in the form of wires
          logic [31:0]   in___foo [0:4];

          always_comb begin : upblk
            out = in___foo[3'd1];
          end

          // Connections
          assign in___foo[0] = in___0__foo;
          assign in___foo[1] = in___1__foo;
          assign in___foo[2] = in___2__foo;
          assign in___foo[3] = in___3__foo;
          assign in___foo[4] = in___4__foo;

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
          input  logic [0:0]    clk,
          output logic [31:0]   out,
          input  logic [0:0]    reset,
          input  logic [31:0]   in___0__foo,
          input  logic [31:0]   in___1__foo
        );
          // Struct/Array ports in the form of wires
          logic [31:0]   in___foo [0:1];

          always_comb begin : upblk
            out = in___foo[in___foo[1'd0][5'd0]];
          end

          // Connections
          assign in___foo[0] = in___0__foo;
          assign in___foo[1] = in___1__foo;

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
          input  logic [0:0]    clk,
          output logic [31:0]   out,
          input  logic [0:0]    reset
        );

          // Connections
          assign out = 32'd42;

        endmodule

        module DUT_noparam
        (
          input  logic [0:0]    clk,
          output logic [31:0]   out,
          input  logic [0:0]    reset
        );
          // Struct/Array ports of sub-components in the form of wires
          logic [0:0]    b__clk [0:4];
          logic [31:0]   b__out [0:4];
          logic [0:0]    b__reset [0:4];

          // Sub-component declarations
          logic [0:0]    b__0__clk;
          logic [31:0]   b__0__out;
          logic [0:0]    b__0__reset;

          Bits32OutDrivenComp_noparam b__0
          (
            .clk            (         b__0__clk         ),
            .out            (         b__0__out         ),
            .reset          (        b__0__reset        )
          );

          logic [0:0]    b__1__clk;
          logic [31:0]   b__1__out;
          logic [0:0]    b__1__reset;

          Bits32OutDrivenComp_noparam b__1
          (
            .clk            (         b__1__clk         ),
            .out            (         b__1__out         ),
            .reset          (        b__1__reset        )
          );

          logic [0:0]    b__2__clk;
          logic [31:0]   b__2__out;
          logic [0:0]    b__2__reset;

          Bits32OutDrivenComp_noparam b__2
          (
            .clk            (         b__2__clk         ),
            .out            (         b__2__out         ),
            .reset          (        b__2__reset        )
          );

          logic [0:0]    b__3__clk;
          logic [31:0]   b__3__out;
          logic [0:0]    b__3__reset;

          Bits32OutDrivenComp_noparam b__3
          (
            .clk            (         b__3__clk         ),
            .out            (         b__3__out         ),
            .reset          (        b__3__reset        )
          );

          logic [0:0]    b__4__clk;
          logic [31:0]   b__4__out;
          logic [0:0]    b__4__reset;

          Bits32OutDrivenComp_noparam b__4
          (
            .clk            (         b__4__clk         ),
            .out            (         b__4__out         ),
            .reset          (        b__4__reset        )
          );

          // Connect struct/array ports and their wire forms
          assign b__0__clk = b__clk[0];
          assign b__1__clk = b__clk[1];
          assign b__2__clk = b__clk[2];
          assign b__3__clk = b__clk[3];
          assign b__4__clk = b__clk[4];
          assign b__out[0] = b__0__out;
          assign b__out[1] = b__1__out;
          assign b__out[2] = b__2__out;
          assign b__out[3] = b__3__out;
          assign b__out[4] = b__4__out;
          assign b__0__reset = b__reset[0];
          assign b__1__reset = b__reset[1];
          assign b__2__reset = b__reset[2];
          assign b__3__reset = b__reset[3];
          assign b__4__reset = b__reset[4];

          always_comb begin : upblk
            out = b__out[3'd1];
          end

          // Connections
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
    'REF_PORTS_PORT',
    '''\
        input  logic [0:0]    clk,
        input  logic [31:0]   in___0,
        input  logic [31:0]   in___1,
        input  logic [31:0]   in___2,
        input  logic [31:0]   in___3,
        input  logic [31:0]   in___4,
        output logic [31:0]   out,
        input  logic [0:0]    reset
    ''',
    'REF_PORTS_WIRE',
    '''\
        logic [31:0]   in_ [0:4];
    ''',
    'REF_PORTS_CONN',
    '''\
        assign in_[0] = in___0;
        assign in_[1] = in___1;
        assign in_[2] = in___2;
        assign in_[3] = in___3;
        assign in_[4] = in___4;
    ''',
    'REF_WIRE',
    '''\
        logic [31:0]   wire_ [0:4];
    ''',
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
          input  logic [0:0]    clk,
          input  logic [31:0]   in___0,
          input  logic [31:0]   in___1,
          input  logic [31:0]   in___2,
          input  logic [31:0]   in___3,
          input  logic [31:0]   in___4,
          output logic [31:0]   out,
          input  logic [0:0]    reset
        );
          // Struct/Array ports in the form of wires
          logic [31:0]   in_ [0:4];

          // Wire declarations
          logic [31:0]   wire_ [0:4];

          // Connections
          assign in_[0] = in___0;
          assign in_[1] = in___1;
          assign in_[2] = in___2;
          assign in_[3] = in___3;
          assign in_[4] = in___4;
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
    'REF_PORTS_PORT',
    '''\
        input  logic [0:0]    clk,
        output logic [31:0]   out,
        input  logic [0:0]    reset
    ''',
    'REF_PORTS_WIRE',
    '''\
    ''',
    'REF_PORTS_CONN',
    '''\
    ''',
    'REF_WIRE',
    '''\
    ''',
    'REF_CONN',
    '''\
        assign out = 32'd0;
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input  logic [0:0]    clk,
          output logic [31:0]   out,
          input  logic [0:0]    reset
        );

          // Connections
          assign out = 32'd0;

        endmodule
    '''
)

CaseConnectConstToOutComp = set_attributes( CaseConnectConstToOutComp,
    'REF_PORTS_PORT',
    '''\
        input  logic [0:0]    clk,
        output logic [31:0]   out,
        input  logic [0:0]    reset
    ''',
    'REF_PORTS_WIRE',
    '''\
    ''',
    'REF_PORTS_CONN',
    '''\
    ''',
    'REF_WIRE',
    '''\
    ''',
    'REF_CONN',
    '''\
        assign out = 32'd42;
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input  logic [0:0]    clk,
          output logic [31:0]   out,
          input  logic [0:0]    reset
        );

          // Connections
          assign out = 32'd42;

        endmodule
    '''
)

CaseConnectBitSelToOutComp = set_attributes( CaseConnectBitSelToOutComp,
    'REF_PORTS_PORT',
    '''\
        input  logic [0:0]    clk,
        input  logic [31:0]   in_,
        output logic [0:0]   out,
        input  logic [0:0]    reset
    ''',
    'REF_PORTS_WIRE',
    '''\
    ''',
    'REF_PORTS_CONN',
    '''\
    ''',
    'REF_WIRE',
    '''\
    ''',
    'REF_CONN',
    '''\
        assign out = in_[0:0];
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input  logic [0:0]    clk,
          input  logic [31:0]   in_,
          output logic [0:0]    out,
          input  logic [0:0]    reset
        );

          // Connections
          assign out = in_[0:0];

        endmodule
    '''
)

CaseConnectSliceToOutComp = set_attributes( CaseConnectSliceToOutComp,
    'REF_PORTS_PORT',
    '''\
        input  logic [0:0]    clk,
        input  logic [31:0]   in_,
        output logic [3:0]   out,
        input  logic [0:0]    reset
    ''',
    'REF_PORTS_WIRE',
    '''\
    ''',
    'REF_PORTS_CONN',
    '''\
    ''',
    'REF_WIRE',
    '''\
    ''',
    'REF_CONN',
    '''\
        assign out = in_[7:4];
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input  logic [0:0]    clk,
          input  logic [31:0]   in_,
          output logic [3:0]    out,
          input  logic [0:0]    reset
        );

          // Connections
          assign out = in_[7:4];

        endmodule
    '''
)

CaseConnectConstStructAttrToOutComp = set_attributes( CaseConnectConstStructAttrToOutComp,
    'REF_PORTS_PORT',
    '''\
        input  logic [0:0]    clk,
        output logic [31:0]   out,
        input  logic [0:0]    reset
    ''',
    'REF_PORTS_WIRE',
    '''\
    ''',
    'REF_PORTS_CONN',
    '''\
    ''',
    'REF_WIRE',
    '''\
    ''',
    'REF_CONN',
    '''\
        assign out = 32'd42;
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input  logic [0:0]    clk,
          output logic [31:0]   out,
          input  logic [0:0]    reset
        );

          // Connections
          assign out = 32'd42;

        endmodule
    '''
)

CaseConnectLiteralStructComp = set_attributes( CaseConnectLiteralStructComp,
    'REF_PORTS_PORT',
    '''\
        input  logic [0:0]    clk,
        output logic [31:0]   out__foo,
        output logic [31:0]   out__bar__0,
        output logic [31:0]   out__bar__1,
        output logic [31:0]   out__woo__foo,
        input  logic [0:0]    reset
    ''',
    'REF_PORTS_WIRE',
    '''\
        logic [31:0]   out__bar [0:1];
        logic [31:0]   out__woo;
        logic [127:0]  out;
    ''',
    'REF_PORTS_CONN',
    '''\
        assign out__bar__0 = out__bar[0];
        assign out__bar__1 = out__bar[1];
        assign out__woo__foo = out__woo[31:0];
        assign out__foo = out[127:96];
        assign out__bar__1 = out[95:64];
        assign out__bar__0 = out[63:32];
        assign out__woo__foo = out[31:0];
    ''',
    'REF_WIRE',
    '''\
    ''',
    'REF_CONN',
    '''\
        assign out = { 32'd42, { 32'd2, 32'd1 }, 32'd3 };
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input  logic [0:0]    clk,
          output logic [31:0]   out__foo,
          output logic [31:0]   out__bar__0,
          output logic [31:0]   out__bar__1,
          output logic [31:0]   out__woo__foo,
          input  logic [0:0]    reset
        );
          // Struct/Array ports in the form of wires
          logic [31:0]   out__bar [0:1];
          logic [31:0]   out__woo;
          logic [127:0]  out;

          // Connections
          assign out__bar__0 = out__bar[0];
          assign out__bar__1 = out__bar[1];
          assign out__woo__foo = out__woo[31:0];
          assign out__foo = out[127:96];
          assign out__bar__1 = out[95:64];
          assign out__bar__0 = out[63:32];
          assign out__woo__foo = out[31:0];
          assign out = { 32'd42, { 32'd2, 32'd1 }, 32'd3 };

        endmodule
    '''
)

CaseConnectArrayStructAttrToOutComp = set_attributes( CaseConnectArrayStructAttrToOutComp,
    'REF_PORTS_PORT',
    '''\
        input  logic [0:0]    clk,
        input  logic [31:0]   in___foo__0,
        input  logic [31:0]   in___foo__1,
        input  logic [31:0]   in___foo__2,
        input  logic [31:0]   in___foo__3,
        input  logic [31:0]   in___foo__4,
        output logic [31:0]   out,
        input  logic [0:0]    reset
    ''',
    'REF_PORTS_WIRE',
    '''\
        logic [31:0]   in___foo [0:4];
        logic [159:0]  in_;
    ''',
    'REF_PORTS_CONN',
    '''\
        assign in___foo[0] = in___foo__0;
        assign in___foo[1] = in___foo__1;
        assign in___foo[2] = in___foo__2;
        assign in___foo[3] = in___foo__3;
        assign in___foo[4] = in___foo__4;
        assign in_[159:128] = in___foo__4;
        assign in_[127:96] = in___foo__3;
        assign in_[95:64] = in___foo__2;
        assign in_[63:32] = in___foo__1;
        assign in_[31:0] = in___foo__0;
    ''',
    'REF_WIRE',
    '''\
    ''',
    'REF_CONN',
    '''\
        assign out = in___foo[1];
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input  logic [0:0]    clk,
          input  logic [31:0]   in___foo__0,
          input  logic [31:0]   in___foo__1,
          input  logic [31:0]   in___foo__2,
          input  logic [31:0]   in___foo__3,
          input  logic [31:0]   in___foo__4,
          output logic [31:0]   out,
          input  logic [0:0]    reset
        );
          // Struct/Array ports in the form of wires
          logic [31:0]   in___foo [0:4];
          logic [159:0]  in_;

          // Connections
          assign in___foo[0] = in___foo__0;
          assign in___foo[1] = in___foo__1;
          assign in___foo[2] = in___foo__2;
          assign in___foo[3] = in___foo__3;
          assign in___foo[4] = in___foo__4;
          assign in_[159:128] = in___foo__4;
          assign in_[127:96] = in___foo__3;
          assign in_[95:64] = in___foo__2;
          assign in_[63:32] = in___foo__1;
          assign in_[31:0] = in___foo__0;
          assign out = in___foo[1];

        endmodule
    '''
)

CaseConnectNestedStructPackedArrayComp = set_attributes( CaseConnectNestedStructPackedArrayComp,
    'REF_PORTS_PORT',
    '''\
        input  logic [0:0]    clk,
        input  logic [31:0]   in___foo,
        input  logic [31:0]   in___bar__0,
        input  logic [31:0]   in___bar__1,
        input  logic [31:0]   in___woo__foo,
        output logic [95:0]   out,
        input  logic [0:0]    reset
    ''',
    'REF_PORTS_WIRE',
    '''\
        logic [31:0]   in___bar [0:1];
        logic [31:0]   in___woo;
        logic [127:0]  in_;
    ''',
    'REF_PORTS_CONN',
    '''\
        assign in___bar[0] = in___bar__0;
        assign in___bar[1] = in___bar__1;
        assign in___woo[31:0] = in___woo__foo;
        assign in_[127:96] = in___foo;
        assign in_[95:64] = in___bar__1;
        assign in_[63:32] = in___bar__0;
        assign in_[31:0] = in___woo__foo;
    ''',
    'REF_WIRE',
    '''\
    ''',
    'REF_CONN',
    '''\
        assign out[31:0] = in___foo;
        assign out[63:32] = in___woo__foo;
        assign out[95:64] = in___bar[0];
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input  logic [0:0]    clk,
          input  logic [31:0]   in___foo,
          input  logic [31:0]   in___bar__0,
          input  logic [31:0]   in___bar__1,
          input  logic [31:0]   in___woo__foo,
          output logic [95:0]   out,
          input  logic [0:0]    reset
        );
          // Struct/Array ports in the form of wires
          logic [31:0]   in___bar [0:1];
          logic [31:0]   in___woo;
          logic [127:0]  in_;

          // Connections
          assign in___bar[0] = in___bar__0;
          assign in___bar[1] = in___bar__1;
          assign in___woo[31:0] = in___woo__foo;
          assign in_[127:96] = in___foo;
          assign in_[95:64] = in___bar__1;
          assign in_[63:32] = in___bar__0;
          assign in_[31:0] = in___woo__foo;
          assign out[31:0] = in___foo;
          assign out[63:32] = in___woo__foo;
          assign out[95:64] = in___bar[0];

        endmodule
    '''
)

CaseBitSelOverBitSelComp = set_attributes( CaseBitSelOverBitSelComp,
    'REF_PORTS_PORT',
    '''\
        input logic [0:0] clk,
        input logic [31:0] in_,
        output logic [0:0] out,
        input logic [0:0] reset
    ''',
    'REF_PORTS_WIRE',
    '',
    'REF_PORTS_CONN',
    '',
)

CaseBitSelOverPartSelComp = set_attributes( CaseBitSelOverPartSelComp,
    'REF_PORTS_PORT',
    '''\
        input logic [0:0] clk,
        input logic [31:0] in_,
        output logic [0:0] out,
        input logic [0:0] reset
    ''',
    'REF_PORTS_WIRE',
    '',
    'REF_PORTS_CONN',
    '',
)

CasePartSelOverBitSelComp = set_attributes( CasePartSelOverBitSelComp,
    'REF_PORTS_PORT',
    '''\
        input logic [0:0] clk,
        input logic [31:0] in_,
        output logic [0:0] out,
        input logic [0:0] reset
    ''',
    'REF_PORTS_WIRE',
    '',
    'REF_PORTS_CONN',
    '',
)

CasePartSelOverPartSelComp = set_attributes( CasePartSelOverPartSelComp,
    'REF_PORTS_PORT',
    '''\
        input logic [0:0] clk,
        input logic [31:0] in_,
        output logic [0:0] out,
        input logic [0:0] reset
    ''',
    'REF_PORTS_WIRE',
    '',
    'REF_PORTS_CONN',
    '',
)

CaseConnectValRdyIfcComp = set_attributes( CaseConnectValRdyIfcComp,
    'REF_IFC_PORT',
    '''\
        input  logic [31:0]   in___msg,
        output logic [0:0]    in___rdy,
        input  logic [0:0]    in___val,
        output logic [31:0]   out__msg,
        input  logic [0:0]    out__rdy,
        output logic [0:0]    out__val
    ''',
    'REF_IFC_WIRE',
    '''\
    ''',
    'REF_IFC_CONN',
    '''\
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
          input  logic [0:0]    clk,
          input  logic [0:0]    reset,
          input  logic [31:0]   in___msg,
          output logic [0:0]    in___rdy,
          input  logic [0:0]    in___val,
          output logic [31:0]   out__msg,
          input  logic [0:0]    out__rdy,
          output logic [0:0]    out__val
        );

          // Connections
          assign out__msg = in___msg;
          assign in___rdy = out__rdy;
          assign out__val = in___val;

        endmodule
    '''
)

CaseConnectArrayBits32FooIfcComp = set_attributes( CaseConnectArrayBits32FooIfcComp,
    'REF_IFC_PORT',
    '''\
        input  logic [31:0]   in___0__foo__foo,
        input  logic [31:0]   in___1__foo__foo,
        output logic [31:0]   out__0__foo__foo,
        output logic [31:0]   out__1__foo__foo
    ''',
    'REF_IFC_WIRE',
    '''\
        logic [31:0]   in___foo__foo [0:1];
        logic [31:0]   in___foo [0:1];
        logic [31:0]   out__foo__foo [0:1];
        logic [31:0]   out__foo [0:1];
    ''',
    'REF_IFC_CONN',
    '''\
        assign in___foo__foo[0] = in___0__foo__foo;
        assign in___foo__foo[1] = in___1__foo__foo;
        assign in___foo[0][31:0] = in___0__foo__foo;
        assign in___foo[1][31:0] = in___1__foo__foo;
        assign out__0__foo__foo = out__foo__foo[0];
        assign out__1__foo__foo = out__foo__foo[1];
        assign out__0__foo__foo = out__foo[0][31:0];
        assign out__1__foo__foo = out__foo[1][31:0];
    ''',
    'REF_CONN',
    '''\
        assign out__foo[0] = in___foo[0];
        assign out__foo[1] = in___foo[1];
    ''',
    'REF_SRC',
    '''\
        module DUT_noparam
        (
          input  logic [0:0]    clk,
          input  logic [0:0]    reset,
          input  logic [31:0]   in___0__foo__foo,
          input  logic [31:0]   in___1__foo__foo,
          output logic [31:0]   out__0__foo__foo,
          output logic [31:0]   out__1__foo__foo
        );
          // Struct/Array ports in the form of wires
          logic [31:0]   in___foo__foo [0:1];
          logic [31:0]   in___foo [0:1];
          logic [31:0]   out__foo__foo [0:1];
          logic [31:0]   out__foo [0:1];

          // Connections
          assign in___foo__foo[0] = in___0__foo__foo;
          assign in___foo__foo[1] = in___1__foo__foo;
          assign in___foo[0][31:0] = in___0__foo__foo;
          assign in___foo[1][31:0] = in___1__foo__foo;
          assign out__0__foo__foo = out__foo__foo[0];
          assign out__1__foo__foo = out__foo__foo[1];
          assign out__0__foo__foo = out__foo[0][31:0];
          assign out__1__foo__foo = out__foo[1][31:0];
          assign out__foo[0] = in___foo[0];
          assign out__foo[1] = in___foo[1];

        endmodule
    '''
)

CaseConnectArrayNestedIfcComp = set_attributes( CaseConnectArrayNestedIfcComp,
    'REF_IFC_PORT',
    '''\
        input  logic [0:0]    in___0__ctrl_foo,
        input  logic [0:0]    in___1__ctrl_foo,
        input  logic [31:0]   in___0__memifc__msg,
        input  logic [31:0]   in___1__memifc__msg,
        output logic [0:0]    in___0__memifc__rdy,
        output logic [0:0]    in___1__memifc__rdy,
        input  logic [0:0]    in___0__memifc__val,
        input  logic [0:0]    in___1__memifc__val,
        output logic [0:0]    out__0__ctrl_foo,
        output logic [0:0]    out__1__ctrl_foo,
        output logic [31:0]   out__0__memifc__msg,
        output logic [31:0]   out__1__memifc__msg,
        input  logic [0:0]    out__0__memifc__rdy,
        input  logic [0:0]    out__1__memifc__rdy,
        output logic [0:0]    out__0__memifc__val,
        output logic [0:0]    out__1__memifc__val
    ''',
    'REF_IFC_WIRE',
    '''\
        logic [0:0]    in___ctrl_foo [0:1];
        logic [31:0]   in___memifc__msg [0:1];
        logic [0:0]    in___memifc__rdy [0:1];
        logic [0:0]    in___memifc__val [0:1];
        logic [0:0]    out__ctrl_foo [0:1];
        logic [31:0]   out__memifc__msg [0:1];
        logic [0:0]    out__memifc__rdy [0:1];
        logic [0:0]    out__memifc__val [0:1];
    ''',
    'REF_IFC_CONN',
    '''\
        assign in___ctrl_foo[0] = in___0__ctrl_foo;
        assign in___ctrl_foo[1] = in___1__ctrl_foo;
        assign in___memifc__msg[0] = in___0__memifc__msg;
        assign in___memifc__msg[1] = in___1__memifc__msg;
        assign in___0__memifc__rdy = in___memifc__rdy[0];
        assign in___1__memifc__rdy = in___memifc__rdy[1];
        assign in___memifc__val[0] = in___0__memifc__val;
        assign in___memifc__val[1] = in___1__memifc__val;
        assign out__0__ctrl_foo = out__ctrl_foo[0];
        assign out__1__ctrl_foo = out__ctrl_foo[1];
        assign out__0__memifc__msg = out__memifc__msg[0];
        assign out__1__memifc__msg = out__memifc__msg[1];
        assign out__memifc__rdy[0] = out__0__memifc__rdy;
        assign out__memifc__rdy[1] = out__1__memifc__rdy;
        assign out__0__memifc__val = out__memifc__val[0];
        assign out__1__memifc__val = out__memifc__val[1];
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
          input  logic [0:0]    clk,
          input  logic [0:0]    reset,
          input  logic [0:0]    in___0__ctrl_foo,
          input  logic [0:0]    in___1__ctrl_foo,
          input  logic [31:0]   in___0__memifc__msg,
          input  logic [31:0]   in___1__memifc__msg,
          output logic [0:0]    in___0__memifc__rdy,
          output logic [0:0]    in___1__memifc__rdy,
          input  logic [0:0]    in___0__memifc__val,
          input  logic [0:0]    in___1__memifc__val,
          output logic [0:0]    out__0__ctrl_foo,
          output logic [0:0]    out__1__ctrl_foo,
          output logic [31:0]   out__0__memifc__msg,
          output logic [31:0]   out__1__memifc__msg,
          input  logic [0:0]    out__0__memifc__rdy,
          input  logic [0:0]    out__1__memifc__rdy,
          output logic [0:0]    out__0__memifc__val,
          output logic [0:0]    out__1__memifc__val
        );
          // Struct/Array ports in the form of wires
          logic [0:0]    in___ctrl_foo [0:1];
          logic [31:0]   in___memifc__msg [0:1];
          logic [0:0]    in___memifc__rdy [0:1];
          logic [0:0]    in___memifc__val [0:1];
          logic [0:0]    out__ctrl_foo [0:1];
          logic [31:0]   out__memifc__msg [0:1];
          logic [0:0]    out__memifc__rdy [0:1];
          logic [0:0]    out__memifc__val [0:1];

          // Connections
          assign in___ctrl_foo[0] = in___0__ctrl_foo;
          assign in___ctrl_foo[1] = in___1__ctrl_foo;
          assign in___memifc__msg[0] = in___0__memifc__msg;
          assign in___memifc__msg[1] = in___1__memifc__msg;
          assign in___0__memifc__rdy = in___memifc__rdy[0];
          assign in___1__memifc__rdy = in___memifc__rdy[1];
          assign in___memifc__val[0] = in___0__memifc__val;
          assign in___memifc__val[1] = in___1__memifc__val;
          assign out__0__ctrl_foo = out__ctrl_foo[0];
          assign out__1__ctrl_foo = out__ctrl_foo[1];
          assign out__0__memifc__msg = out__memifc__msg[0];
          assign out__1__memifc__msg = out__memifc__msg[1];
          assign out__memifc__rdy[0] = out__0__memifc__rdy;
          assign out__memifc__rdy[1] = out__1__memifc__rdy;
          assign out__0__memifc__val = out__memifc__val[0];
          assign out__1__memifc__val = out__memifc__val[1];
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
    'REF_COMP_PORT',
    '''\
        logic [0:0]    b__clk;
        logic [31:0]   b__out;
        logic [0:0]    b__reset;

        Bits32OutDrivenComp_noparam b
        (
          .clk            (           b__clk          ),
          .out            (           b__out          ),
          .reset          (          b__reset         )
        );
    ''',
    'REF_COMP_WIRE',
    '''\
    ''',
    'REF_COMP_CONN',
    '''\
    ''',
    'REF_SRC',
    '''\
        module Bits32OutDrivenComp_noparam
        (
          input  logic [0:0]    clk,
          output logic [31:0]   out,
          input  logic [0:0]    reset
        );

          // Connections
          assign out = 32'd42;

        endmodule

        module DUT_noparam
        (
          input  logic [0:0]    clk,
          output logic [31:0]   out,
          input  logic [0:0]    reset
        );
          // Sub-component declarations
          logic [0:0]    b__clk;
          logic [31:0]   b__out;
          logic [0:0]    b__reset;

          Bits32OutDrivenComp_noparam b
          (
            .clk            (           b__clk          ),
            .out            (           b__out          ),
            .reset          (          b__reset         )
          );

          // Connections
          assign b__clk = clk;
          assign b__reset = reset;
          assign out = b__out;

        endmodule
    '''
)

CaseConnectArraySubCompArrayStructIfcComp = set_attributes( CaseConnectArraySubCompArrayStructIfcComp,
    'REF_COMP_PORT',
    '''\
        logic [0:0]    b__0__clk;
        logic [31:0]   b__0__out;
        logic [0:0]    b__0__reset;
        logic [31:0]   b__0__ifc__0__foo__0__foo;

        Bits32ArrayStructIfcComp_noparam b__0
        (
          .clk            (         b__0__clk         ),
          .out            (         b__0__out         ),
          .reset          (        b__0__reset        ),
          .ifc__0__foo__0__foo( b__0__ifc__0__foo__0__foo )
        );
    ''',
    'REF_COMP_WIRE',
    '''\
        logic [0:0]    b__clk [0:0];
        logic [31:0]   b__out [0:0];
        logic [0:0]    b__reset [0:0];
        logic [31:0]   b__ifc__foo__foo [0:0][0:0][0:0];
        logic [31:0]   b__ifc__foo [0:0][0:0][0:0];
          ''',
          'REF_COMP_CONN',
          '''\
        assign b__0__clk = b__clk[0];
        assign b__out[0] = b__0__out;
        assign b__0__reset = b__reset[0];
        assign b__0__ifc__0__foo__0__foo = b__ifc__foo__foo[0][0][0];
        assign b__0__ifc__0__foo__0__foo = b__ifc__foo[0][0][0][31:0];
    ''',
    'REF_SRC',
    '''\
        module Bits32ArrayStructIfcComp_noparam
        (
          input  logic [0:0]    clk,
          output logic [31:0]   out,
          input  logic [0:0]    reset,
          input  logic [31:0]   ifc__0__foo__0__foo
        );
          // Struct/Array ports in the form of wires
          logic [31:0]   ifc__foo__foo [0:0][0:0];
          logic [31:0]   ifc__foo [0:0][0:0];

          // Connections
          assign ifc__foo__foo[0][0] = ifc__0__foo__0__foo;
          assign ifc__foo[0][0][31:0] = ifc__0__foo__0__foo;
          assign out = ifc__foo__foo[0][0];

        endmodule

        module DUT_noparam
        (
          input  logic [0:0]    clk,
          input  logic [31:0]   in_,
          output logic [31:0]   out,
          input  logic [0:0]    reset
        );
          // Struct/Array ports of sub-components in the form of wires
          logic [0:0]    b__clk [0:0];
          logic [31:0]   b__out [0:0];
          logic [0:0]    b__reset [0:0];
          logic [31:0]   b__ifc__foo__foo [0:0][0:0][0:0];
          logic [31:0]   b__ifc__foo [0:0][0:0][0:0];

          // Sub-component declarations
          logic [0:0]    b__0__clk;
          logic [31:0]   b__0__out;
          logic [0:0]    b__0__reset;
          logic [31:0]   b__0__ifc__0__foo__0__foo;

          Bits32ArrayStructIfcComp_noparam b__0
          (
            .clk            (         b__0__clk         ),
            .out            (         b__0__out         ),
            .reset          (        b__0__reset        ),
            .ifc__0__foo__0__foo( b__0__ifc__0__foo__0__foo )
          );

          // Connect struct/array ports and their wire forms
          assign b__0__clk = b__clk[0];
          assign b__out[0] = b__0__out;
          assign b__0__reset = b__reset[0];
          assign b__0__ifc__0__foo__0__foo = b__ifc__foo__foo[0][0][0];
          assign b__0__ifc__0__foo__0__foo = b__ifc__foo[0][0][0][31:0];

          // Connections
          assign b__clk[0] = clk;
          assign b__reset[0] = reset;
          assign b__ifc__foo__foo[0][0][0] = in_;
          assign out = b__out[0];

        endmodule
    '''
)

CaseBits32ArrayConnectSubCompAttrComp = set_attributes( CaseBits32ArrayConnectSubCompAttrComp,
    'REF_COMP_PORT',
    '''\
        logic [0:0]    b__0__clk;
        logic [31:0]   b__0__out;
        logic [0:0]    b__0__reset;

        Bits32OutDrivenComp_noparam b__0
        (
          .clk            (         b__0__clk         ),
          .out            (         b__0__out         ),
          .reset          (        b__0__reset        )
        );

        logic [0:0]    b__1__clk;
        logic [31:0]   b__1__out;
        logic [0:0]    b__1__reset;

        Bits32OutDrivenComp_noparam b__1
        (
          .clk            (         b__1__clk         ),
          .out            (         b__1__out         ),
          .reset          (        b__1__reset        )
        );

        logic [0:0]    b__2__clk;
        logic [31:0]   b__2__out;
        logic [0:0]    b__2__reset;

        Bits32OutDrivenComp_noparam b__2
        (
          .clk            (         b__2__clk         ),
          .out            (         b__2__out         ),
          .reset          (        b__2__reset        )
        );

        logic [0:0]    b__3__clk;
        logic [31:0]   b__3__out;
        logic [0:0]    b__3__reset;

        Bits32OutDrivenComp_noparam b__3
        (
          .clk            (         b__3__clk         ),
          .out            (         b__3__out         ),
          .reset          (        b__3__reset        )
        );

        logic [0:0]    b__4__clk;
        logic [31:0]   b__4__out;
        logic [0:0]    b__4__reset;

        Bits32OutDrivenComp_noparam b__4
        (
          .clk            (         b__4__clk         ),
          .out            (         b__4__out         ),
          .reset          (        b__4__reset        )
        );
    ''',
    'REF_COMP_WIRE',
    '''\
        logic [0:0]    b__clk [0:4];
        logic [31:0]   b__out [0:4];
        logic [0:0]    b__reset [0:4];
    ''',
    'REF_COMP_CONN',
    '''\
        assign b__0__clk = b__clk[0];
        assign b__1__clk = b__clk[1];
        assign b__2__clk = b__clk[2];
        assign b__3__clk = b__clk[3];
        assign b__4__clk = b__clk[4];
        assign b__out[0] = b__0__out;
        assign b__out[1] = b__1__out;
        assign b__out[2] = b__2__out;
        assign b__out[3] = b__3__out;
        assign b__out[4] = b__4__out;
        assign b__0__reset = b__reset[0];
        assign b__1__reset = b__reset[1];
        assign b__2__reset = b__reset[2];
        assign b__3__reset = b__reset[3];
        assign b__4__reset = b__reset[4];
    ''',
    'REF_SRC',
    '''\
        module Bits32OutDrivenComp_noparam
        (
          input  logic [0:0]    clk,
          output logic [31:0]   out,
          input  logic [0:0]    reset
        );

          // Connections
          assign out = 32'd42;

        endmodule

        module DUT_noparam
        (
          input  logic [0:0]    clk,
          output logic [31:0]   out,
          input  logic [0:0]    reset
        );
          // Struct/Array ports of sub-components in the form of wires
          logic [0:0]    b__clk [0:4];
          logic [31:0]   b__out [0:4];
          logic [0:0]    b__reset [0:4];

          // Sub-component declarations
          logic [0:0]    b__0__clk;
          logic [31:0]   b__0__out;
          logic [0:0]    b__0__reset;

          Bits32OutDrivenComp_noparam b__0
          (
            .clk            (         b__0__clk         ),
            .out            (         b__0__out         ),
            .reset          (        b__0__reset        )
          );

          logic [0:0]    b__1__clk;
          logic [31:0]   b__1__out;
          logic [0:0]    b__1__reset;

          Bits32OutDrivenComp_noparam b__1
          (
            .clk            (         b__1__clk         ),
            .out            (         b__1__out         ),
            .reset          (        b__1__reset        )
          );

          logic [0:0]    b__2__clk;
          logic [31:0]   b__2__out;
          logic [0:0]    b__2__reset;

          Bits32OutDrivenComp_noparam b__2
          (
            .clk            (         b__2__clk         ),
            .out            (         b__2__out         ),
            .reset          (        b__2__reset        )
          );

          logic [0:0]    b__3__clk;
          logic [31:0]   b__3__out;
          logic [0:0]    b__3__reset;

          Bits32OutDrivenComp_noparam b__3
          (
            .clk            (         b__3__clk         ),
            .out            (         b__3__out         ),
            .reset          (        b__3__reset        )
          );

          logic [0:0]    b__4__clk;
          logic [31:0]   b__4__out;
          logic [0:0]    b__4__reset;

          Bits32OutDrivenComp_noparam b__4
          (
            .clk            (         b__4__clk         ),
            .out            (         b__4__out         ),
            .reset          (        b__4__reset        )
          );

          // Connect struct/array ports and their wire forms
          assign b__0__clk = b__clk[0];
          assign b__1__clk = b__clk[1];
          assign b__2__clk = b__clk[2];
          assign b__3__clk = b__clk[3];
          assign b__4__clk = b__clk[4];
          assign b__out[0] = b__0__out;
          assign b__out[1] = b__1__out;
          assign b__out[2] = b__2__out;
          assign b__out[3] = b__3__out;
          assign b__out[4] = b__4__out;
          assign b__0__reset = b__reset[0];
          assign b__1__reset = b__reset[1];
          assign b__2__reset = b__reset[2];
          assign b__3__reset = b__reset[3];
          assign b__4__reset = b__reset[4];

          // Connections
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

CaseBehavioralArraySubCompArrayStructIfcComp = set_attributes( CaseBehavioralArraySubCompArrayStructIfcComp,
    'REF_UPBLK',
    '''\
        integer __loopvar__upblk_i;
        integer __loopvar__upblk_j;

        always_comb begin : upblk
          for ( __loopvar__upblk_i = 1'd0; __loopvar__upblk_i < 2'd2; __loopvar__upblk_i = __loopvar__upblk_i + 1'd1 )
            for ( __loopvar__upblk_j = 1'd0; __loopvar__upblk_j < 1'd1; __loopvar__upblk_j = __loopvar__upblk_j + 1'd1 )
              b__ifc__foo__foo[1'(__loopvar__upblk_i)][1'(__loopvar__upblk_j)][1'd0] = in_;
          out = b__out[1'd1];
        end
    ''',
    'REF_SRC',
    '''\
        module Bits32ArrayStructIfcComp_noparam
        (
          input  logic [0:0]    clk,
          output logic [31:0]   out,
          input  logic [0:0]    reset,
          input  logic [31:0]   ifc__0__foo__0__foo
        );
          logic [31:0]   ifc__foo__foo [0:0][0:0];
          logic [31:0]   ifc__foo [0:0][0:0];

          assign ifc__foo__foo[0][0] = ifc__0__foo__0__foo;
          assign ifc__foo[0][0][31:0] = ifc__0__foo__0__foo;
          assign out = ifc__foo__foo[0][0];

        endmodule

        module DUT_noparam
        (
          input  logic [0:0]    clk,
          input  logic [31:0]   in_,
          output logic [31:0]   out,
          input  logic [0:0]    reset
        );
          logic [0:0]    b__clk [0:1];
          logic [31:0]   b__out [0:1];
          logic [0:0]    b__reset [0:1];
          logic [31:0]   b__ifc__foo__foo [0:1][0:0][0:0];
          logic [31:0]   b__ifc__foo [0:1][0:0][0:0];

          logic [0:0]    b__0__clk;
          logic [31:0]   b__0__out;
          logic [0:0]    b__0__reset;
          logic [31:0]   b__0__ifc__0__foo__0__foo;

          Bits32ArrayStructIfcComp_noparam b__0
          (
            .clk            (         b__0__clk          ),
            .out            (         b__0__out          ),
            .reset          (        b__0__reset         ),
            .ifc__0__foo__0__foo( b__0__ifc__0__foo__0__foo  )
          );

          logic [0:0]    b__1__clk;
          logic [31:0]   b__1__out;
          logic [0:0]    b__1__reset;
          logic [31:0]   b__1__ifc__0__foo__0__foo;

          Bits32ArrayStructIfcComp_noparam b__1
          (
            .clk            (         b__1__clk          ),
            .out            (         b__1__out          ),
            .reset          (        b__1__reset         ),
            .ifc__0__foo__0__foo( b__1__ifc__0__foo__0__foo  )
          );

          assign b__0__clk = b__clk[0];
          assign b__1__clk = b__clk[1];
          assign b__out[0] = b__0__out;
          assign b__out[1] = b__1__out;
          assign b__0__reset = b__reset[0];
          assign b__1__reset = b__reset[1];
          assign b__0__ifc__0__foo__0__foo = b__ifc__foo__foo[0][0][0];
          assign b__1__ifc__0__foo__0__foo = b__ifc__foo__foo[1][0][0];
          assign b__0__ifc__0__foo__0__foo = b__ifc__foo[0][0][0][31:0];
          assign b__1__ifc__0__foo__0__foo = b__ifc__foo[1][0][0][31:0];

          integer __loopvar__upblk_i;
          integer __loopvar__upblk_j;

          always_comb begin : upblk
            for ( __loopvar__upblk_i = 1'd0; __loopvar__upblk_i < 2'd2; __loopvar__upblk_i = __loopvar__upblk_i + 1'd1  )
              for ( __loopvar__upblk_j = 1'd0; __loopvar__upblk_j < 1'd1; __loopvar__upblk_j = __loopvar__upblk_j + 1'd1  )
                b__ifc__foo__foo[1'(__loopvar__upblk_i)][1'(__loopvar__upblk_j)][1'd0] = in_;
            out = b__out[1'd1];
          end

          assign b__clk[0] = clk;
          assign b__reset[0] = reset;
          assign b__clk[1] = clk;
          assign b__reset[1] = reset;

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
        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out1,
          output logic [31:0] out2__foo,
          output logic [31:0] out3__foo,
          input logic [0:0] reset
        );

        logic [31:0] out2;
        logic [31:0] out3;

          always_comb begin : upblk
            out1 = 32'd42;
            out2 = 32'd1;
            out3 = 32'd1;
          end

        assign out2__foo = out2[31:0];
        assign out3__foo = out3[31:0];

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
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in___foo,
          output logic [31:0] out,
          input logic [0:0] reset
        );

          logic [31:0] in_;

          always_comb begin : upblk
            out = in_;
          end

          assign in_[31:0] = in___foo;

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
        module DUT_noparam
        (
          input logic [0:0] clk,
          input logic [31:0] in_,
          output logic [31:0] out__foo,
          input logic [0:0] reset
        );

          logic [31:0] out;

          always_comb begin : upblk
            out = in_;
          end

          assign out__foo = out[31:0];

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
        module DUT_noparam
        (
          input logic [0:0] clk,
          output logic [31:0] out__foo,
          input logic [0:0] reset
        );

          logic [31:0] out;

          always_comb begin : upblk
            out = 32'd42;
          end

          assign out__foo = out[31:0];

        endmodule
    '''
)
