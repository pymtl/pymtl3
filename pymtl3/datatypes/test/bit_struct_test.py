"""
==========================================================================
bit_structs_test.py
==========================================================================
Test cases for bit_structs.

Author : Yanghui Ou
  Date : July 27, 2019
"""
from copy import deepcopy

from ..bit_struct  import is_bit_struct, bit_struct, field, mk_bit_struct
from ..bits_import import *
from pymtl3.dsl import Component, InPort, OutPort
from pymtl3.dsl.test.sim_utils import simple_sim_pass

#-------------------------------------------------------------------------
# Basic test
#-------------------------------------------------------------------------

@bit_struct
class Pixel:
  r : Bits8
  g : Bits8
  b : Bits8 = b8(4)
  nbits = 24

MadePixel = mk_bit_struct( 'MadePixel',{
    'r' : Bits8,
    'g' : Bits8,
    'b' : field( Bits8, default=b8(4) )
  },
  namespace = {
    'nbits' : 24
  }
)

def test_simple():
  print()

  # Test basic
  px = Pixel()
  assert px.r == px.g == 0
  assert px.b == 4
  assert px.nbits == 24

  # Test dynamic basic
  mpx = MadePixel()
  assert mpx.r == mpx.g == 0
  assert mpx.b == 4
  assert mpx.nbits == 24

  # Test str
  assert str(px) == str(mpx)

  # Check repr
  print(( repr(px), repr(mpx) ))

  # test equality
  px1 = Pixel( b4(1), b4(2), b4(3) )
  px2 = Pixel( b4(0), b4(0), b4(4) )
  assert px != px1
  assert px == px2

# FIXME: The following inherited bit struct cannot be used for construct
# nested struct as the newly made class is not captured in the scope of
# mk_bit_struct. Manually created structs cannot be used by mk_bit_struct
# to create nested structs.
# class StaticPoint(
#   mk_bit_struct( "BasePoint", [
#     ( 'x', Bits4 ),
#     ( 'y', Bits4 ),
#   ]) ):
#
#   def __str__( s ):
#     return "({},{})".format( int(s.x), int(s.y) )

# Create bit struct using syntax sugar (mk_bit_struct):
StaticPoint = mk_bit_struct( "StaticPoint", {
    'x': Bits4,
    'y': Bits4,
  })
# Create nested struct using mk_bit_struct
NestedSimple = mk_bit_struct( "NestedSimple", {
    'pt0': StaticPoint,
    'pt1': StaticPoint,
  })

def test_struct():
  pt = StaticPoint( Bits4(2), Bits4(4) )
  print( pt           )
  # print( pt.to_bits() )
  try:
    StaticPoint.__dict__[ 'haha' ]
  except KeyError as e:
    assert str( e ) == "'haha'"
  # assert StaticPoint.nbits == 8
  # assert StaticPoint.field_nbits( 'x' ) == 4
  # assert StaticPoint.field_nbits( 'y' ) == 4
  # assert pt.to_bits() == 0x24
  assert pt.x == 2
  assert pt.y == 4

  np = NestedSimple( StaticPoint(1,2), StaticPoint(3,4) )
  print( NestedSimple )
  print( np           )
  # print( np.to_bits() )
  # assert NestedSimple.nbits == 16
  # assert NestedSimple.field_nbits( 'pt0' ) == 8
  # assert NestedSimple.field_nbits( 'pt1' ) == 8
  assert np.pt0 == StaticPoint(1,2)
  assert np.pt0 != StaticPoint(1,1)
  assert np.pt0.x == 1
  assert np.pt0.y == 2
  assert np.pt1.x == 3
  assert np.pt1.y == 4

  def dynamic_point( xnbits, ynbits ):
    XType = mk_bits( xnbits )
    YType = mk_bits( ynbits )

    return mk_bit_struct(
      "Point_{}_{}".format( xnbits, ynbits ), {
        'x': XType,
        'y': YType,
      },
      namespace = { '__str__': lambda s: "({},{})".format( int(s.x), int(s.y) ) }
    )

  DPoint = dynamic_point( 4, 8 )
  dp = DPoint( 1, 2 )
  print( DPoint )
  print( dp     )
  # assert DPoint.nbits == 12
  assert dp.x == 1
  assert dp.y == 2

def test_component():
  class A( Component ):
    def construct( s ):
      s.in_    =  InPort( NestedSimple )
      s.out    = OutPort( NestedSimple )
      s.out_pt = OutPort( StaticPoint  )

      @s.update
      def up_bit_struct():
        # TODO:We have to use deepcopy here as a temporary workaround
        # to prevent s.in_ being mutated by the following operations.
        s.out = deepcopy( s.in_ )
        s.out.pt0.x += 1
        s.out.pt0.y -= 1
        s.out.pt1.x += 1
        s.out.pt1.y -= 1
        s.out_pt = s.in_.pt1

  dut = A()
  dut.elaborate()
  dut.apply( simple_sim_pass )
  dut.in_ = NestedSimple( StaticPoint(b4(1),b4(2)), StaticPoint(b4(3),b4(4)) )
  dut.tick()
  assert dut.out == NestedSimple( StaticPoint(Bits4(2),Bits4(1)), StaticPoint(Bits4(4),Bits4(3)) )
  print( dut.out_pt )
  assert dut.out_pt == StaticPoint(Bits4(3),Bits4(4))

#-------------------------------------------------------------------------
# Overwrite test
#-------------------------------------------------------------------------

@bit_struct
class Point:
  x : Bits8
  y : Bits8

  def __str__( self ):
    return f'({int(self.x)},{int(self.y)})'

  def __eq__( self, other ):
    return self.x == other.x and self.y == other.y

MadePoint = mk_bit_struct( 'MadePoint', {
    'x' : Bits8,
    'y' : Bits8,
  },
  namespace = {
    '__str__' : lambda self : f'({int(self.x)},{int(self.y)})',
    '__eq__'  : lambda self, other : self.x == other.x and self.y == other.y
  })

def test_overwrite():
  pt  = Point( b8(1), b8(2) )
  mpt = MadePoint( b8(1), b8(2) )

  assert pt == mpt
  assert str(pt) == str(mpt)

#-------------------------------------------------------------------------
# Nested bit struct test
#-------------------------------------------------------------------------

@bit_struct
class TwoPoint:
  pt0 : Point
  pt1 : MadePoint

MadeTwoPoint = mk_bit_struct( 'MadeTwoPoint', {
  'pt0' : Point,
  'pt1' : MadePoint,
})

def test_nested():
  a = TwoPoint( pt0=Point( b8(1), b8(2) ) )
  b = MadeTwoPoint( pt1=MadePoint( b8(3), b8(4) ) )
  assert a.pt0.x == 1
  assert a.pt0.y == 2
  assert a.pt1.x == 0
  assert a.pt1.y == 0
  assert b.pt0.x == 0
  assert b.pt0.y == 0
  assert b.pt1.x == 3
  assert b.pt1.y == 4

#-------------------------------------------------------------------------
# Bit struct instance test
#-------------------------------------------------------------------------

def test_is_bit_struct():
  class A:
    x : Bits4
    y : Bits4

  @bit_struct
  class B:
    x : Bits4
    y : Bits4

  assert not is_bit_struct( A() )
  assert is_bit_struct( B() )
