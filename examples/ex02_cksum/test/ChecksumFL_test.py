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
# You can reuse

class ChecksumFL_Tests( object ):

  # You can overwrite this function when inheriting...
  def cksum_func( s, words ):
    return checksum( words )

  def test_simple( s ):
    # Use b16 directly
    words = [ 1, 2, 3, 4, 5, 6, 7, 8 ]
    words = [ b16(x) for x in words ] # Convert words to a list of Bits16
    assert s.cksum_func( words ) == b32( 0x00780024 )

  def test_overflow( s ):
    words = [ 0xf000, 0xff00, 0x1000, 0x2000,
              0x5000, 0x6000, 0x7000, 0x8000 ]
    words = [ b16(x) for x in words ]
    assert s.cksum_func( words ) == b32( 0x3900bf00 )

  def test_order( s ):
    # pass
    words0 = [ 1, 2, 3, 4, 5, 6, 7, 8 ]
    words1 = [ 1, 2, 3, 4, 8, 7, 6, 5 ]
    words0 = [ b16(x) for x in words0 ]
    words1 = [ b16(x) for x in words1 ]
    assert s.cksum_func( words0 ) != s.cksum_func( words1 )
    assert s.cksum_func( words0 ) == b32( 0x00780024 )
    assert s.cksum_func( words1 ) == b32( 0x00820024 )

