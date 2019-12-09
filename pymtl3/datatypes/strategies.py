"""
==========================================================================
strategies.py
==========================================================================
Hypothesis strategies for built-in data types.

Author : Shunning Jiang, Yanghui Ou
  Date : Dec 9, 2019
"""
import hypothesis
from hypothesis import strategies as st

from .bits_import import Bits, mk_bits
from .bitstructs import is_bitstruct_class

#-------------------------------------------------------------------------
# strategies.bits
#-------------------------------------------------------------------------
# Return the SearchStrategy for Bits_nbits with the support to limit
# min/max value and setting signedness

def bits( nbits, signed=False, min_value=None, max_value=None ):
  BitsN = mk_bits( nbits )

  if (min_value is not None or max_value is not None) and signed:
    raise ValueError("bits strategy currently doesn't support setting "
                     "signedness and min/max value at the same time")

  if min_value is None:
    min_value = (-(2**(nbits-1))) if signed else 0
  if max_value is None:
    max_value = (2**(nbits-1)-1)  if signed else (2**nbits - 1)

  strat = st.booleans() if nbits == 1 else st.integers( min_value, max_value )

  @st.composite
  def strategy_bits( draw ):
    return BitsN( draw( strat ) )

  return strategy_bits() # RETURN A STRATEGY INSTEAD OF FUNCTION

#-------------------------------------------------------------------------
# strategies.bitslist
#-------------------------------------------------------------------------
# Return the SearchStrategy for a list of Bits with the support of
# dictionary based min/max value limit

def bitslist( types, limit_dict=None ):
  # Make sure limit_dict becomes a dict, not None
  limit_dict = limit_dict or {}
  assert isinstance( limit_dict, dict ), "bitslist only takes a dictionary " \
                                         "e.g. { 0:(1,2), 1:(3,4) } to specify min/max limit"

  # We capture the strategies inside a list inside closure of the
  # strategy. For each element, we recursively compose a strategy based on
  # the type and the field limit.

  strats = [ _strategy_dispatch( type_, limit_dict.get( i, None ) )
              for i, type_ in enumerate(types) ]

  @st.composite
  def strategy_list( draw ):
    return [ draw(strat) for strat in strats ]

  return strategy_list() # RETURN A STRATEGY INSTEAD OF FUNCTION

#-------------------------------------------------------------------------
# strategies.bitstruct
#-------------------------------------------------------------------------
# Return the SearchStrategy for bitstruct type T with the support of
# dictionary-based min/max value limit

def bitstruct( T, limit_dict=None ):
  # Make sure limit_dict becomes a dict, not None
  limit_dict = limit_dict or {}
  assert isinstance( limit_dict, dict ), "bitstruct only takes a dictionary " \
                                         "e.g. { 'x':(1,2), 'y':(3,4) } to specify min/max limit"

  # We capture the fields of T inside a list inside closure of the
  # strategy. For each field, we recursively compose a strategy based on
  # the type and the field limit.

  strats = [ _strategy_dispatch( type_, limit_dict.get( name, None ) )
              for name, type_ in T.__bitstruct_fields__.items() ]

  @st.composite
  def strategy_bitstruct( draw ):
    # Since strats already preserves the order of bitstruct fields,
    # we can directly asterisk the generatort to pass in as *args
    return T( * (draw(strat) for strat in strats) )

  return strategy_bitstruct() # RETURN A STRATEGY INSTEAD OF FUNCTION

# Dispatch to construct corresponding strategy based on given type
# The type can be a list of types, a Bits type, or a nested
# bitstruct. For nested bitstruct, we recursively call the bitstruct(T)
# function to construct the strategy
def _strategy_dispatch( T, limit ):

  # a list of types
  if isinstance( T, list ):
    return bitslist( T, limit )

  # nested bitstruct
  if is_bitstruct_class( T ):
    return bitstruct( T, limit )

  # bits field, "leaf node", directly use bits strategy
  assert issubclass( T, Bits )
  if limit is None:
    return bits( T.nbits )

  # bits field with limit
  assert isinstance( limit, tuple )
  min_value, max_value = limit
  assert min_value < max_value
  return bits( T.nbits, False, min_value, max_value )
