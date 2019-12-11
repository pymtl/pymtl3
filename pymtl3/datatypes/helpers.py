"""
========================================================================
helpers.py
========================================================================
Useful helper functions of Bits operations. Ideally these functions
should be implemented in RPython.

Author : Shunning Jiang
Date   : Nov 3, 2017
"""
import functools
import math
import operator

from .bits_import import *
from .bitstructs import is_bitstruct_class, is_bitstruct_inst


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

def get_nbits( Type ):
  if isinstance( Type, list ):
    return sum(get_nbits(v) for v in Type )

  assert isinstance( Type, type )
  if issubclass( Type, Bits ):
    return Type.nbits

  assert is_bitstruct_class( Type ), f"{Type} is not a valid PyMTL data type!"
  return sum(get_nbits(v) for v in Type.__bitstruct_fields__.values())

def to_bits( obj ):
  if isinstance( obj, list ):
    return concat( *[ to_bits(x) for x in obj ] )

  # BitsN
  if isinstance( obj, Bits ):
    return obj

  assert not isinstance( obj, int ), f"{obj} is an integer, not Bits or Bitstruct."
  # BitStruct
  assert is_bitstruct_inst( obj ), f"{obj} is not a valid PyMTL Bitstruct!"
  return concat( *[ to_bits(getattr(obj, v)) for v in obj.__bitstruct_fields__.keys() ] )

def get_bitstruct_inst_all_classes( obj ):
  # list: put all types together
  if isinstance( obj, list ):
    return functools.reduce( operator.or_, [ get_bitstruct_inst_all_classes(x) for x in obj ] )
  ret = { obj.__class__ }
  # BitsN or int
  if isinstance( obj, (Bits, int) ):
    return ret
  # BitStruct
  assert is_bitstruct_inst( obj ), f"{obj} is not a valid PyMTL Bitstruct!"
  return ret | functools.reduce( operator.or_, [ get_bitstruct_inst_all_classes(getattr(obj, v))
                                                for v in obj.__bitstruct_fields__.keys() ] )
