"""
==========================================================================
 ChecksumFL_test.py
==========================================================================
Test cases for functional level checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""
from __future__ import absolute_import, division, print_function

import hypothesis
from hypothesis import strategies as st

from pymtl3 import *

from ..ChecksumFL import checksum

#-------------------------------------------------------------------------
# Test checksum as a function
#-------------------------------------------------------------------------
# We manage all our test cases into a class so that these tests can be
# easily reused through inheriting.

class ChecksumFL_Tests( object ):

  # We can overwrite this function after inheriting the test class, in
  # which way we can reuse all the test cases to test another
  # implementation.
  def cksum_func( s, words ):
    return checksum( words )

  def test_simple( s ):
    # Use b16 directly
    words = [ b16(x) for x in [ 1, 2, 3, 4, 5, 6, 7, 8 ] ]
    assert s.cksum_func( words ) == b32( 0x00780024 )

  def test_overflow( s ):
    words = [ b16(x) for x in [ 0xf000, 0xff00, 0x1000, 0x2000,
                                0x5000, 0x6000, 0x7000, 0x8000 ] ]
    assert s.cksum_func( words ) == b32( 0x3900bf00 )

  def test_order( s ):
    # pass
    words0 = [ b16(x) for x in [ 1, 2, 3, 4, 5, 6, 7, 8 ] ]
    words1 = [ b16(x) for x in [ 1, 2, 3, 4, 8, 7, 6, 5 ] ]
    assert s.cksum_func( words0 ) != s.cksum_func( words1 )
    assert s.cksum_func( words0 ) == b32( 0x00780024 )
    assert s.cksum_func( words1 ) == b32( 0x00820024 )

