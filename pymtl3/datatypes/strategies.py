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

from .bits_import import mk_bits

#-------------------------------------------------------------------------
# A generic bits strategy.
#-------------------------------------------------------------------------

@st.composite
def bits( draw, nbits, signed=False ):
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
