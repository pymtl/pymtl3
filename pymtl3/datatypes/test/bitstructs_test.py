"""
==========================================================================
bitstruct_test.py
==========================================================================
Test cases for bitstructs.

Author : Yanghui Ou
  Date : July 27, 2019
"""

import pytest

from pymtl3.dsl import Component, InPort, OutPort, update
from pymtl3.dsl.test.sim_utils import simple_sim_pass

from ..bits_import import *
from ..bitstructs import (
    bitstruct,
    get_bitstruct_inst_all_classes,
    is_bitstruct_class,
    is_bitstruct_inst,
    mk_bitstruct,
)

#-------------------------------------------------------------------------
# Basic test to test error messages and exceptions
#-------------------------------------------------------------------------

def test_no_field():
  try:
    @bitstruct
    class Pixel:
      b = Bits8
  except AttributeError as e:
    print(e)
    assert str(e).startswith( "No field is declared in the bit struct definition." )

def test_field_no_default():
  try:
    @bitstruct
    class Pixel:
      r : Bits8
      g : Bits8
      b : Bits8 = b8(4)
  except TypeError as e:
    print(e)
    assert str(e).startswith( "We don't allow subfields to have default value:\n- Field " )

def test_field_wrong_type():
  try:
    @bitstruct
    class A:
      x: int
  except TypeError as e:
    print(e)
    assert str(e).startswith( "We currently only support BitsN, list, or another BitStruct as BitStruct field:\n- Field " )

def test_field_not_type():
  try:
    @bitstruct
    class A:
      x: 1
  except TypeError as e:
    print(e)

@bitstruct
class Pixel:
  r : Bits8
  g : Bits8
  b : Bits8
  # nbits = 24

MadePixel = mk_bitstruct( 'MadePixel',{
    'r' : Bits8,
    'g' : Bits8,
    'b' : Bits8,
  },
  # namespace = { 'nbits' : 24 }
)

#-------------------------------------------------------------------------
# Caching test
#-------------------------------------------------------------------------

def test_structs_caching():

  class A:
    @bitstruct
    class S:
      x: Bits8
      y: Bits8
      z:  [ [ Bits32, Bits32 ] ] * 2

  class B:
    @bitstruct
    class S:
      x: Bits8
      y: Bits8
      z:  [ [ Bits32, Bits32 ] ] * 2

  SS = mk_bitstruct( 'S', {
    'x' : Bits8,
    'y' : Bits8,
    'z' : [ [ Bits32, Bits32 ], [ Bits32, Bits32 ] ]
  })

  assert B.S is A.S
  assert SS is B.S
  assert SS is A.S

  class C:
    @bitstruct
    class S:
      x: Bits8
      y: Bits8
      w:  [ [ Bits32, Bits32 ] ] * 2

  assert C.S is not A.S

  SS2 = mk_bitstruct( 'S', {
    'x' : Bits8,
    'y' : Bits7,
    'z' : [ [ Bits32, Bits32 ], [ Bits32, Bits32 ] ]
  })

  assert SS2 is not A.S

  SS3 = mk_bitstruct( 's', {
    'x' : Bits8,
    'y' : Bits8,
    'z' : [ [ Bits32, Bits32 ], [ Bits32, Bits32 ] ]
  })
  assert SS3 is not A.S

# Shunning: As of now, since we still want metadata fields in the struct
# definition, we have to mark this as xfail until we find a better
# solution. In terms of the test, B.S gets cached because A.S and B.S have
# the same annotated fields. However, the nbits field of B is different
# from A, which is an underfined behavior ...

@pytest.mark.xfail
def test_structs_caching_metadata_undefined():

  class A:
    @bitstruct
    class S:
      x: Bits8
      y: Bits8
      nbits = 1

  class B:
    @bitstruct
    class S:
      x: Bits8
      y: Bits8
      nbits = 2

  assert B.S is A.S
  assert B.S.nbits == 2 # From get cache B.S is A.S ... so no nbits=2

#-------------------------------------------------------------------------
# Test the functionalities
#-------------------------------------------------------------------------

def test_simple():
  print()

  # Test basic
  px = Pixel()
  assert isinstance( px.r, Bits8 )
  assert isinstance( px.g, Bits8 )
  assert isinstance( px.b, Bits8 )
  assert px.r == px.g == 0
  assert px.b == 0
  assert px.nbits == 24

  # Test dynamic basic
  mpx = MadePixel()
  assert isinstance( mpx.r, Bits8 )
  assert isinstance( mpx.g, Bits8 )
  assert isinstance( mpx.b, Bits8 )
  assert mpx.r == mpx.g == 0
  assert mpx.b == 0
  assert mpx.nbits == 24

  # Test str
  assert str(px) == str(mpx)

  # Check repr
  print(( repr(px), repr(mpx) ))

  # test equality
  px1 = Pixel(1, 2, 3)
  assert isinstance( px1.r, Bits8 )
  assert isinstance( px1.g, Bits8 )
  assert isinstance( px1.b, Bits8 )
  px2 = Pixel( 0, 0, 0 )
  assert px != px1
  assert px == px2

# FIXME: The following inherited bit struct cannot be used for construct
# nested struct as the newly made class is not captured in the scope of
# mk_bitstruct. Manually created structs cannot be used by mk_bitstruct
# to create nested structs.
# class StaticPoint(
#   mk_bitstruct( "BasePoint", [
#     ( 'x', Bits4 ),
#     ( 'y', Bits4 ),
#   ]) ):
#
#   def __str__( s ):
#     return "({},{})".format( int(s.x), int(s.y) )

# Create bit struct using syntax sugar (mk_bitstruct):
StaticPoint = mk_bitstruct( "StaticPoint", {
    'x': Bits4,
    'y': Bits4,
  })
# Create nested struct using mk_bitstruct
NestedSimple = mk_bitstruct( "NestedSimple", {
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
  # assert pt.to_bits() == 0x24
  assert pt.x == 2
  assert pt.y == 4

  np = NestedSimple( StaticPoint(1,2), StaticPoint(3,4) )
  print( NestedSimple )
  print( np           )
  assert np.pt0 == StaticPoint(1,2)
  assert np.pt0 != StaticPoint(1,1)
  assert np.pt0.x == 1
  assert np.pt0.y == 2
  assert np.pt1.x == 3
  assert np.pt1.y == 4

  def dynamic_point( xnbits, ynbits ):
    XType = mk_bits( xnbits )
    YType = mk_bits( ynbits )

    return mk_bitstruct(
      f"Point_{xnbits}_{ynbits}", {
        'x': XType,
        'y': YType,
      },
      namespace = { '__str__': lambda s: "({},{})".format( int(s.x), int(s.y) ) }
    )

  DPoint = dynamic_point( 4, 8 )
  dp = DPoint( 1, 2 )
  print( DPoint )
  print( dp     )
  assert dp.x == 1
  assert dp.y == 2

def test_component():
  class A( Component ):
    def construct( s ):
      s.in_    =  InPort( NestedSimple )
      s.out    = OutPort( NestedSimple )
      s.out_pt = OutPort( StaticPoint  )

      @update
      def up_bitstruct():
        # TODO:We have to use deepcopy here as a temporary workaround
        # to prevent s.in_ being mutated by the following operations.
        s.out @= s.in_
        s.out.pt0.x @= 10
        s.out.pt0.y @= 11
        s.out.pt1.x @= 12
        s.out.pt1.y @= 13
        s.out_pt @= s.in_.pt1

  dut = A()
  dut.elaborate()
  dut.apply( simple_sim_pass )
  dut.in_ = NestedSimple( StaticPoint(b4(1),b4(2)), StaticPoint(b4(3),b4(4)) )
  dut.tick()
  assert dut.out == NestedSimple( StaticPoint(Bits4(10),Bits4(11)), StaticPoint(Bits4(12),Bits4(13)) )
  print( dut.out_pt )
  assert dut.out_pt == StaticPoint(Bits4(3),Bits4(4))

#-------------------------------------------------------------------------
# Overwrite test
#-------------------------------------------------------------------------

@bitstruct
class Point:
  x : Bits8
  y : Bits8

  def __str__( self ):
    return f'({int(self.x)},{int(self.y)})'

  def __eq__( self, other ):
    return self.x == other.x and self.y == other.y

MadePoint = mk_bitstruct( 'MadePoint', {
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

@bitstruct
class TwoPoint:
  pt0 : Point
  pt1 : MadePoint

MadeTwoPoint = mk_bitstruct( 'MadeTwoPoint', {
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

def test_nested_two_struct_with_same_name():

  class A:
    @bitstruct
    class S:
      z: Bits2

  class B:
    @bitstruct
    class S:
      x: Bits8
      y: Bits8

  SS = mk_bitstruct( 'SS', {
    'a' : A.S,
    'b' : B.S,
  })
  ss = SS()
  assert isinstance( ss.a.z, Bits2 )
  assert isinstance( ss.b.x, Bits8 )
  assert isinstance( ss.b.y, Bits8 )

  ss = SS( A.S(2), B.S(3,3) )
  assert isinstance( ss.a.z, Bits2 )
  assert isinstance( ss.b.x, Bits8 )
  assert isinstance( ss.b.y, Bits8 )

  assert ss.a.z == 2
  assert ss.b.x == 3
  assert ss.b.y == 3

#-------------------------------------------------------------------------
# Bit struct instance test
#-------------------------------------------------------------------------

def test_is_bitstruct_inst_class():
  class A:
    x : Bits4
    y : Bits4

  @bitstruct
  class B:
    x : Bits4
    y : Bits4

  assert not is_bitstruct_class( A )
  assert not is_bitstruct_inst( A )
  assert not is_bitstruct_class( A() )
  assert not is_bitstruct_inst( A() )

  assert is_bitstruct_class( B )
  assert not is_bitstruct_inst( B )
  assert not is_bitstruct_class( B() )
  assert is_bitstruct_inst( B() )

#-------------------------------------------------------------------------
# bit struct with array test
#-------------------------------------------------------------------------

def test_list_same_class():
  @bitstruct
  class A:
    x: Bits4
    y: [ Bits4, Bits4 ]
  a = A()
  assert a.x == Bits4(0)
  assert a.y == [ Bits4(0), Bits4(0) ]

  b = a.clone()
  assert a == b

  b.x = Bits4(3)

  assert a.x != b.x
  assert a.y[0] == b.y[0]
  assert a.y[1] == b.y[1]
  assert a != b

  b.y[0] = Bits4(4)

  assert a.x != b.x
  assert a.y[0] != b.y[0]
  assert a.y[1] == b.y[1]
  assert a != b

  b.y[1] = Bits4(4)

  assert a.x != b.x
  assert a.y[0] != b.y[0]
  assert a.y[1] != b.y[1]
  assert a != b

def test_crazy_list_not_same_class():
  @bitstruct
  class A:
    x: Bits4
  try:
    @bitstruct
    class B:
      x: Bits4
      y: [[[[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]]],
          [[[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]]],
          [[[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]]],
          [[[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]]],
          [[[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]]],
          [[[A, A, A]], [[A, A, A]], [[A, A, Bits1]], [[A, A, A]], [[A, A, A]], [[A, A, A]]],
          [[[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]]],
          [[[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]]],
          [[[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]]],
          [[[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]], [[A, A, A]]]]
  except TypeError as e:
    print(e)
    assert str(e) == "The provided list spec should be a strict multidimensional ARRAY with no varying sizes or types. "\
                     "All non-list elements should be VALID types."

def test_high_d_list_inside():
  @bitstruct
  class A:
    x: Bits4
    y:[ [ [ [Bits4, Bits4, Bits4] ] ] * 6 ] * 10
  a = A()
  assert a.x == Bits4(0)
  assert a.y == [ [ [ [ Bits4(), Bits4(), Bits4()] ] for _ in range(6) ] for _ in range(10) ]

def test_mk_high_d_list_inside():
  A = mk_bitstruct( "A", {
    'x': Bits4,
    'y': [ [ [ [Bits4, Bits4, Bits4] ] ] * 6 ] * 10,
  })
  a = A()
  assert a.x == Bits4(0)
  assert a.y == [ [ [ [ Bits4(), Bits4(), Bits4()] ] for _ in range(6) ] for _ in range(10) ]

  print(a)

def test_high_d_list_struct_inside():
  @bitstruct
  class A:
    x: Bits4
  @bitstruct
  class B:
    x: Bits4
    y: [ [ [ [A, A, A] ] ] * 6 ] * 10
  b = B()
  assert b.x == Bits4(0)
  assert b.y == [ [ [ [ A(), A(), A()] ] for _ in range(6) ] for _ in range(10) ]

def test_mk_high_d_list_struct_inside():
  @bitstruct
  class A:
    x: Bits4
  B = mk_bitstruct( "B", {
    'x': Bits4,
    'y': [ [ [ [A, A, A] ] ] * 6 ] * 10,
  })
  b = B()
  assert b.x == Bits4(0)
  assert b.y == [ [ [ [ A(), A(), A()] ] for _ in range(6) ] for _ in range(10) ]

  print(b)
  c = b.clone()
  c.y[9][2][0][2].x = Bits4(3)
  print(c.y[9][2][0][2])
  assert b != c

def test_get_nbits():

  @bitstruct
  class SomeMsg:
    c: [ Bits3, Bits3 ]
    d: [ Bits5, Bits5 ]

  assert SomeMsg.nbits == 16
  a = SomeMsg()
  assert a.nbits == 16

def test_to_bits():

  @bitstruct
  class SomeMsg:
    c: [ Bits4, Bits4 ]
    d: [ Bits8, Bits8 ]

  # list is LSB-based now
  assert SomeMsg([b4(0x2),b4(0x3)],[b8(0x45), b8(0x67)]).to_bits() == b24(0x326745)

def test_get_bitstruct_inst_all_classes():

  @bitstruct
  class SomeMsg1:
    a: [ Bits4, Bits4 ]
    b: Bits8

  @bitstruct
  class SomeMsg2:
    c: [ SomeMsg1, SomeMsg1 ]
    d: [ Bits6, Bits6 ]

  a = SomeMsg2()
  print()
  print(get_bitstruct_inst_all_classes( a ))
  print({Bits4, Bits8, SomeMsg1, Bits6, SomeMsg2})
  assert get_bitstruct_inst_all_classes( a ) == {Bits4, Bits8, SomeMsg1, Bits6, SomeMsg2}

def test_nbits_to_bits():
  @bitstruct
  class A:
    x: Bits16

  B = mk_bitstruct( "B", {
    'x': Bits100,
    'y': [ A ] * 3,
    'z': A,
  })
  b = B(0x1234567890abcd0f,[A(2),A(3),A(4)], A(5) )
  print(b)

  assert b.nbits == 164
  assert b.to_bits() == Bits164(0x1234567890abcd0f0004000300020005)

def test_from_bits():
  @bitstruct
  class A:
    x: Bits16

  B = mk_bitstruct( "B", {
    'x': Bits100,
    'y': [ A ] * 3,
    'z': A,
  })
  b = B(0x1234567890abcd0f,[A(2),A(3),A(4)], A(5) )

  assert b.to_bits() == Bits164(0x1234567890abcd0f0004000300020005)
  assert b.from_bits( b.to_bits() ) == b

def test_imatmul_ilshift():

  @bitstruct
  class A:
    x: Bits16

  B = mk_bitstruct( "B", {
    'x': Bits100,
    'y': [ A ] * 3,
    'z': A,
  })

  b = B(0x1234567890abcd0f,[A(2),A(3),A(4)], A(5) )

  b @= Bits164(0xf0dcba09876543210005000400030002)
  assert b.to_bits() == Bits164(0xf0dcba09876543210005000400030002)

  c = B(0x1234567890abcd0f,[A(2),A(3),A(4)], A(5) )
  c <<= Bits164(0xf0dcba09876543210005000400030002)
  assert c == B(0x1234567890abcd0f,[A(2),A(3),A(4)], A(5) )
  c._flip()
  assert c.to_bits() == Bits164(0xf0dcba09876543210005000400030002)
