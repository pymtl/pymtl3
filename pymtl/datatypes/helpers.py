from bits_import import *
import math

def concat( *args ):
  nbits = sum( [ x.nbits for x in args ] )
  concat_bits = Bits( nbits, 0 )

  begin = 0
  for bits in reversed( args ):
    concat_bits[ begin : begin+bits.nbits ] = bits
    begin += bits.nbits

  return concat_bits

def zext( value, new_width ):
  assert new_width > value.nbits
  return Bits( new_width, value )

def clog2( N ):
  assert N > 0
  return int( math.ceil( math.log( N, 2 ) ) )

def sext( value, new_width ):
  assert new_width > value.nbits
  return Bits( new_width, value.int() )
