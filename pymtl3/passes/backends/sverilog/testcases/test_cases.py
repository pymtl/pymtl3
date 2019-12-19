"""
=========================================================================
test_cases.py
=========================================================================
Centralized test case repository for the SystemVerilog backend.

Author : Peitian Pan
Date   : Dec 16, 2019
"""

from textwrap import dedent

from pymtl3 import *
from pymtl3.testcases import add_attributes, \
      CasePassThroughComp, CaseSequentialPassThroughComp, \
      CaseBits32x2ConcatComp, CaseBits32x2ConcatConstComp, \
      CaseBits32x2ConcatMixedComp, CaseBits64SextInComp, \
      CaseBits64ZextInComp, CaseBits32x2ConcatFreeVarComp, \
      CaseBits32x2ConcatUnpackedSignalComp, CaseBits32BitSelUpblkComp, \
      CaseBits64PartSelUpblkComp, CaseSVerilogReservedComp, \
      CaseReducesInx3OutComp, CaseIfBasicComp, CaseIfDanglingElseInnerComp, \
      CaseIfDanglingElseOutterComp, CaseElifBranchComp, CaseNestedIfComp, \
      CaseForRangeLowerUpperStepPassThroughComp, CaseIfExpInForStmtComp, \
      CaseIfBoolOpInForStmtComp, CaseIfTmpVarInForStmtComp, CaseFixedSizeSliceComp, \
      CaseIfExpUnaryOpInForStmtComp, Bits32Foo, NestedStructPackedPlusScalar, \
      CaseBits32FooInBits32OutComp, CaseConstStructInstComp, \
      CaseStructPackedArrayUpblkComp, CaseNestedStructPackedArrayUpblkComp, \
      Bits32x5Foo, CaseConnectValRdyIfcUpblkComp, CaseArrayBits32IfcInUpblkComp, \
      CaseInterfaceArrayNonStaticIndexComp, \
      CaseBits32SubCompAttrUpblkComp, CaseBits32ArraySubCompAttrUpblkComp

CasePassThroughComp = add_attributes( CasePassThroughComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_;
        end
    ''',
)

CaseSequentialPassThroughComp = add_attributes( CaseSequentialPassThroughComp,
    'REF_UPBLK',
    '''\
        always_ff @(posedge clk) begin : upblk
          out <= in_;
        end
    ''',
)

CaseBits32x2ConcatComp = add_attributes( CaseBits32x2ConcatComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_1, in_2 };
        end
    ''',
)

CaseBits32x2ConcatConstComp = add_attributes( CaseBits32x2ConcatConstComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { 32'd42, 32'd0 };
        end
    ''',
)

CaseBits32x2ConcatMixedComp = add_attributes( CaseBits32x2ConcatMixedComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_, 32'd0 };
        end
    ''',
)

CaseBits64SextInComp = add_attributes( CaseBits64SextInComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { { 32 { in_[31] } }, in_ };
        end
    ''',
)

CaseBits64ZextInComp = add_attributes( CaseBits64ZextInComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { { 32 { 1'b0 } }, in_ };
        end
    ''',
)

CaseBits32x2ConcatFreeVarComp = add_attributes( CaseBits32x2ConcatFreeVarComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_, __const__STATE_IDLE };
        end
    ''',
)

CaseBits32x2ConcatUnpackedSignalComp = add_attributes( CaseBits32x2ConcatUnpackedSignalComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_[0], in_[1] };
        end
    ''',
)

CaseBits32BitSelUpblkComp = add_attributes( CaseBits32BitSelUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_[1];
        end
    ''',
)

CaseBits64PartSelUpblkComp = add_attributes( CaseBits64PartSelUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_[35:4];
        end
    ''',
)

CaseReducesInx3OutComp = add_attributes( CaseReducesInx3OutComp,
    'REF_UPBLK',
    '''\
        always_comb begin : v_reduce
          out = ( ( & in_1 ) & ( | in_2 ) ) | ( ^ in_3 );
        end
    ''',
)

CaseIfBasicComp = add_attributes( CaseIfBasicComp,
    'REF_UPBLK',
    '''\
        always_comb begin : if_basic
          if ( in_[7:0] == 8'd255 ) begin
            out = in_[15:8];
          end
          else
            out = 8'd0;
        end
    ''',
)

CaseIfDanglingElseInnerComp = add_attributes( CaseIfDanglingElseInnerComp,
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
)

CaseIfDanglingElseOutterComp = add_attributes( CaseIfDanglingElseOutterComp,
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
)

CaseElifBranchComp = add_attributes( CaseElifBranchComp,
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
)

CaseNestedIfComp = add_attributes( CaseNestedIfComp,
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
)

CaseForRangeLowerUpperStepPassThroughComp = add_attributes( CaseForRangeLowerUpperStepPassThroughComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int i = 0; i < 5; i += 2 )
            out[i] = in_[i];
          for ( int i = 1; i < 5; i += 2 )
            out[i] = in_[i];
        end
    ''',
)

CaseIfExpInForStmtComp = add_attributes( CaseIfExpInForStmtComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int i = 0; i < 5; i += 1 )
            out[i] = ( i == 1 ) ? in_[i] : in_[0];
        end
    ''',
)

CaseIfExpUnaryOpInForStmtComp = add_attributes( CaseIfExpUnaryOpInForStmtComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int i = 0; i < 5; i += 1 )
            out[i] = ( i == 1 ) ? ~in_[i] : in_[0];
        end
    ''',
)

CaseIfBoolOpInForStmtComp = add_attributes( CaseIfBoolOpInForStmtComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int i = 0; i < 5; i += 1 )
            if ( ( in_[i] != 32'd0 ) && ( ( i < 4 ) ? in_[i + 1] != 32'd0 : in_[4] != 32'd0 ) ) begin
              out[i] = in_[i];
            end
            else
              out[i] = 32'd0;
        end
    ''',
)

CaseIfTmpVarInForStmtComp = add_attributes( CaseIfTmpVarInForStmtComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int i = 0; i < 5; i += 1 ) begin
            if ( ( in_[i] != 32'd0 ) && ( ( i < 4 ) ? in_[i + 1] != 32'd0 : in_[4] != 32'd0 ) ) begin
              __tmpvar__upblk_tmpvar = in_[i];
            end
            else
              __tmpvar__upblk_tmpvar = 32'd0;
            out[i] = __tmpvar__upblk_tmpvar;
          end
        end
    ''',
)

CaseFixedSizeSliceComp = add_attributes( CaseFixedSizeSliceComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int i = 0; i < 2; i += 1 )
            out[i] = in_[i * 8 +: 8];
        end
    ''',
)

CaseBits32FooInBits32OutComp = add_attributes( CaseBits32FooInBits32OutComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_.foo;
        end
    ''',
)

CaseConstStructInstComp = add_attributes( CaseConstStructInstComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_.foo;
        end
    ''',
)

CaseStructPackedArrayUpblkComp = add_attributes( CaseStructPackedArrayUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_.foo[0], in_.foo[1], in_.foo[2] };
        end
    ''',
)

CaseNestedStructPackedArrayUpblkComp = add_attributes( CaseNestedStructPackedArrayUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_.bar[0], in_.woo.foo, in_.foo };
        end
    ''',
)

CaseConnectValRdyIfcUpblkComp = add_attributes( CaseConnectValRdyIfcUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out__val = in___val;
          out__msg = in___msg;
          in___rdy = out__rdy;
        end
    ''',
)

CaseArrayBits32IfcInUpblkComp = add_attributes( CaseArrayBits32IfcInUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in___1__foo;
        end
    ''',
)

CaseBits32SubCompAttrUpblkComp = add_attributes( CaseBits32SubCompAttrUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = b__out;
        end
    ''',
)

CaseBits32ArraySubCompAttrUpblkComp = add_attributes( CaseBits32ArraySubCompAttrUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = b__1__out;
        end
    ''',
)
