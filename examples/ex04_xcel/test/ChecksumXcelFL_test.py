
"""
==========================================================================
ChecksumXcelFL_test.py
==========================================================================
Tests for the functional level checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.stdlib.ifcs import mk_xcel_msg

from examples.ex02_cksum.test.ChecksumCL_test import ChecksumCL_Tests as BaseTests
from ..ChecksumXcelFL import ChecksumXcelFL

#-------------------------------------------------------------------------
# Wrap Xcel into a function
#-------------------------------------------------------------------------

Req, Resp = mk_xcel_msg( 3, 32 )

def checksum_fl( words ):
  assert len( words ) == 8
  dut = ChecksumXcelFL()
  dut.apply( SimpleSim )

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

class ChecksumXcelFL_Tests( BaseTests ):

  def cksum_func( s, words ):
    return checksum_fl( words )