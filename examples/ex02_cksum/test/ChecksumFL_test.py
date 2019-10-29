"""
==========================================================================
 ChecksumFL_test.py
==========================================================================
Test cases for functional level checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""
import hypothesis
from hypothesis import strategies as st

from pymtl3 import *

from ..ChecksumFL import checksum

#=========================================================================
# Test checksum as a function
#=========================================================================
# We manage all our test cases into a class so that these tests can be
# easily reused across modeling levels through inheritance.

class ChecksumFL_Tests:

  #-----------------------------------------------------------------------
  # cksum_func
  #-----------------------------------------------------------------------
  # Other tests scripts can inherit from this class and overload this
  # method to specify how we should calculate the checksum using the
  # design under test.

  def cksum_func( s, words ):
    return checksum( words )

  #-----------------------------------------------------------------------
  # test_simple
  #-----------------------------------------------------------------------

  def test_simple( s ):
    words = [ b16(x) for x in [ 1, 2, 3, 4, 5, 6, 7, 8 ] ]
    assert s.cksum_func( words ) == b32( 0x00780024 )

  #-----------------------------------------------------------------------
  # test_overflow
  #-----------------------------------------------------------------------

  def test_overflow( s ):
    words = [ b16(x) for x in [ 0xf000, 0xff00, 0x1000, 0x2000,
                                0x5000, 0x6000, 0x7000, 0x8000 ] ]
    assert s.cksum_func( words ) == b32( 0x3900bf00 )

  #-----------------------------------------------------------------------
  # test_order
  #-----------------------------------------------------------------------

  # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''
  # Add a test for ordering
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
  #; Fletcher's algorithm should calculate different checksums for the
  #; same data if that data is in a different order. For example, the
  #; algorithm should calculate different checksums for these two lists
  #; of data:
  #;
  #;   [ 1, 2, 3, 4, 5, 6, 7, 8 ]
  #;   [ 1, 2, 3, 4, 8, 7, 6, 5 ]
  #;
  #; Add a test which verifies this property.

  def test_order( s ):
    words0 = [ b16(x) for x in [ 1, 2, 3, 4, 5, 6, 7, 8 ] ]
    words1 = [ b16(x) for x in [ 1, 2, 3, 4, 8, 7, 6, 5 ] ]
    assert s.cksum_func( words0 ) != s.cksum_func( words1 )
    assert s.cksum_func( words0 ) == b32( 0x00780024 )
    assert s.cksum_func( words1 ) == b32( 0x00820024 )
