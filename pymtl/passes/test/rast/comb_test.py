import pytest

from pymtl import *
from pymtl.passes.RAST import *
from pymtl.passes.errors import PyMTLTypeError
from pymtl.passes.SystemVerilogTranslationPass import SystemVerilogTranslationPass

#-----------------------------------------------------------------------
# verify_manual
#-----------------------------------------------------------------------
# Verify that the generated RAST is the same as the manually generated
# reference.

def verify_manual( m, ref ):
  m.elaborate()
  SystemVerilogTranslationPass()( m )

  for blk in m.get_update_blocks():
    assert m._rast[ blk ] == ref[ blk.__name__ ]

#-----------------------------------------------------------------------
# Test basic indexing support
#-----------------------------------------------------------------------

def test_index_basic():
  class A( RTLComponent ):
    def construct( s ):
      s.in_ = [ InVPort( Bits16 ) for _ in xrange( 4 ) ]
      s.out = [ OutVPort( Bits16 ) for _ in xrange( 2 ) ]

      @s.update
      def index_basic():
        s.out[ 0 ] = s.in_[ 0 ] + s.in_[ 1 ]
        s.out[ 1 ] = s.in_[ 2 ] + s.in_[ 3 ]

  a = A()

  ref = { 'index_basic' : CombUpblk( [
    Assign( Index( Attribute( Module( a ), 'out' ), Number( 0, 0 ) ),
      BinOp( Index( Attribute( Module( a ), 'in_' ), Number( 0, 0 ) ), Add(),
             Index( Attribute( Module( a ), 'in_' ), Number( 0, 1 ) ) ) ),
    Assign( Index( Attribute( Module( a ), 'out' ), Number( 0, 1 ) ),
      BinOp( Index( Attribute( Module( a ), 'in_' ), Number( 0, 2 ) ), Add(),
             Index( Attribute( Module( a ), 'in_' ), Number( 0, 3 ) ) ) )
  ] ) }

  verify_manual( a, ref )

#-----------------------------------------------------------------------
# Test assginment with mismatched width
#-----------------------------------------------------------------------

@pytest.mark.xfail( reason = "Assignment with mismatched width!",
                    raises = PyMTLTypeError )
def test_mismatch_width_assign():
  class A( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits16 )
      s.out = OutVPort( Bits8 )

      @s.update
      def mismatch_width_assign():
        s.out = s.in_

  a = A()

  verify_manual( a, {} )

#-----------------------------------------------------------------------
# Test basic slicing support
#-----------------------------------------------------------------------

def test_slicing_basic():
  class A( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits32 )
      s.out = OutVPort( Bits64 )

      @s.update
      def slicing_basic():
        s.out[ 0:16 ] = s.in_[ 16:32 ]
        s.out[ 16:32 ] = s.in_[ 0:16 ]

  a = A()

  ref = { 'slicing_basic' : CombUpblk( [
    Assign( Slice( Attribute( Module( a ), 'out' ), Number( 0, 0 ), Number( 0, 16 ) ),
      Slice( Attribute( Module( a ), 'in_' ), Number( 0, 16 ), Number( 0, 32 ) ) ),
    Assign( Slice( Attribute( Module( a ), 'out' ), Number( 0, 16 ), Number( 0, 32 ) ),
      Slice( Attribute( Module( a ), 'in_' ), Number( 0, 0 ), Number( 0, 16 ) ) )
  ] ) }

  verify_manual( a, ref )

#-----------------------------------------------------------------------
# Test calls to BitsX
#-----------------------------------------------------------------------

def test_bits_basic():
  class A( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits16 )
      s.out = OutVPort( Bits16 )

      @s.update
      def bits_basic():
        s.out = s.in_ + Bits16( 10 )

  a = A()

  ref = { 'bits_basic' : CombUpblk( [
    Assign( Attribute( Module( a ), 'out' ),
      BinOp( Attribute( Module( a ), 'in_' ), Add(), Number( 16, 10 ) ) )
  ] ) }

  verify_manual( a, ref )

#-----------------------------------------------------------------------
# Test support for expressions with indexing, slicing, and BitX
#-----------------------------------------------------------------------

def test_index_bits_slicing():
  class A( RTLComponent ):
    def construct( s ):
      s.in_ = [ InVPort( Bits16 ) for _ in xrange( 10 ) ]
      s.out = [ OutVPort( Bits16 ) for _ in xrange( 5 ) ]

      @s.update
      def index_bits_slicing():
        s.out[0][0:8] = s.in_[1][8:16] + s.in_[2][0:8] + Bits8( 10 )
        s.out[1] = s.in_[3][0:16] + s.in_[4] + Bits16( 1 )

  a = A()

  ref = { 'index_bits_slicing' : CombUpblk( [
    Assign( Slice( 
      Index( Attribute( Module( a ), 'out' ), Number( 0, 0 ) ),
      Number( 0, 0 ), Number( 0, 8 ) 
      ),
      BinOp( 
        BinOp( 
          Slice( Index( Attribute( Module( a ), 'in_' ), Number( 0, 1 ) ), Number( 0, 8 ), Number( 0, 16 ) ),
          Add(),
          Slice( Index( Attribute( Module( a ), 'in_' ), Number( 0, 2 ) ), Number( 0, 0 ), Number( 0, 8 ) ),
        ),
        Add(),
        Number( 8, 10 ) 
      )
    ),
    Assign( 
      Index( Attribute( Module( a ), 'out' ), Number( 0, 1 ) ),
      BinOp( 
        BinOp( 
          Slice( Index( Attribute( Module( a ), 'in_' ), Number( 0, 3 ) ), Number( 0, 0 ), Number( 0, 16 ) ),
          Add(),
          Index( Attribute( Module( a ), 'in_' ), Number( 0, 4 ) )
        ),
        Add(),
        Number( 16, 1 ) 
      )
    ),
  ] ) }

  verify_manual( a, ref )

#-----------------------------------------------------------------------
# Test support for component reference
#-----------------------------------------------------------------------

def test_multi_components():
  class B( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits16 )
      s.out = OutVPort( Bits16 )

      @s.update
      def multi_components_B():
        s.out = s.in_

  class A( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits16 )
      s.out = OutVPort( Bits16 )
      s.b = B()

      @s.update
      def multi_components_A():
        s.out = s.in_ + s.b.out

  a = A()

  ref = { 'multi_components_A' : CombUpblk( [
    Assign( Attribute( Module( a ), 'out' ),
      BinOp(
        Attribute( Module( a ), 'in_' ),
        Add(),
        Attribute( Attribute( Module( a ), 'b' ), 'out' )
      ) 
    )
  ] ) }

  verify_manual( a, ref )

#-----------------------------------------------------------------------
# Test support for if statement
#-----------------------------------------------------------------------

def test_if_basic():
  class A( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits16 )
      s.out = OutVPort( Bits8 )

      @s.update
      def if_basic():
        if s.in_[ 0:8 ] == Bits8( 255 ):
          s.out = s.in_[ 8:16 ]
        else:
          s.out = Bits8( 0 )

  a = A()

  ref = {
    'if_basic' : CombUpblk( [ If(
      Compare( Slice( Attribute( Module( a ), 'in_' ), Number( 0, 0 ), Number( 0, 8 ) ), Eq(), Number( 8, 255 ) ),
      [ Assign( Attribute( Module( a ), 'out' ), Slice( Attribute( Module( a ), 'in_' ), Number( 0, 8 ), Number( 0, 16 ) ) ) ],
      [ Assign( Attribute( Module( a ), 'out' ), Number( 8, 0 ) ) ]
    )
  ] ) }

  verify_manual( a, ref )

#-----------------------------------------------------------------------
# Test support for for statement
#-----------------------------------------------------------------------

def test_for_basic():
  class A( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits16 )
      s.out = OutVPort( Bits8 )

      @s.update
      def for_basic():
        for i in xrange( 8 ):
          s.out[ 2*i:2*i+1 ] = s.in_[ 2*i:2*i+1 ] + s.in_[ 2*i+1:2*i+2 ]

  a = A()

  twice_i = BinOp( Number( 0, 2 ), Mult(), LoopVar( 'i' ) )

  ref = {
    'for_basic' : CombUpblk( [ For(
      LoopVarDecl( 'i' ), Number( 0, 0 ), Number( 0, 8 ), Number( 0, 1 ),
      [ Assign(
          Slice( Attribute( Module( a ), 'out' ), twice_i, BinOp( twice_i, Add(), Number( 0, 1 ) ) ),
          BinOp(
            Slice( Attribute( Module( a ), 'in_' ), twice_i, BinOp( twice_i, Add(), Number( 0, 1 ) ) ),
            Add(),
            Slice( Attribute( Module( a ), 'in_' ),
              BinOp( twice_i, Add(), Number( 0, 1 ) ),
              BinOp( twice_i, Add(), Number( 0, 2 ) )
            )
          )
      ) 
    ]
    ) ] )
  }

  verify_manual( a, ref )

if __name__ == '__main__':
  test_for_basic()
