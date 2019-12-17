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

#-------------------------------------------------------------------------
# Helper functions that create tv_in and tv_out
#-------------------------------------------------------------------------

# args: [attr, Bits, idx]
def _set( *args ):
  local_dict = {}
  assert len(args) % 3 == 0
  _tv_in_str = 'def tv_in( m, tv ):  \n'
  if len(args) == 0:
    _tv_in_str += '  pass'
  for attr, Bits, idx in zip( args[0::3], args[1::3], args[2::3] ):
    _tv_in_str += f'  m.{attr} = {Bits.__name__}( tv[{idx}] )\n'
  exec( _tv_in_str, globals(), local_dict )
  return local_dict['tv_in']

# args: [attr, Bits, idx]
def _check( *args ):
  local_dict = {}
  assert len(args) % 3 == 0
  _tv_out_str = 'def tv_out( m, tv ):  \n'
  if len(args) == 0:
    _tv_out_str += '  pass'
  for attr, Bits, idx in zip( args[0::3], args[1::3], args[2::3] ):
    _tv_out_str += f'  assert m.{attr} == {Bits.__name__}( tv[{idx}] )\n'
  exec( _tv_out_str, globals(), local_dict )
  return local_dict['tv_out']

CasePassThroughComp = add_attributes( CasePassThroughComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_;
        end
    ''',
    'TV_IN',
    _set( 'in_', Bits32, 0 ),
    'TV_OUT',
    _check( 'out', Bits32, 1 ),
    'TEST_VECTOR',
    [
        [    0,    0 ],
        [   42,   42 ],
        [   24,   24 ],
        [   -2,   -2 ],
        [   -1,   -1 ],
    ]
)

CaseSequentialPassThroughComp = add_attributes( CaseSequentialPassThroughComp,
    'REF_UPBLK',
    '''\
        always_ff @(posedge clk) begin : upblk
          out <= in_;
        end
    ''',
    'TV_IN',
    _set( 'in_', Bits32, 0 ),
    'TV_OUT',
    _check( 'out', Bits32, 1 ),
    'TEST_VECTOR',
    [
        [    0,     0 ],
        [   42,     0 ],
        [   24,    42 ],
        [   -2,    24 ],
        [   -1,    -2 ],
    ]
)

CaseBits32x2ConcatComp = add_attributes( CaseBits32x2ConcatComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_1, in_2 };
        end
    ''',
    'TV_IN',
    _set(
        'in_1', Bits32, 0,
        'in_2', Bits32, 1,
    ),
    'TV_OUT',
    _check( 'out', Bits64, 2 ),
    'TEST_VECTOR',
    [
        [    0,    0,     concat(    Bits32(0),     Bits32(0) ) ],
        [   42,    0,     concat(   Bits32(42),     Bits32(0) ) ],
        [   42,   42,     concat(   Bits32(42),    Bits32(42) ) ],
        [   -1,   42,     concat(   Bits32(-1),    Bits32(42) ) ],
    ]
)

CaseBits32x2ConcatConstComp = add_attributes( CaseBits32x2ConcatConstComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { 32'd42, 32'd0 };
        end
    ''',
    'TV_IN',
    _set(),
    'TV_OUT',
    _check( 'out', Bits64, 0 ),
    'TEST_VECTOR',
    [
        [    concat(    Bits32(42),    Bits32(0) ) ],
    ]
)

CaseBits32x2ConcatMixedComp = add_attributes( CaseBits32x2ConcatMixedComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_, 32'd0 };
        end
    ''',
    'TV_IN',
    _set( 'in_', Bits32, 0 ),
    'TV_OUT',
    _check( 'out', Bits64, 1 ),
    'TEST_VECTOR',
    [
        [  42,  concat(    Bits32(42),    Bits32(0) ) ],
        [  -1,  concat(    Bits32(-1),    Bits32(0) ) ],
        [  -2,  concat(    Bits32(-2),    Bits32(0) ) ],
        [   2,  concat(     Bits32(2),    Bits32(0) ) ],
    ]
)

CaseBits64SextInComp = add_attributes( CaseBits64SextInComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { { 32 { in_[31] } }, in_ };
        end
    ''',
    'TV_IN',
    _set( 'in_', Bits32, 0 ),
    'TV_OUT',
    _check( 'out', Bits64, 1 ),
    'TEST_VECTOR',
    [
        [  42,   sext(    Bits32(42),    64 ) ],
        [  -2,   sext(    Bits32(-2),    64 ) ],
        [  -1,   sext(    Bits32(-1),    64 ) ],
        [   2,   sext(     Bits32(2),    64 ) ],
    ]
)

CaseBits64ZextInComp = add_attributes( CaseBits64ZextInComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { { 32 { 1'b0 } }, in_ };
        end
    ''',
    'TV_IN',
    _set( 'in_', Bits32, 0 ),
    'TV_OUT',
    _check( 'out', Bits64, 1 ),
    'TEST_VECTOR',
    [
        [  42,   zext(    Bits32(42),    64 ) ],
        [  -2,   zext(    Bits32(-2),    64 ) ],
        [  -1,   zext(    Bits32(-1),    64 ) ],
        [   2,   zext(     Bits32(2),    64 ) ],
    ]
)

CaseBits32x2ConcatFreeVarComp = add_attributes( CaseBits32x2ConcatFreeVarComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_, __const__STATE_IDLE };
        end
    ''',
    'TV_IN',
    _set( 'in_', Bits32, 0 ),
    'TV_OUT',
    _check( 'out', Bits64, 1 ),
    'TEST_VECTOR',
    [
        [  42,  concat(    Bits32(42),    Bits32(42) ) ],
        [  -1,  concat(    Bits32(-1),    Bits32(42) ) ],
        [  -2,  concat(    Bits32(-2),    Bits32(42) ) ],
        [   2,  concat(     Bits32(2),    Bits32(42) ) ],
    ]
)

CaseBits32x2ConcatUnpackedSignalComp = add_attributes( CaseBits32x2ConcatUnpackedSignalComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_[0], in_[1] };
        end
    ''',
    'TV_IN',
    _set(
        'in_[0]', Bits32, 0,
        'in_[1]', Bits32, 1,
    ),
    'TV_OUT',
    _check( 'out', Bits64, 2 ),
    'TEST_VECTOR',
    [
        [  42,   2,  concat(    Bits32(42),     Bits32(2) ) ],
        [  -1,  42,  concat(    Bits32(-1),    Bits32(42) ) ],
        [  -2,  -1,  concat(    Bits32(-2),    Bits32(-1) ) ],
        [   2,  -2,  concat(     Bits32(2),    Bits32(-2) ) ],
    ]
)

CaseBits32BitSelUpblkComp = add_attributes( CaseBits32BitSelUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_[1];
        end
    ''',
    'TV_IN',
    _set( 'in_', Bits32, 0 ),
    'TV_OUT',
    _check( 'out', Bits1, 1 ),
    'TEST_VECTOR',
    [
        [   0,   0 ],
        [  -1,   1 ],
        [  -2,   1 ],
        [   2,   1 ],
    ]
)

CaseBits64PartSelUpblkComp = add_attributes( CaseBits64PartSelUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_[35:4];
        end
    ''',
    'TV_IN',
    _set( 'in_', Bits64, 0 ),
    'TV_OUT',
    _check( 'out', Bits32, 1 ),
    'TEST_VECTOR',
    [
        [   -1,   -1 ],
        [   -2,   -1 ],
        [   -4,   -1 ],
        [   -8,   -1 ],
        [  -16,   -1 ],
        [  -32,   -2 ],
        [  -64,   -4 ],
    ]
)

CaseReducesInx3OutComp = add_attributes( CaseReducesInx3OutComp,
    'REF_UPBLK',
    '''\
        always_comb begin : v_reduce
          out = ( ( & in_1 ) & ( | in_2 ) ) | ( ^ in_3 );
        end
    ''',
    'TV_IN',
    _set(
        'in_1', Bits32, 0,
        'in_2', Bits32, 1,
        'in_3', Bits32, 2,
    ),
    'TV_OUT',
    _check( 'out', Bits1, 3 ),
    'TEST_VECTOR',
    [
        [  0,   1,    2,  1   ],
        [ -1,   1,   -1,  1   ],
        [  9,   8,    7,  1   ],
        [  9,   8,    0,  0   ],
    ]
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
    'TV_IN',
    _set( 'in_', Bits16, 0 ),
    'TV_OUT',
    _check( 'out', Bits8, 1 ),
    'TEST_VECTOR',
    [
        [ 255,   0, ],
        [  -1, 255, ],
        [ 511,   1, ],
        [ 254,   0, ],
        [  42,   0, ],
        [   0,   0, ],
    ]
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
    'TV_IN',
    _set(
        'in_1', Bits32, 0,
        'in_2', Bits32, 1,
    ),
    'TV_OUT',
    _check( 'out', Bits32, 2 ),
    'TEST_VECTOR',
    [
        [    0,    -1,  -1 ],
        [   42,     0,   0 ],
        [   24,    42,  42 ],
        [   -2,    24,  24 ],
        [   -1,    -2,  -2 ],
    ]
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
    'TV_IN',
    _set(
        'in_1', Bits32, 0,
        'in_2', Bits32, 1,
    ),
    'TV_OUT',
    _check( 'out', Bits32, 2 ),
    'TEST_VECTOR',
    [
        [    0,    -1,   0 ],
        [   42,     0,   0 ],
        [   24,    42,   0 ],
        [   -2,    24,   0 ],
        [   -1,    -2,   0 ],
    ]
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
    'TV_IN',
    _set(
        'in_1', Bits32, 0,
        'in_2', Bits32, 1,
        'in_3', Bits32, 2,
    ),
    'TV_OUT',
    _check( 'out', Bits32, 3 ),
    'TEST_VECTOR',
    [
        [    0,    -1,   0,  0 ],
        [   42,     0,  42, 42 ],
        [   24,    42,  24, 24 ],
        [   -2,    24,  -2, -2 ],
        [   -1,    -2,  -1, -1 ],
    ]
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
    'TV_IN',
    _set(
        'in_1', Bits32, 0,
        'in_2', Bits32, 1,
        'in_3', Bits32, 2,
    ),
    'TV_OUT',
    _check( 'out', Bits32, 3 ),
    'TEST_VECTOR',
    [
        [    0,    -1,   0,  -1 ],
        [   42,     0,  42,   0 ],
        [   24,    42,  24,  42 ],
        [   -2,    24,  -2,  24 ],
        [   -1,    -2,  -1,  -2 ],
    ]
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
    'TV_IN',
    _set(
        'in_[0]', Bits32, 0,
        'in_[1]', Bits32, 1,
        'in_[2]', Bits32, 2,
        'in_[3]', Bits32, 3,
        'in_[4]', Bits32, 4,
    ),
    'TV_OUT',
    _check(
        'out[0]', Bits32, 5,
        'out[1]', Bits32, 6,
        'out[2]', Bits32, 7,
        'out[3]', Bits32, 8,
        'out[4]', Bits32, 9,
    ),
    'TEST_VECTOR',
    [
        [    0,    -1,   0,  -1,   0,    0,    -1,   0,  -1,   0, ],
        [   42,     0,  42,   0,  42,   42,     0,  42,   0,  42, ],
        [   24,    42,  24,  42,  24,   24,    42,  24,  42,  24, ],
        [   -2,    24,  -2,  24,  -2,   -2,    24,  -2,  24,  -2, ],
        [   -1,    -2,  -1,  -2,  -1,   -1,    -2,  -1,  -2,  -1, ],
    ]
)

CaseIfExpInForStmtComp = add_attributes( CaseIfExpInForStmtComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int i = 0; i < 5; i += 1 )
            out[i] = ( i == 1 ) ? in_[i] : in_[0];
        end
    ''',
    'TV_IN',
    _set(
        'in_[0]', Bits32, 0,
        'in_[1]', Bits32, 1,
        'in_[2]', Bits32, 2,
        'in_[3]', Bits32, 3,
        'in_[4]', Bits32, 4,
    ),
    'TV_OUT',
    _check(
        'out[0]', Bits32, 5,
        'out[1]', Bits32, 6,
        'out[2]', Bits32, 7,
        'out[3]', Bits32, 8,
        'out[4]', Bits32, 9,
    ),
    'TEST_VECTOR',
    [
        [    0,    -1,   0,  -1,   0,    0,    -1,   0,   0,   0, ],
        [   42,     0,  42,   0,  42,   42,     0,  42,  42,  42, ],
        [   24,    42,  24,  42,  24,   24,    42,  24,  24,  24, ],
        [   -2,    24,  -2,  24,  -2,   -2,    24,  -2,  -2,  -2, ],
        [   -1,    -2,  -1,  -2,  -1,   -1,    -2,  -1,  -1,  -1, ],
    ]
)

CaseIfExpUnaryOpInForStmtComp = add_attributes( CaseIfExpUnaryOpInForStmtComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int i = 0; i < 5; i += 1 )
            out[i] = ( i == 1 ) ? ~in_[i] : in_[0];
        end
    ''',
    'TV_IN',
    _set(
        'in_[0]', Bits32, 0,
        'in_[1]', Bits32, 1,
        'in_[2]', Bits32, 2,
        'in_[3]', Bits32, 3,
        'in_[4]', Bits32, 4,
    ),
    'TV_OUT',
    _check(
        'out[0]', Bits32, 5,
        'out[1]', Bits32, 6,
        'out[2]', Bits32, 7,
        'out[3]', Bits32, 8,
        'out[4]', Bits32, 9,
    ),
    'TEST_VECTOR',
    [
        [    0,    -1,   0,  -1,   0,    0,    ~-1,   0,   0,   0, ],
        [   42,     0,  42,   0,  42,   42,     ~0,  42,  42,  42, ],
        [   24,    42,  24,  42,  24,   24,    ~42,  24,  24,  24, ],
        [   -2,    24,  -2,  24,  -2,   -2,    ~24,  -2,  -2,  -2, ],
        [   -1,    -2,  -1,  -2,  -1,   -1,    ~-2,  -1,  -1,  -1, ],
    ]
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
    'TV_IN',
    _set(
        'in_[0]', Bits32, 0,
        'in_[1]', Bits32, 1,
        'in_[2]', Bits32, 2,
        'in_[3]', Bits32, 3,
        'in_[4]', Bits32, 4,
    ),
    'TV_OUT',
    _check(
        'out[0]', Bits32, 5,
        'out[1]', Bits32, 6,
        'out[2]', Bits32, 7,
        'out[3]', Bits32, 8,
        'out[4]', Bits32, 9,
    ),
    'TEST_VECTOR',
    [
        [    0,    -1,   0,  -1,   0,     0,     0,    0,    0,    0, ],
        [   42,     0,  42,   0,  42,     0,     0,    0,    0,   42, ],
        [   24,    42,  24,  42,  24,    24,    42,   24,   42,   24, ],
        [   -2,    24,  -2,  24,  -2,    -2,    24,   -2,   24,   -2, ],
        [   -1,    -2,  -1,  -2,  -1,    -1,    -2,   -1,   -2,   -1, ],
    ]
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
    'TV_IN',
    _set(
        'in_[0]', Bits32, 0,
        'in_[1]', Bits32, 1,
        'in_[2]', Bits32, 2,
        'in_[3]', Bits32, 3,
        'in_[4]', Bits32, 4,
    ),
    'TV_OUT',
    _check(
        'out[0]', Bits32, 5,
        'out[1]', Bits32, 6,
        'out[2]', Bits32, 7,
        'out[3]', Bits32, 8,
        'out[4]', Bits32, 9,
    ),
    'TEST_VECTOR',
    [
        [    0,    -1,   0,  -1,   0,     0,     0,    0,    0,    0, ],
        [   42,     0,  42,   0,  42,     0,     0,    0,    0,   42, ],
        [   24,    42,  24,  42,  24,    24,    42,   24,   42,   24, ],
        [   -2,    24,  -2,  24,  -2,    -2,    24,   -2,   24,   -2, ],
        [   -1,    -2,  -1,  -2,  -1,    -1,    -2,   -1,   -2,   -1, ],
    ]
)

CaseFixedSizeSliceComp = add_attributes( CaseFixedSizeSliceComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          for ( int i = 0; i < 2; i += 1 )
            out[i] = in_[i * 8 +: 8];
        end
    ''',
    'TV_IN',
    _set( 'in_', Bits16, 0 ),
    'TV_OUT',
    _check(
        'out[0]', Bits8, 1,
        'out[1]', Bits8, 2,
    ),
    'TEST_VECTOR',
    [
        [     -1, 0xff, 0xff ],
        [      1, 0x01, 0x00 ],
        [      7, 0x07, 0x00 ],
        [ 0xff00, 0x00, 0xff ],
        [ 0x3412, 0x12, 0x34 ],
        [ 0x9876, 0x76, 0x98 ],
    ]
)

CaseBits32FooInBits32OutComp = add_attributes( CaseBits32FooInBits32OutComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_.foo;
        end
    ''',
    'TV_IN',
    _set( 'in_', Bits32Foo, 0 ),
    'TV_OUT',
    _check( 'out', Bits32, 1 ),
    'TEST_VECTOR',
    [
        [     Bits32Foo(),   0 ],
        [    Bits32Foo(0),   0 ],
        [   Bits32Foo(-1),  -1 ],
        [   Bits32Foo(42),  42 ],
        [   Bits32Foo(-2),  -2 ],
        [   Bits32Foo(10),  10 ],
        [  Bits32Foo(256), 256 ],
    ]
)

CaseConstStructInstComp = add_attributes( CaseConstStructInstComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in_.foo;
        end
    ''',
    'TV_IN',
    _set(),
    'TV_OUT',
    _check( 'out', Bits32, 0 ),
    'TEST_VECTOR',
    [
        [ 0 ],
    ]
)

CaseStructPackedArrayUpblkComp = add_attributes( CaseStructPackedArrayUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_.foo[0], in_.foo[1], in_.foo[2] };
        end
    ''',
    'TV_IN',
    _set( 'in_', Bits32x5Foo, 0 ),
    'TV_OUT',
    _check( 'out', Bits96, 1 ),
    'TEST_VECTOR',
    [
        [  Bits32x5Foo([ b32(0), b32(0), b32(0), b32(0),b32(0) ] ), concat( b32(0),   b32(0),   b32(0)  ) ],
        [  Bits32x5Foo([ b32(-1),b32(-1),b32(-1),b32(0),b32(0) ] ), concat( b32(-1),  b32(-1),  b32(-1) ) ],
        [  Bits32x5Foo([ b32(42),b32(42),b32(-1),b32(0),b32(0) ] ), concat( b32(42),  b32(42),  b32(-1) ) ],
        [  Bits32x5Foo([ b32(42),b32(42),b32(42),b32(0),b32(0) ] ), concat( b32(42),  b32(42),  b32(42) ) ],
        [  Bits32x5Foo([ b32(-1),b32(-1),b32(42),b32(0),b32(0) ] ), concat( b32(-1),  b32(-1),  b32(42) ) ],
    ]
)

CaseNestedStructPackedArrayUpblkComp = add_attributes( CaseNestedStructPackedArrayUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = { in_.bar[0], in_.woo.foo, in_.foo };
        end
    ''',
    'TV_IN',
    _set( 'in_', NestedStructPackedPlusScalar, 0 ),
    'TV_OUT',
    _check( 'out', Bits96, 1 ),
    'TEST_VECTOR',
    [
        [   NestedStructPackedPlusScalar(0, [ Bits32(0) , Bits32(0)  ], Bits32Foo(5) ), concat(   Bits32(0), Bits32(5),   Bits32(0) ) ],
        [  NestedStructPackedPlusScalar(-1, [ Bits32(-1), Bits32(-2) ], Bits32Foo(6) ), concat(  Bits32(-1), Bits32(6),  Bits32(-1) ) ],
        [  NestedStructPackedPlusScalar(-1, [ Bits32(42), Bits32(43) ], Bits32Foo(7) ), concat(  Bits32(42), Bits32(7),  Bits32(-1) ) ],
        [  NestedStructPackedPlusScalar(42, [ Bits32(42), Bits32(43) ], Bits32Foo(8) ), concat(  Bits32(42), Bits32(8),  Bits32(42) ) ],
        [  NestedStructPackedPlusScalar(42, [ Bits32(-1), Bits32(-2) ], Bits32Foo(9) ), concat(  Bits32(-1), Bits32(9),  Bits32(42) ) ],
    ]
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
    'TV_IN',
    _set(
        'in_.val', Bits1, 0,
        'in_.msg', Bits32, 1,
    ),
    'TV_OUT',
    _check(
        'in_.rdy', Bits1, 0,
        'out.val', Bits1, 2,
        'out.msg', Bits32, 3,
    ),
    'TEST_VECTOR',
    [
        [   1,      0,   1,      0 ],
        [   0,     42,   0,     42 ],
        [   1,     42,   1,     42 ],
        [   1,     -1,   1,     -1 ],
        [   1,     -2,   1,     -2 ],
    ]
)

CaseArrayBits32IfcInUpblkComp = add_attributes( CaseArrayBits32IfcInUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = in___1__foo;
        end
    ''',
    'TV_IN',
    _set(
        'in_[0].foo', Bits32, 0,
        'in_[1].foo', Bits32, 1,
    ),
    'TV_OUT',
    _check( 'out', Bits32, 2 ),
    'TEST_VECTOR',
    [
        [    0,    0,      0 ],
        [    0,   42,     42 ],
        [   24,   42,     42 ],
        [   -2,   -1,     -1 ],
        [   -1,   -2,     -2 ],
    ]
)

CaseBits32SubCompAttrUpblkComp = add_attributes( CaseBits32SubCompAttrUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = b__out;
        end
    ''',
    'TV_IN',
    _set(),
    'TV_OUT',
    _check( 'out', Bits32, 0 ),
    'TEST_VECTOR',
    [
        [ 42 ],
    ]
)

CaseBits32ArraySubCompAttrUpblkComp = add_attributes( CaseBits32ArraySubCompAttrUpblkComp,
    'REF_UPBLK',
    '''\
        always_comb begin : upblk
          out = b__1__out;
        end
    ''',
    'TV_IN',
    _set(),
    'TV_OUT',
    _check( 'out', Bits32, 0 ),
    'TEST_VECTOR',
    [
        [ 42 ],
    ]
)
