"""
==========================================================================
bit_structs_test.py
==========================================================================
Test cases for bit_structs.

Author : Yanghui Ou
  Date : July 27, 2019
"""
from __future__ import print_function

from ..bit_structs import _IS_BIT_STRUCT, bit_struct, field, mk_bit_struct
from ..bits_import import *

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

def is_bit_struct( bs ):
  return hasattr( bs, _IS_BIT_STRUCT )

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
