import pytest

from pymtl import *
from pymtl.passes.RAST import *
from pymtl.passes.errors import PyMTLTypeError
from pymtl.passes.SystemVerilogTranslationPass import SystemVerilogTranslationPass

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
  a.elaborate()
  SystemVerilogTranslationPass()( a )

  ref_dict = {}

  ref_dict[ 'index_basic' ] = CombUpblk( [
    Assign( [ Index( Attribute( Module( a ), 'out' ), Const( 0, 0 ) ) ],
      BinOp( Index( Attribute( Module( a ), 'in_' ), Const( 0, 0 ) ), Add(),
             Index( Attribute( Module( a ), 'in_' ), Const( 0, 1 ) ) ) ),
    Assign( [ Index( Attribute( Module( a ), 'out' ), Const( 0, 1 ) ) ],
      BinOp( Index( Attribute( Module( a ), 'in_' ), Const( 0, 2 ) ), Add(),
             Index( Attribute( Module( a ), 'in_' ), Const( 0, 3 ) ) ) )
  ] )

  for blk in a.get_update_blocks():
    assert a._rast[ blk ] == ref_dict[ blk.__name__ ]

@pytest.mark.xfail( reason = "Assignment with ismatched width!",
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
  a.elaborate()
  # Translation fails because of mismatch width
  SystemVerilogTranslationPass()( a )

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
  a.elaborate()
  SystemVerilogTranslationPass()( a )

  ref_dict = {}

  ref_dict[ 'slicing_basic' ] = CombUpblk( [
    Assign( [ Slice( Attribute( Module( a ), 'out' ), Const( 0, 0 ), Const( 0, 16 ) ) ],
      Slice( Attribute( Module( a ), 'in_' ), Const( 0, 16 ), Const( 0, 32 ) ) ),
    Assign( [ Slice( Attribute( Module( a ), 'out' ), Const( 0, 16 ), Const( 0, 32 ) ) ],
      Slice( Attribute( Module( a ), 'in_' ), Const( 0, 0 ), Const( 0, 16 ) ) )
  ] )

  for blk in a.get_update_blocks():
    assert a._rast[ blk ] == ref_dict[ blk.__name__ ]

def test_bits_basic():
  class A( RTLComponent ):
    def construct( s ):
      s.in_ = InVPort( Bits16 )
      s.out = OutVPort( Bits16 )

      @s.update
      def bits_basic():
        s.out = s.in_ + Bits16( 10 )

  a = A()
  a.elaborate()
  SystemVerilogTranslationPass()( a )

  ref_dict = {}

  ref_dict[ 'bits_basic' ] = CombUpblk( [
    Assign( [ Attribute( Module( a ), 'out' ) ],
      BinOp( Attribute( Module( a ), 'in_' ), Add(), Const( 16, 10 ) ) )
  ] )

  for blk in a.get_update_blocks():
    assert a._rast[ blk ] == ref_dict[ blk.__name__ ]

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
  a.elaborate()
  SystemVerilogTranslationPass()( a )

  ref_dict = {}

  ref_dict[ 'index_bits_slicing' ] = CombUpblk( [
    Assign( [ Slice( 
      Index( Attribute( Module( a ), 'out' ), Const( 0, 0 )),
      Const( 0, 0 ), Const( 0, 8 ) 
      ) ],
      BinOp( 
        BinOp( 
          Slice( Index( Attribute( Module( a ), 'in_' ), Const( 0, 1 ) ), Const( 0, 8 ), Const( 0, 16 ) ),
          Add(),
          Slice( Index( Attribute( Module( a ), 'in_' ), Const( 0, 2 ) ), Const( 0, 0 ), Const( 0, 8 ) ),
        ),
        Add(),
        Const( 8, 10 ) 
      )
    ),
    Assign( [ 
      Index( Attribute( Module( a ), 'out' ), Const( 0, 1 ) )
      ],
      BinOp( 
        BinOp( 
          Slice( Index( Attribute( Module( a ), 'in_' ), Const( 0, 3 ) ), Const( 0, 0 ), Const( 0, 16 ) ),
          Add(),
          Index( Attribute( Module( a ), 'in_' ), Const( 0, 4 ) )
        ),
        Add(),
        Const( 16, 1 ) 
      )
    ),
  ] )

  for blk in a.get_update_blocks():
    assert a._rast[ blk ] == ref_dict[ blk.__name__ ]

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
  a.elaborate()
  SystemVerilogTranslationPass()( a )

  ref_dict = {}

  ref_dict[ 'multi_components_A' ] = CombUpblk( [
    Assign( [ Attribute( Module( a ), 'out' ) ],
      BinOp(
        Attribute( Module( a ), 'in_' ),
        Add(),
        Attribute( Attribute( Module( a ), 'b' ), 'out' )
      ) 
    )
  ] )

  for blk in a.get_update_blocks():
    assert a._rast[ blk ] == ref_dict[ blk.__name__ ]

if __name__ == '__main__':
  test_index_basic()
