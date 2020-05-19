"""
==========================================================================
ChecksumXcelFL_test.py
==========================================================================
Tests for the functional level checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
from examples.ex02_cksum.test.ChecksumCL_test import ChecksumCL_Tests as BaseTests
from pymtl3 import *
from pymtl3.stdlib.ifcs import mk_xcel_msg

from ..ChecksumXcelFL import ChecksumXcelFL

#-------------------------------------------------------------------------
# Wrap Xcel into a function
#-------------------------------------------------------------------------

Req, Resp = mk_xcel_msg( 3, 32 )

def checksum_xcel_fl( words ):
  assert len( words ) == 8

  # Create a simulator using ChecksumXcelFL
  dut = ChecksumXcelFL()
  dut.elaborate()
  dut.apply( DefaultPassGroup() )

  # Transfer checksum input
  for i in range( 4 ):
    data = concat( words[i*2+1], words[i*2] )
    dut.xcel.write( i, data )

  # Set the go bit
  dut.xcel.write( 4, b32(1) )

  # get result
  return dut.xcel.read( 5 )

#-------------------------------------------------------------------------
# Test checksum as a function
#-------------------------------------------------------------------------
# We reuse the extened function tests in ex02_cksum.test.ChecksumCL_test.


# ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Implement the tests for ChecksumXcelFL
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
#; Write a ChecksumXcelFL_Tests class that inherits from BaseTests which
#; is basically ChecksumCL_Tests. ChecksumCL_Tests is developed in Task 2
#; for the checksum unit.

class ChecksumXcelFL_Tests( BaseTests ):

  def cksum_func( s, words ):
    return checksum_xcel_fl( words )

# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\
