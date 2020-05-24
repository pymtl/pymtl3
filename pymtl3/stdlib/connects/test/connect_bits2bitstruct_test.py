'''
==========================================================================
connect_bits2bitstruct_test.py
==========================================================================
Unit tests for connect_bits2bitstruct.

Author : Yanghui Ou
  Date : Feb 24, 2020
'''
from pymtl3 import *

from ..connect_bits2bitstruct import connect_bits2bitstruct

#-------------------------------------------------------------------------
# Bitstructs for unit tests
#-------------------------------------------------------------------------

@bitstruct
class Point:
  x : Bits8
  y : Bits4

@bitstruct
class Nested:
  z    : Bits6
  pt   : Point
  flag : Bits1

#-------------------------------------------------------------------------
# Unit test for imatmul casting
#-------------------------------------------------------------------------

def test_imatmul_bits2bitstruct_simple():

  class Bits2Bitstruct( Component ):
    def construct( s ):
      s.pt_bits      = InPort ( Bits12 )
      s.pt_bitstruct = OutPort( Point  )
      @update
      def up_2():
        s.pt_bitstruct @= s.pt_bits

  a = Bits2Bitstruct()
  a.elaborate()
  a.apply( DefaultPassGroup() )
  a.pt_bits @= 0xeda
  a.sim_eval_combinational()
  assert a.pt_bitstruct.x == 0xed
  assert a.pt_bitstruct.y == 0xa

def test_imatmul_bitstruct2bits_simple():

  class Bitstruct2Bits( Component ):
    def construct( s ):
      s.pt_bitstruct = InPort ( Point  )
      s.pt_bits      = OutPort( Bits12 )
      @update
      def up_2():
        s.pt_bits @= s.pt_bitstruct

  b = Bitstruct2Bits()
  b.elaborate()
  b.apply( DefaultPassGroup() )
  b.pt_bitstruct.x @= 0xed
  b.pt_bitstruct.y @= 0xa
  b.sim_eval_combinational()
  assert b.pt_bits == 0xeda

def test_imatmul_bits2bitstruct_nested():

  class Bits2BitstructNested( Component ):
    def construct( s ):
      s.pt_bits      = InPort ( Bits19 )
      s.pt_bitstruct = OutPort( Nested )
      @update
      def up_2():
        s.pt_bitstruct @= s.pt_bits

  a = Bits2BitstructNested()
  a.elaborate()
  a.apply( DefaultPassGroup() )
  a.pt_bits @= concat( b6(0x3f), b12(0xeda), b1(1) )
  a.sim_eval_combinational()
  assert a.pt_bitstruct.z    == 0x3f
  assert a.pt_bitstruct.pt.x == 0xed
  assert a.pt_bitstruct.pt.y == 0xa
  assert a.pt_bitstruct.flag == 1

def test_imatmul_bitstruct2bits_nested():

  class Bitstruct2BitsNested( Component ):
    def construct( s ):
      s.pt_bitstruct = InPort ( Nested )
      s.pt_bits      = OutPort( Bits19 )
      @update
      def up_2():
        s.pt_bits @= s.pt_bitstruct

  b = Bitstruct2BitsNested()
  b.elaborate()
  b.apply( DefaultPassGroup() )
  b.pt_bitstruct.z    @= 0x3f
  b.pt_bitstruct.pt.x @= 0xed
  b.pt_bitstruct.pt.y @= 0xa
  b.pt_bitstruct.flag @= 0x1
  b.sim_eval_combinational()
  assert b.pt_bits == concat( b6(0x3f), b12(0xeda), b1(1) )

#-------------------------------------------------------------------------
# Components for connect tests
#-------------------------------------------------------------------------

class Bits2Bitstruct( Component ):
  def construct( s ):
    s.pt_bits      = InPort ( Bits12 )
    s.pt_bitstruct = OutPort( Point  )
    connect_bits2bitstruct( s.pt_bits, s.pt_bitstruct )

class Bitstruct2Bits( Component ):
  def construct( s ):
    s.pt_bitstruct = InPort ( Point  )
    s.pt_bits      = OutPort( Bits12 )
    @update
    def up_2():
      s.pt_bits @= s.pt_bitstruct

class Bits2BitstructNested( Component ):
  def construct( s ):
    s.pt_bits      = InPort ( Bits19 )
    s.pt_bitstruct = OutPort( Nested )
    @update
    def up_2():
      s.pt_bitstruct @= s.pt_bits

class Bitstruct2BitsNested( Component ):
  def construct( s ):
    s.pt_bitstruct = InPort ( Nested )
    s.pt_bits      = OutPort( Bits19 )
    @update
    def up_2():
      s.pt_bits @= s.pt_bitstruct

#-------------------------------------------------------------------------
# Unit test fos connect_bits2bitstruct
#-------------------------------------------------------------------------

def test_connect_bits2bitstruct_simple():

  class Bits2Bitstruct( Component ):
    def construct( s ):
      s.pt_bits      = InPort ( Bits12 )
      s.pt_bitstruct = OutPort( Point  )
      connect_bits2bitstruct( s.pt_bits, s.pt_bitstruct )

  a = Bits2Bitstruct()
  a.elaborate()
  a.apply( DefaultPassGroup() )
  a.pt_bits @= 0xeda
  a.sim_eval_combinational()
  assert a.pt_bitstruct.x == 0xed
  assert a.pt_bitstruct.y == 0xa

def test_connect_bitstruct2bits_simple():

  class Bitstruct2Bits( Component ):
    def construct( s ):
      s.pt_bitstruct = InPort ( Point  )
      s.pt_bits      = OutPort( Bits12 )
      connect_bits2bitstruct( s.pt_bitstruct, s.pt_bits )

  b = Bitstruct2Bits()
  b.elaborate()
  b.apply( DefaultPassGroup() )
  b.pt_bitstruct.x @= 0xed
  b.pt_bitstruct.y @= 0xa
  b.sim_eval_combinational()
  assert b.pt_bits == 0xeda

def test_connect_bits2bitstruct_nested():

  class Bits2BitstructNested( Component ):
    def construct( s ):
      s.pt_bits      = InPort ( Bits19 )
      s.pt_bitstruct = OutPort( Nested )
      connect_bits2bitstruct( s.pt_bits, s.pt_bitstruct )

  a = Bits2BitstructNested()
  a.elaborate()
  a.apply( DefaultPassGroup() )
  a.pt_bits @= concat( b6(0x3f), b12(0xeda), b1(1) )
  a.sim_eval_combinational()
  assert a.pt_bitstruct.z    == 0x3f
  assert a.pt_bitstruct.pt.x == 0xed
  assert a.pt_bitstruct.pt.y == 0xa
  assert a.pt_bitstruct.flag == 1

def test_connect_bitstruct2bits_nested():

  class Bitstruct2BitsNested( Component ):
    def construct( s ):
      s.pt_bitstruct = InPort ( Nested )
      s.pt_bits      = OutPort( Bits19 )
      connect_bits2bitstruct( s.pt_bitstruct, s.pt_bits )

  b = Bitstruct2BitsNested()
  b.elaborate()
  b.apply( DefaultPassGroup() )
  b.pt_bitstruct.z    @= b6( 0x3f )
  b.pt_bitstruct.pt.x @= b8( 0xed )
  b.pt_bitstruct.pt.y @= b4( 0xa  )
  b.pt_bitstruct.flag @= b1( 0x1  )
  b.sim_eval_combinational()
  assert b.pt_bits == concat( b6(0x3f), b12(0xeda), b1(1) )
