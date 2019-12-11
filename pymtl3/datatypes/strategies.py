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
# strategies.bitslists
#-------------------------------------------------------------------------
# Return the SearchStrategy for a list of Bits with the support of
# dictionary based min/max value limit

def bitslists( types, limit_dict=None ):
  # Make sure limit_dict becomes a dict, not None
  limit_dict = limit_dict or {}
  if not isinstance( limit_dict, dict ):
    raise TypeError( f"bitlist '{types}' doesn't not take '{limit_dict}' " \
                      "to specify min/max limit. Here only a dictionary " \
                      "like { 0:range(1,2), 1:range(3,4) } is accepted. " )

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
# strategies.bitstructs
#-------------------------------------------------------------------------
# Return the SearchStrategy for bitstruct type T with the support of
# dictionary-based min/max value limit

def bitstructs( T, limit_dict=None ):
  # Make sure limit_dict becomes a dict, not None
  limit_dict = limit_dict or {}
  if not isinstance( limit_dict, dict ):
    raise TypeError( f"bitstruct '{T}' doesn't not take '{limit_dict}' " \
                      "to specify min/max limit. Here only a dictionary " \
                      "like { 'x':range(1,2), 'y':range(3,4), 'z': { ... } } is accepted. " )

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

  # User-specified search strategy, early exit
  if isinstance( limit, st.SearchStrategy ):
    return limit

  # a list of types
  if isinstance( T, list ):
    return bitslists( T, limit )

  # nested bitstruct
  if is_bitstruct_class( T ):
    return bitstructs( T, limit )

  # bits field, "leaf node", directly use bits strategy
  assert issubclass( T, Bits )
  if limit is None:
    return bits( T.nbits )

  # bits field with range limit
  assert isinstance( limit, range ), f"We only accept range as min/max value specifier, not {type(limit)}"
  assert limit.step == 1, f"We only accept step=1 range, not {limit}."
  assert limit.start < limit.stop, f"We only accept start < stop range, not {limit}"

  return bits( T.nbits, False, limit.start, limit.stop-1 )
