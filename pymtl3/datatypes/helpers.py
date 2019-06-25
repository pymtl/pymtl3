"""
========================================================================
helpers.py
========================================================================
Useful helper functions of Bits operations. Ideally these functions
should be implemented in RPython.

Author : Shunning Jiang
Date   : Nov 3, 2017
"""
import math

from .bits_import import *


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

def reduce_and( value ):
  try:
    return b1( int(value) == (1 << value.nbits) - 1 )
  except AttributeError:
    raise TypeError("Cannot call reduce_and on int")

def reduce_or( value ):
  try:
    return b1( int(value) != 0 )
  except AttributeError:
    raise TypeError("Cannot call reduce_or on int")

def reduce_xor( value ):
  try:
    pop_count = 0
    value = int(value)
    while value != 0:
      pop_count += value & 1
      value >>= 1
    return b1( pop_count & 1 )

  except AttributeError:
    raise TypeError("Cannot call reduce_xor on int")
