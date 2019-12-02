"""
==========================================================================
strategies.py
==========================================================================
Hypothesis strategies for built-in data types.

Author : Yanghui Ou
  Date : June 16, 2019
"""
import hypothesis
from hypothesis import strategies as st

from .bits_import import Bits

#-------------------------------------------------------------------------
# A generic bits strategy.
#-------------------------------------------------------------------------

@st.composite
def bits( draw, nbits, signed=False, min_value=None, max_value=None ):
  if nbits == 1:
    value = draw( st.booleans() )
  elif not signed:
    if min_value is None: min_value = 0
    if max_value is None: max_value = 2**nbits - 1
    assert min_value < max_value
    value = draw( st.integers(min_value, max_value) )
  else:
    if min_value is None: min_value = - ( 2 ** (nbits-1) )
    if max_value is None: max_value = 2**(nbits-1) - 1
    assert min_value < max_value
    value = draw( st.integers(min_value, max_value) )

  return Bits( nbits, value )

@st.composite
def bitstruct( draw, Type ):
  if nbits == 1:
    value = draw( st.booleans() )
  elif not signed:
    min_value = 0
    max_value = 2**nbits - 1
    value = draw( st.integers(min_value, max_value) )
  else:
    min_value = - ( 2 ** (nbits-1) )
    max_value = 2**(nbits-1) - 1
    value = draw( st.integers(min_value, max_value) )

  BitsN = mk_bits( nbits )
  return BitsN( value )

#-------------------------------------------------------------------------
# bits_struct_strategy
#-------------------------------------------------------------------------
def bits_struct_strategy( bits_struct_type,
                          predefined={},
                          remaining_names=None ):

  field_strategies = {}
  for name, field_type in bits_struct_type.fields:
    predefined_field = predefined.get( name, {} )
    field_strategies[ name ] = get_strategy_from_type(
        field_type, predefined_field, remaining_names )

  @st.composite
  def strategy( draw ):
    new_bits_struct = bits_struct_type()
    for name, field_type in bits_struct_type.fields:
      # recursively draw st
      data = draw( field_strategies[ name ] )
      setattr( new_bits_struct, name, data )
    return new_bits_struct

  return strategy()


#-------------------------------------------------------------------------
# get_strategy_from_type
#-------------------------------------------------------------------------
def get_strategy_from_type( dtype, predefined={}, remaining_names=None ):
  if isinstance( predefined, tuple ):
    assert isinstance( predefined[ 0 ], SearchStrategy )
    remaining_names.discard( predefined[ 1 ] )
    return predefined[ 0 ]

  if isinstance( dtype(), Bits ):
    if predefined:
      raise TypeError( "Need strategy for Bits type {}".format(
          repr( dtype ) ) )
    return bitstype_strategy( dtype() )

  if isinstance( dtype(), BitStruct ):
    return bits_struct_strategy( dtype, predefined, remaining_names )

  raise TypeError( "Argument strategy for {} not supported".format( dtype ) )
