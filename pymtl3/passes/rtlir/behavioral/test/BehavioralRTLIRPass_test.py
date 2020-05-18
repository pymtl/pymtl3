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
    CaseForFreeVarStepComp,
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
  m.apply( BehavioralRTLIRGenPass( m ) )
  m.apply( BehavioralRTLIRTypeCheckPass( m ) )
  m.apply( BehavioralRTLIRVisualizationPass() )

  rtlir_upblks = m.get_metadata( BehavioralRTLIRGenPass.rtlir_upblks )

  for blk in m.get_update_blocks():
    assert rtlir_upblks[ blk ] == ref[ blk.__name__ ]

def test_reduce( do_test ):
  a = CaseReducesInx3OutComp.DUT()
  in_1 = Attribute( Base( a ), 'in_1' )
  in_2 = Attribute( Base( a ), 'in_2' )
  in_3 = Attribute( Base( a ), 'in_3' )
  out = Attribute( Base( a ), 'out' )

  a._rtlir_test_ref = { 'v_reduce' : CombUpblk( 'v_reduce', [
    Assign( [out], BinOp(
      BinOp( Reduce( BitAnd(), in_1 ), BitAnd(), Reduce( BitOr(), in_2 ) ),
      BitOr(), Reduce( BitXor(), in_3 ),
    ), True )
  ] ) }

  do_test( a )

def test_index_basic( do_test ):
  a = CaseBits16IndexBasicComp.DUT()

  a._rtlir_test_ref = { 'index_basic' : CombUpblk( 'index_basic', [
    Assign( [Index( Attribute( Base( a ), 'out' ), Number( 0 ) )],
      BinOp( Index( Attribute( Base( a ), 'in_' ), Number( 0 ) ), Add(),
             Index( Attribute( Base( a ), 'in_' ), Number( 1 ) ) ), True ),
    Assign( [Index( Attribute( Base( a ), 'out' ), Number( 1 ) )],
      BinOp( Index( Attribute( Base( a ), 'in_' ), Number( 2 ) ), Add(),
             Index( Attribute( Base( a ), 'in_' ), Number( 3 ) ) ), True )
  ] ) }

  do_test( a )

def test_mismatch_width_assign( do_test ):
  a = CaseBits8Bits16MismatchAssignComp.DUT()

  a._rtlir_test_ref = { 'mismatch_width_assign' : CombUpblk(
    'mismatch_width_assign', [ Assign(
      [Attribute( Base( a ), 'out' )], Attribute( Base( a ), 'in_' ), True
    )
  ] ) }

  with expected_failure( PyMTLTypeError, "LHS and RHS of assignment" ):
    do_test( a )

def test_slicing_basic( do_test ):
  a = CaseBits32Bits64SlicingBasicComp.DUT()

  a._rtlir_test_ref = { 'slicing_basic' : CombUpblk( 'slicing_basic', [
    Assign( [Slice( Attribute( Base( a ), 'out' ), Number( 0 ), Number( 16 ) )],
      Slice( Attribute( Base( a ), 'in_' ), Number( 16 ), Number( 32 ) ), True ),
    Assign( [Slice( Attribute( Base( a ), 'out' ), Number( 16 ), Number( 32 ) )],
      Slice( Attribute( Base( a ), 'in_' ), Number( 0 ), Number( 16 ) ), True )
  ] ) }

  do_test( a )

def test_bits_basic( do_test ):
  a = CaseBits16ConstAddComp.DUT()

  a._rtlir_test_ref = { 'bits_basic' : CombUpblk( 'bits_basic', [
    Assign( [Attribute( Base( a ), 'out' )],
      BinOp( Attribute( Base( a ), 'in_' ), Add(), SizeCast( 16, Number( 10 ) ) ), True )
  ] ) }

  do_test( a )

def test_index_bits_slicing( do_test ):
  a = CaseSlicingOverIndexComp.DUT()

  a._rtlir_test_ref = { 'index_bits_slicing' : CombUpblk( 'index_bits_slicing', [
    Assign( [Slice(
      Index( Attribute( Base( a ), 'out' ), Number( 0 ) ),
      Number( 0 ), Number( 8 )
      )],
      BinOp(
        BinOp(
          Slice( Index( Attribute( Base( a ), 'in_' ), Number( 1 ) ), Number( 8 ), Number( 16 ) ),
          Add(),
          Slice( Index( Attribute( Base( a ), 'in_' ), Number( 2 ) ), Number( 0 ), Number( 8 ) ),
        ),
        Add(),
        Number( 10 )
      ),
      True
    ),
    Assign(
      [Index( Attribute( Base( a ), 'out' ), Number( 1 ) )],
      BinOp(
        BinOp(
          Slice( Index( Attribute( Base( a ), 'in_' ), Number( 3 ) ), Number( 0 ), Number( 16 ) ),
          Add(),
          Index( Attribute( Base( a ), 'in_' ), Number( 4 ) )
        ),
        Add(),
        Number( 1 )
      ),
      True
    ),
  ] ) }

  do_test( a )

def test_multi_components( do_test ):
  a = CaseSubCompAddComp.DUT()

  a._rtlir_test_ref = { 'multi_components_A' : CombUpblk( 'multi_components_A', [
    Assign( [Attribute( Base( a ), 'out' )],
      BinOp(
        Attribute( Base( a ), 'in_' ),
        Add(),
        Attribute( Attribute( Base( a ), 'b' ), 'out' )
      ),
      True
    )
  ] ) }

  do_test( a )

def test_if_basic( do_test ):
  a = CaseIfBasicComp.DUT()

  a._rtlir_test_ref = {
    'if_basic' : CombUpblk( 'if_basic', [ If(
      Compare( Slice( Attribute( Base( a ), 'in_' ), Number( 0 ), Number( 8 ) ), Eq(), Number( 255 ) ),
      [ Assign( [Attribute( Base( a ), 'out' )], Slice( Attribute( Base( a ), 'in_' ), Number( 8 ), Number( 16 ) ), True ) ],
      [ Assign( [Attribute( Base( a ), 'out' )], Number( 0 ), True ) ]
    )
  ] ) }

  do_test( a )

@XFAIL_ON_PY3
def test_for_basic( do_test ):
  a = CaseForBasicComp.DUT()

  twice_i = BinOp( Number( 2 ), Mult(), LoopVar( 'i' ) )

  a._rtlir_test_ref = {
    'for_basic' : CombUpblk( 'for_basic', [ For(
      LoopVarDecl( 'i' ), Number( 0 ), Number( 8 ), Number( 1 ),
      [ Assign(
          [Slice( Attribute( Base( a ), 'out' ), twice_i, BinOp( twice_i, Add(), Number( 1 ) ) )],
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

  do_test( a )

def test_for_freevar_step( do_test ):
  a = CaseForFreeVarStepComp.DUT()

  a._rtlir_test_ref = {
    'upblk' : CombUpblk( 'upblk', [ For(
      LoopVarDecl( 'i' ), Number( 0 ), Number( 2 ), FreeVar( 'freevar_at_upblk', 1 ),
      [ Assign(
          [Attribute( Base( a ), 'out' )],
          Slice( Attribute( Base( a ), 'in_' ), Number(0), Number(8) ),
          True
        )
      ]
    ) ] )
  }

  do_test( a )

def test_multi_upblks( do_test ):
  a = CaseTwoUpblksSliceComp.DUT()

  a._rtlir_test_ref = { 'multi_upblks_1' : CombUpblk( 'multi_upblks_1', [
      Assign( [Slice( Attribute( Base( a ), 'out' ), Number(0), Number(4) )], Attribute( Base( a ), 'in_' ), True ),
    ] ),
    'multi_upblks_2' : CombUpblk( 'multi_upblks_2', [
      Assign( [Slice( Attribute( Base( a ), 'out' ), Number(4), Number(8) )], Attribute( Base( a ), 'in_' ), True ),
    ] )
  }

  do_test( a )

def test_ff_upblk( do_test ):
  a = CaseFlipFlopAdder.DUT()
  a._rtlir_test_ref = {
      'update_ff_upblk' : SeqUpblk( 'update_ff_upblk', [
        Assign( [Attribute( Base( a ), 'out0' )], BinOp( Attribute( Base( a ), 'in0' ), Add(), Attribute( Base( a ), 'in1' ) ), False ),
        ] )
  }

  do_test( a )

def test_fixed_size_slice( do_test ):
  a = CaseConstSizeSlicingComp.DUT()
  a._rtlir_test_ref = {
      'upblk' : CombUpblk( 'upblk', [
        For( LoopVarDecl('i'), Number(0), Number(2), Number(1), [
          Assign(
            [Index(Attribute(Base(a), 'out'), LoopVar('i'))],
            Slice(Attribute(Base(a), 'in_'),
                  BinOp(LoopVar('i'), Mult(), Number(8)),
                  BinOp(BinOp(LoopVar('i'), Mult(), Number(8)), Add(), Number(8)),
                  BinOp(LoopVar('i'), Mult(), Number(8)),
                  8,
            ), True)]
        )
      ])
  }

  do_test( a )
