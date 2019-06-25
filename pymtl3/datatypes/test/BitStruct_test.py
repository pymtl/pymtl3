"""
#=========================================================================
# BitStruct_test.py
#=========================================================================
# A basic BitStruct definition.
#
# Author : Yanghui Ou
#   Date : May 24, 2019
"""
from copy import deepcopy

from pymtl3.datatypes.bits_import import Bits4, Bits5, Bits8, b4, mk_bits
from pymtl3.datatypes.BitStruct import BitStruct, mk_bit_struct
from pymtl3.dsl import Component, InPort, OutPort
from pymtl3.dsl.test.sim_utils import simple_sim_pass


# Manually created bit struct
class ManualPixel( BitStruct ):
  # NOTE: User needs to provide fields information if they want it to be
  # translatable. It is not required for simulation, although providing
  # fields information would enable user to some BitStruct APIs such as
  # to_bits.
  fields = [
    ( 'r', Bits8 ),
    ( 'g', Bits8 ),
    ( 'b', Bits8 ),
  ]

  def __init__( s, r=Bits8(), g=Bits8(), b=Bits8() ):
    s.r = r
    s.g = g
    s.b = b

  def __str__( s ):
    return "({},{},{})".format( s.r, s.g, s.b )

# Manually created nested bit struct
class ManualNestedPixel( BitStruct ):
  fields = [
    ( 'px0', ManualPixel ),
    ( 'px1', ManualPixel ),
  ]

  def __init__( s, px0=ManualPixel(), px1=ManualPixel() ):
    s.px0 = px0
    s.px1 = px1

  def __str__( s ):
    return "{},{}".format( s.px0, s.px1 )

# Create bit struct using syntax sugar (mk_bit_struct):
StaticPoint = mk_bit_struct( "StaticPoint", [
    ( 'x', Bits4 ),
    ( 'y', Bits4 ),
  ] )

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

# Create nested struct using mk_bit_struct
NestedSimple = mk_bit_struct( "NestedSimple", [
    ( 'pt0', StaticPoint ),
    ( 'pt1', StaticPoint ),
  ] )

def test_manual():
  px = ManualPixel( Bits8(0xff), Bits8(0xff), Bits8(0xff) )
  assert px.to_bits() == 0xffffff
  assert px.r == 0xff
  assert px.g == 0xff
  assert px.b == 0xff
  px.r = Bits8(0x00)
  assert px.to_bits() == 0x00ffff
  assert px.r == 0x00
  assert px.g == 0xff
  assert px.b == 0xff

  npx = ManualNestedPixel()
  npx.px0 = ManualPixel( Bits8(0x00), Bits8(0xff), Bits8(0xff) )
  npx.px1 = ManualPixel( Bits8(0xff), Bits8(0x00), Bits8(0x00) )
  assert npx.to_bits() == 0x00ffffff0000
  assert npx.px0.to_bits() == 0x00ffff
  assert npx.px1.to_bits() == 0xff0000
  assert npx.px0.r == 0x00
  assert npx.px0.g == 0xff
  assert npx.px0.b == 0xff
  assert npx.px1.r == 0xff
  assert npx.px1.g == 0x00
  assert npx.px1.b == 0x00

def test_struct():
  pt = StaticPoint( Bits4(2), Bits4(4) )
  print( pt           )
  print( pt.to_bits() )
  try:
    StaticPoint.field_nbits( 'haha' )
  except AssertionError as e:
    print( e )
    assert str( e ) == "StaticPoint does not have field haha!"
  assert StaticPoint.nbits == 8
  assert StaticPoint.field_nbits( 'x' ) == 4
  assert StaticPoint.field_nbits( 'y' ) == 4
  assert pt.to_bits() == 0x24
  assert pt.x == 2
  assert pt.y == 4

  np = NestedSimple( StaticPoint(1,2), StaticPoint(3,4) )
  print( NestedSimple )
  print( np           )
  print( np.to_bits() )
  assert NestedSimple.nbits == 16
  assert NestedSimple.field_nbits( 'pt0' ) == 8
  assert NestedSimple.field_nbits( 'pt1' ) == 8
  assert np.pt0 == StaticPoint(1,2)
  assert np.pt0 != StaticPoint(1,1)
  assert np.pt0.x == 1
  assert np.pt0.y == 2
  assert np.pt1.x == 3
  assert np.pt1.y == 4

  try:
    BadStruct = mk_bit_struct( "BadStruct", [
      ( 'x', Bits4 ),
      ( 'x', Bits5 )
    ])
  except AssertionError as e:
    print( e )
    assert str( e ) == "Failed to create BadStruct due to duplicate fields!"

  def dynamic_point( xnbits, ynbits ):
    XType = mk_bits( xnbits )
    YType = mk_bits( ynbits )

    return mk_bit_struct(
      "Point_{}_{}".format( xnbits, ynbits ), [
        ( 'x', XType ),
        ( 'y', YType ),
      ],
      lambda s: "({},{})".format( int(s.x), int(s.y) )
    )

  DPoint = dynamic_point( 4, 8 )
  dp = DPoint( 1, 2 )
  print( DPoint )
  print( dp     )
  assert DPoint.nbits == 12
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
