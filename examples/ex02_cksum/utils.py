"""
==========================================================================
utils.py
==========================================================================
Helper functions for the checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""

from functools import reduce

from pymtl3 import *

#-------------------------------------------------------------------------
# words_to_b128 converts a list of Bits16 to Bits128
#-------------------------------------------------------------------------

def words_to_b128( words ):
  assert len( words ) == 8
  bits = reduce( lambda x, y: concat( y, x ), words )
  return bits

#-------------------------------------------------------------------------
# Helper function that converts Bits128 to a list of Bits16
#-------------------------------------------------------------------------

def b128_to_words( bits ):
  assert bits.nbits == 128
  words = [ bits[i*16:(i+1)*16] for i in range( 8 ) ]
  return words
