#=========================================================================
# BitStruct_test.py
#=========================================================================
# A basic BitStruct definition.
# 
# Author : Yanghui Ou
#   Date : May 24, 2019

from __future__ import absolute_import, division, print_function

from pymtl import *

from .BitStruct import BitStruct, mk_bit_struct

StaticPoint = mk_bit_struct( "BasePoint", [
    ( 'x', Bits4 ), 
    ( 'y', Bits4 ), 
  ] ) 

# FIXME: The following inherited bit struct cannot be used for construct
# nested struct as the newly made class is not captured in the scope of 
# mk_bit_struct.
# class StaticPoint( 
#   mk_bit_struct( "BasePoint", [
#     ( 'x', Bits16 ), 
#     ( 'y', Bits16 ), 
#   ]) ):
# 
#   def __str__( s ):
#     return "({},{})".format( int(s.x), int(s.y) )

NestedSimple = mk_bit_struct( "NestedSimple", [ 
    ( 'pt0', StaticPoint ), 
    ( 'pt1', StaticPoint ), 
  ] )

def test_struct():
  pt = StaticPoint( Bits4(2), Bits4(4) )
  print( pt           )
  print( pt.to_bits() )
  assert pt.to_bits() == 0x24
  assert pt.x == 2
  assert pt.y == 4
  
  np = NestedSimple( StaticPoint(1,2), StaticPoint(3,4) )
  print( NestedSimple ) 
  print( np           )
  print( np.to_bits() )
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
        s.out = s.in_
        s.out.pt0.x += 1
        s.out.pt0.y -= 1
        s.out.pt1.x += 1
        s.out.pt1.y -= 1
        # s.out_pt = s.in_.pt1 FIXME: this mutates the object in s.in_

  dut = A()
  dut.apply( SimpleSim )
  dut.in_ = NestedSimple( StaticPoint(1,2), StaticPoint(3,4) )
  dut.tick()
  assert dut.out == NestedSimple( StaticPoint(2,1), StaticPoint(4,3) )
  #print( dut.out_pt )
  #assert dut.out_pt == StaticPoint(3,4)
