"""
==========================================================================
 ChecksumFL_test.py
==========================================================================
Test cases for functional level checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""
from __future__ import absolute_import, division, print_function

from unittest import TestCase

import hypothesis
from hypothesis import strategies as st

from pymtl3 import *

from .ChecksumFL import b128_to_words, checksum, words_to_b128

#-------------------------------------------------------------------------
# Test helper functions with hypothesis
#-------------------------------------------------------------------------

# TODO: Write a directed test for utils

def test_b128_to_words():
  bits = b128(0x00010002000300040005000600070008)
  words = [ 8, 7, 6, 5, 4, 3, 2, 1 ]
  assert b128_to_words( bits ) == words

def test_words_to_b128():
  pass

# TODO: Add a Bits strategy
@hypothesis.given(
  words = st.lists( st.integers(0, 2**16-1), min_size=8, max_size=8 ) 
)
def test_helper( words ):
  words = [ b16(x) for x in words ]
  assert b128_to_words( words_to_b128( words ) ) == words

#-------------------------------------------------------------------------
# Test checksum as a function
#-------------------------------------------------------------------------

class ChecksumFL_Tests( object ):

  def func_impl( s, words ):
    return checksum( words )

  def test_simple( s ):
    words = [ 1, 2, 3, 4, 5, 6, 7, 8 ]
    words = [ b16(x) for x in words ] # Convert words to a list of Bits16
    assert s.func_impl( words ) == b32( 0x00780024 )

  def test_order( s ):
    words0 = [ 1, 2, 3, 4, 5, 6, 7, 8 ]
    words1 = [ 1, 2, 3, 4, 8, 7, 6, 5 ]
    words0 = [ b16(x) for x in words0 ]
    words1 = [ b16(x) for x in words1 ]
    assert s.func_impl( words0 ) != s.func_impl( words1 )
    assert s.func_impl( words0 ) == b32( 0x00780024 )
    assert s.func_impl( words1 ) == b32( 0x00820024 )

  def test_overflow( s ):
    words = [ 0xf000, 0xff00, 0x1000, 0x2000,
              0x5000, 0x6000, 0x7000, 0x8000 ]
    words = [ b16(x) for x in words ]
    assert s.func_impl( words ) == b32( 0x3900bf00 )
