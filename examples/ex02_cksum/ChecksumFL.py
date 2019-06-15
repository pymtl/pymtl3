"""
==========================================================================
ChecksumFL.py
==========================================================================
Functional level implementation of a checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""
from __future__ import absolute_import, division, print_function

from functools import reduce

from pymtl3 import *

#-------------------------------------------------------------------------
# Helper function that converts a list of Bits16 to Bits128
#-------------------------------------------------------------------------
# Let people implement words_to_b128 
# Show something pythonic solutions

def words_to_b128( words ):
  assert len( words ) == 8
  # A more pythonic version
  bits = reduce( lambda x, y: concat( y, x ), words )
  # Add a for loop one
  # bits = b128(0)
  # for i in range( 8 ):
  #   bits =  ( bits | words[-i] ) << 16
  return bits

#-------------------------------------------------------------------------
# Helper function that converts Bits128 to a list of Bits16
#-------------------------------------------------------------------------

def b128_to_words( bits ):
  assert bits.nbits == 128
  words = [ bits[i*16:(i+1)*16] for i in range( 8 ) ]
  return words

#-------------------------------------------------------------------------
# Checksum FL
#-------------------------------------------------------------------------

def checksum( words ):

  sum1 = b32(0)
  sum2 = b32(0)
  for word in words:
    sum1 = ( sum1 + word ) & 0xffff
    sum2 = ( sum2 + sum1 ) & 0xffff

  return ( sum2 << 16 ) | sum1
