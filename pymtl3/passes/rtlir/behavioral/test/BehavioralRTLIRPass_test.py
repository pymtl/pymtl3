#=========================================================================
# BehavioralRTLIRPass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 2, 2019
"""Test the behavioral RTLIR passes.

The generation, type check, and visualization passes are invoked. The
results of generation pass are verifed against a reference AST.
"""

# from pymtl3.datatypes import *
from pymtl3.passes.rtlir.behavioral import (
    BehavioralRTLIRGenPass,
    BehavioralRTLIRTypeCheckPass,
    BehavioralRTLIRVisualizationPass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIR import *
from pymtl3.passes.rtlir.behavioral.test.BehavioralRTLIRL1Pass_test import XFAIL_ON_PY3
from pymtl3.passes.rtlir.errors import PyMTLTypeError
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure
from pymtl3.passes.testcases import (
    CaseBits8Bits16MismatchAssignComp,
    CaseBits16ConstAddComp,
    CaseBits16IndexBasicComp,
    CaseBits32Bits64SlicingBasicComp,
    CaseConstSizeSlicingComp,
    CaseFlipFlopAdder,
    CaseForBasicComp,
    CaseIfBasicComp,
    CaseReducesInx3OutComp,
    CaseSlicingOverIndexComp,
    CaseSubCompAddComp,
    CaseTwoUpblksSliceComp,
)


def local_do_test( m ):
  """Check if generated behavioral RTLIR is the same as reference."""

  ref = m._rtlir_test_ref
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )
  m.apply( BehavioralRTLIRVisualizationPass() )

  for blk in m.get_update_blocks():
    assert\
      m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] == ref[ blk.__name__ ]

def test_reduce( do_test ):
  a = CaseReducesInx3OutComp.DUT()
  in_1 = Attribute( Base( a ), 'in_1' )
  in_2 = Attribute( Base( a ), 'in_2' )
  in_3 = Attribute( Base( a ), 'in_3' )
  out = Attribute( Base( a ), 'out' )

  a._rtlir_test_ref = { 'v_reduce' : CombUpblk( 'v_reduce', [
    Assign( out, BinOp(
      BinOp( Reduce( BitAnd(), in_1 ), BitAnd(), Reduce( BitOr(), in_2 ) ),
      BitOr(), Reduce( BitXor(), in_3 ),
    ), True )
  ] ) }

  # a._test_vector = [
  #         ' in_1        in_2     in_3     *out',
  #   [     Bits32,    Bits32,   Bits32,   Bits1    ],

  #   [          0,         1,        2,        1   ],
  #   [    b32(-1),         1,  b32(-1),        1   ],
  #   [          9,         8,        7,        1   ],
  # ]

  do_test( a )

def test_index_basic( do_test ):
  a = CaseBits16IndexBasicComp.DUT()

  a._rtlir_test_ref = { 'index_basic' : CombUpblk( 'index_basic', [
    Assign( Index( Attribute( Base( a ), 'out' ), Number( 0 ) ),
      BinOp( Index( Attribute( Base( a ), 'in_' ), Number( 0 ) ), Add(),
             Index( Attribute( Base( a ), 'in_' ), Number( 1 ) ) ), True ),
    Assign( Index( Attribute( Base( a ), 'out' ), Number( 1 ) ),
      BinOp( Index( Attribute( Base( a ), 'in_' ), Number( 2 ) ), Add(),
             Index( Attribute( Base( a ), 'in_' ), Number( 3 ) ) ), True )
  ] ) }

  # a._test_vector = [
  #         'in_[0]     in_[1]    in_[2]    in_[3]    *out[0]     *out[1]',
  #   [     Bits16,    Bits16,   Bits16,   Bits16,    Bits16,     Bits16 ],

  #   [          0,         1,        2,        3,         1,          5 ],
  #   [ Bits16(-1),         1, Bits16(-1),      1,         0,          0 ],
  #   [          9,         8,        7,        6,        17,         13 ],
  # ]

  do_test( a )

def test_mismatch_width_assign( do_test ):
  a = CaseBits8Bits16MismatchAssignComp.DUT()

  a._rtlir_test_ref = { 'mismatch_width_assign' : CombUpblk(
    'mismatch_width_assign', [ Assign(
      Attribute( Base( a ), 'out' ), Attribute( Base( a ), 'in_' ), True
    )
  ] ) }

  # a._test_vector = [
  #               'in_             *out',
  #   [        Bits16,           Bits8 ],

  #   [             0,               0 ],
  #   [             2,               2 ],
  #   [    Bits16(-1),       Bits8(-1) ],
  #   [    Bits16(-2),       Bits8(-2) ],
  #   [ Bits16(32767),      Bits8(255) ],
  # ]

  with expected_failure( PyMTLTypeError, "LHS and RHS of assignment" ):
    do_test( a )

def test_slicing_basic( do_test ):
  a = CaseBits32Bits64SlicingBasicComp.DUT()

  a._rtlir_test_ref = { 'slicing_basic' : CombUpblk( 'slicing_basic', [
    Assign( Slice( Attribute( Base( a ), 'out' ), Number( 0 ), Number( 16 ) ),
      Slice( Attribute( Base( a ), 'in_' ), Number( 16 ), Number( 32 ) ), True ),
    Assign( Slice( Attribute( Base( a ), 'out' ), Number( 16 ), Number( 32 ) ),
      Slice( Attribute( Base( a ), 'in_' ), Number( 0 ), Number( 16 ) ), True )
  ] ) }

  # a._test_vector = [
  #               'in_                        *out',
  #   [        Bits32,                     Bits64 ],

  #   [             0,                          0 ],
  #   [             2,            Bits64(0x20000) ],
  #   [    Bits32(-1),         Bits64(0xffffffff) ],
  #   [    Bits32(-2),         Bits64(0xfffeffff) ],
  #   [ Bits32(32767),         Bits64(0x7fff0000) ],
  # ]

  do_test( a )

def test_bits_basic( do_test ):
  a = CaseBits16ConstAddComp.DUT()

  a._rtlir_test_ref = { 'bits_basic' : CombUpblk( 'bits_basic', [
    Assign( Attribute( Base( a ), 'out' ),
      BinOp( Attribute( Base( a ), 'in_' ), Add(), SizeCast( 16, Number( 10 ) ) ), True )
  ] ) }

  # a._test_vector = [
  #               'in_              *out',
  #   [        Bits16,           Bits16 ],
  #   [             0,               10 ],
  #   [             2,               12 ],
  #   [    Bits16(-1),        Bits16(9) ],
  #   [    Bits16(-2),        Bits16(8) ],
  #   [Bits16(0x7FFF),   Bits16(0x8009) ],
  # ]

  do_test( a )

def test_index_bits_slicing( do_test ):
  a = CaseSlicingOverIndexComp.DUT()

  a._rtlir_test_ref = { 'index_bits_slicing' : CombUpblk( 'index_bits_slicing', [
    Assign( Slice(
      Index( Attribute( Base( a ), 'out' ), Number( 0 ) ),
      Number( 0 ), Number( 8 )
      ),
      BinOp(
        BinOp(
          Slice( Index( Attribute( Base( a ), 'in_' ), Number( 1 ) ), Number( 8 ), Number( 16 ) ),
          Add(),
          Slice( Index( Attribute( Base( a ), 'in_' ), Number( 2 ) ), Number( 0 ), Number( 8 ) ),
        ),
        Add(),
        SizeCast( 8, Number( 10 ) )
      ),
      True
    ),
    Assign(
      Index( Attribute( Base( a ), 'out' ), Number( 1 ) ),
      BinOp(
        BinOp(
          Slice( Index( Attribute( Base( a ), 'in_' ), Number( 3 ) ), Number( 0 ), Number( 16 ) ),
          Add(),
          Index( Attribute( Base( a ), 'in_' ), Number( 4 ) )
        ),
        Add(),
        SizeCast( 16, Number( 1 ) )
      ),
      True
    ),
  ] ) }

  # a._test_vector = [
  #     'in_[0] in_[1] in_[2] in_[3] in_[4] in_[5] in_[6] in_[7] in_[8] in_[9]\
  #         *out[0] *out[1] *out[2] *out[3] *out[4]',
  #   [ Bits16 ] * 15,

  #   # 8-bit truncation!
  #   [ Bits16(0xff) ] * 10 + [ Bits16(0x09), Bits16(0x01ff), 0, 0, 0 ],
  #   [ Bits16(0x00) ] * 10 + [ Bits16(0x0a), Bits16(0x0001), 0, 0, 0 ],
  # ]

  do_test( a )

def test_multi_components( do_test ):
  a = CaseSubCompAddComp.DUT()

  a._rtlir_test_ref = { 'multi_components_A' : CombUpblk( 'multi_components_A', [
    Assign( Attribute( Base( a ), 'out' ),
      BinOp(
        Attribute( Base( a ), 'in_' ),
        Add(),
        Attribute( Attribute( Base( a ), 'b' ), 'out' )
      ),
      True
    )
  ] ) }

  # a._test_vector = [
  #               'in_              *out',
  #   [ Bits16 ] *2,

  #   [             0,               0 ],
  #   [             2,               4 ],
  #   [    Bits16(-1),      Bits16(-2) ],
  #   [    Bits16(-2),      Bits16(-4) ],
  # ]

  do_test( a )

def test_if_basic( do_test ):
  a = CaseIfBasicComp.DUT()

  a._rtlir_test_ref = {
    'if_basic' : CombUpblk( 'if_basic', [ If(
      Compare( Slice( Attribute( Base( a ), 'in_' ), Number( 0 ), Number( 8 ) ), Eq(), SizeCast( 8, Number( 255 ) ) ),
      [ Assign( Attribute( Base( a ), 'out' ), Slice( Attribute( Base( a ), 'in_' ), Number( 8 ), Number( 16 ) ), True ) ],
      [ Assign( Attribute( Base( a ), 'out' ), SizeCast( 8, Number( 0 ) ), True ) ]
    )
  ] ) }

  # a._test_vector = [
  #               'in_              *out',
  #   [         Bits16,           Bits8 ],
  #   [           255,                0 ],
  #   [           511,                1 ],
  #   [           256,                0 ],
  # ]

  do_test( a )

@XFAIL_ON_PY3
def test_for_basic( do_test ):
  a = CaseForBasicComp.DUT()

  twice_i = BinOp( Number( 2 ), Mult(), LoopVar( 'i' ) )

  a._rtlir_test_ref = {
    'for_basic' : CombUpblk( 'for_basic', [ For(
      LoopVarDecl( 'i' ), Number( 0 ), Number( 8 ), Number( 1 ),
      [ Assign(
          Slice( Attribute( Base( a ), 'out' ), twice_i, BinOp( twice_i, Add(), Number( 1 ) ) ),
          BinOp(
            Slice( Attribute( Base( a ), 'in_' ), twice_i, BinOp( twice_i, Add(), Number( 1 ) ) ),
            Add(),
            Slice( Attribute( Base( a ), 'in_' ),
              BinOp( twice_i, Add(), Number( 1 ) ),
              BinOp( BinOp( twice_i, Add(), Number( 1 ) ), Add(), Number( 1 ) )
            )
          ),
          True
        )
      ]
    ) ] )
  }

  # a._test_vector = []

  do_test( a )

def test_multi_upblks( do_test ):
  a = CaseTwoUpblksSliceComp.DUT()

  a._rtlir_test_ref = { 'multi_upblks_1' : CombUpblk( 'multi_upblks_1', [
      Assign( Slice( Attribute( Base( a ), 'out' ), Number(0), Number(4) ), Attribute( Base( a ), 'in_' ), True ),
    ] ),
    'multi_upblks_2' : CombUpblk( 'multi_upblks_2', [
      Assign( Slice( Attribute( Base( a ), 'out' ), Number(4), Number(8) ), Attribute( Base( a ), 'in_' ), True ),
    ] )
  }

  # a._test_vector = [
  #               'in_              *out',
  #   [         Bits4,            Bits8 ],

  #   [     Bits4(-1),      Bits8(0xff) ],
  #   [      Bits4(1),      Bits8(0x11) ],
  #   [      Bits4(7),      Bits8(0x77) ],
  # ]

  do_test( a )

def test_ff_upblk( do_test ):
  a = CaseFlipFlopAdder.DUT()
  a._rtlir_test_ref = {
      'update_ff_upblk' : SeqUpblk( 'update_ff_upblk', [
        Assign( Attribute( Base( a ), 'out0' ), BinOp( Attribute( Base( a ), 'in0' ), Add(), Attribute( Base( a ), 'in1' ) ), False ),
        ] )
  }
  # a._test_vector = [
  #               'in0                in1              *out',
  #   [         Bits32,            Bits32,            Bits32 ],

  #   [     Bits32(-1),       Bits32(0xff),     Bits32(0xfe) ],
  #   [     Bits32(1),        Bits32(0x11),     Bits32(0x12) ],
  #   [     Bits32(7),        Bits32(0x77),     Bits32(0x7d) ],
  # ]

  do_test( a )

def test_fixed_size_slice( do_test ):
  a = CaseConstSizeSlicingComp.DUT()
  a._rtlir_test_ref = {
      'upblk' : CombUpblk( 'upblk', [
        For( LoopVarDecl('i'), Number(0), Number(2), Number(1), [
          Assign(
            Index(Attribute(Base(a), 'out'), LoopVar('i')),
            Slice(Attribute(Base(a), 'in_'),
                  BinOp(LoopVar('i'), Mult(), Number(8)),
                  BinOp(BinOp(LoopVar('i'), Mult(), Number(8)), Add(), Number(8)),
                  BinOp(LoopVar('i'), Mult(), Number(8)),
                  8,
            ), True)]
        )
      ])
  }
  # a._test_vector = [
  #               'in_              *out[0]          *out[1]',
  #   [         Bits16,               Bits8,            Bits8 ],

  #   [     Bits16(-1),         Bits8(0xff),      Bits8(0xff) ],
  #   [      Bits16(1),         Bits8(0x01),      Bits8(0x00) ],
  #   [      Bits16(7),         Bits8(0x07),      Bits8(0x00) ],
  #   [ Bits16(0xff00),         Bits8(0x00),      Bits8(0xff) ],
  #   [ Bits16(0x3412),         Bits8(0x12),      Bits8(0x34) ],
  #   [ Bits16(0x9876),         Bits8(0x76),      Bits8(0x98) ],
  # ]

  do_test( a )
