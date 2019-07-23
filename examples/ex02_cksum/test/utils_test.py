"""
==========================================================================
utils.py
==========================================================================
Helper functions for the checksum unit to convert a list of 16b words to
a single Bits object and to convert a single Bits object to a list of 16b
words.

Author : Yanghui Ou
  Date : June 6, 2019

"""
import hypothesis
from hypothesis import strategies as st

import pymtl3.datatypes.strategies as pst
from pymtl3 import *

from ..utils import b128_to_words, words_to_b128

#-------------------------------------------------------------------------
# Directed Tests
#-------------------------------------------------------------------------

def test_bits2words():
  bits = b128(0x00010002000300040005000600070008)
  words = [ b16(x) for x in [ 8, 7, 6, 5, 4, 3, 2, 1 ]]
  assert b128_to_words( bits ) == words

def test_words2bits():
  bits = b128(0x00010002000300040005000600070008)
  words = [ b16(x) for x in [ 8, 7, 6, 5, 4, 3, 2, 1 ]]
  assert words_to_b128( words ) == bits

#-------------------------------------------------------------------------
# Hypothesis Tests
#-------------------------------------------------------------------------

# ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Add Hypothesis test
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
#; Add a Hypothesis tests to verify that converting words to bits and
#; then bits to words always returns the original words.

@hypothesis.given( words=st.lists( pst.bits(16), min_size=8, max_size=8 ) )
def test_hypothesis( words ):
  print(words)
  assert b128_to_words( words_to_b128( words ) ) == words
