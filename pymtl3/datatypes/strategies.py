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
# A generic bits strategy.
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

  # RETURN A STRATEGY INSTEAD OF FUNCTION
  return strategy_bits()

# Helper function to handle a list of Bits/structs
def _list( types ):
  # Bitstruct type construction already guarantees that all elements in
  # the list have the same type. Hence we just need to use the first type
  type_ = types[0]

  # a list of types, recursive
  if isinstance( type_, list ):
    strat = _list( type_ )
  # nested bitstruct, RECURSIVE
  elif is_bitstruct_class( type_ ):
    strat = bitstruct( type_ )
  # bits field, directly use bits strategy
  else:
    assert issubclass( type_, Bits )
    strat = bits( type_.nbits, False )

  @st.composite
  def strategy_list( draw ):
    return [ draw(strat) for _ in types ]

  return strategy_list()

# Return the SearchStrategy for bitstruct type T

def bitstruct( T ):
  types = T.__bitstruct_fields__.values()

  # We capture the fields of T inside a list inside closure of the
  # strategy. For each field, we recursively compose a strategy based on
  # the type. The type can be a list of types, a Bits type, or a nested
  # bitstruct. For nested bitstruct, we recursively call the bitstruct(T)
  # function to construct the strategy

  strats = [ None ] * len( types )
  for i, type_ in enumerate( types ):
    # a list of types, call helper function
    if isinstance( type_, list ):
      strats[i] = _list( type_ )
    # nested bitstruct, RECURSIVE
    elif is_bitstruct_class( type_ ):
      strats[i] = bitstruct( type_ )
    # bits field, directly use bits strategy
    else:
      assert issubclass( type_, Bits )
      strats[i] = bits( type_.nbits, False )
    assert strats[i] is not None

  @st.composite
  def strategy_bitstruct( draw ):
    # Since strats already preserves the order of bitstruct fields,
    # we can directly asterisk the generatort to pass in as *args
    return T( * (draw(strat) for strat in strats) )

  # RETURN A STRATEGY INSTEAD OF FUNCTION
  return strategy_bitstruct()
