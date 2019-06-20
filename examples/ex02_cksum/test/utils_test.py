"""
==========================================================================
utils.py
==========================================================================
Helper functions for the checksum unit. They convert 

Author : Yanghui Ou
  Date : June 6, 2019
"""
from __future__ import absolute_import, division, print_function

import hypothesis
from hypothesis import strategies as st

from pymtl3 import *

from ..utils import b128_to_words, words_to_b128

#-------------------------------------------------------------------------
# Test helper functions with hypothesis
#-------------------------------------------------------------------------

# TODO: Write a directed test for utils

def test_b128_to_words():
  bits = b128(0x00010002000300040005000600070008)
  words = [ 8, 7, 6, 5, 4, 3, 2, 1 ]
  assert b128_to_words( bits ) == words

def test_words_to_b128():
  bits = b128(0x00010002000300040005000600070008)
  words = [ 8, 7, 6, 5, 4, 3, 2, 1 ]
  assert words_to_b128( words ) == bits

@st.composite
def bits_strat( draw, nbits ):
  value = draw( st.integers(0, 2**nbits - 1 ) )
  BitsN = mk_bits( nbits )
  return BitsN( value )

# TODO: Add a Bits strategy
@hypothesis.given(
  words = st.lists( bits_strat(16), min_size=8, max_size=8 ) 
)
def test_words_to_b128_to_words( words ):
  assert b128_to_words( words_to_b128( words ) ) == words

@hypothesis.given(
  bits = bits_strat(128)
)
def test_b128_to_words_to_b128( bits ):
  assert words_to_b128( b128_to_words( bits ) ) == bits
