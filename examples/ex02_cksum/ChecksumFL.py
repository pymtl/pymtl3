"""
==========================================================================
ChecksumFL.py
==========================================================================
Functional level implementation of a checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *

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
