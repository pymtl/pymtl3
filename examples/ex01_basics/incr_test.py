"""
==========================================================================
incr_test.py
==========================================================================
An increment python function that uses PyMTL bits.

Author : Yanghui Ou
  Date : June 17, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *

#-------------------------------------------------------------------------
#  An 8-bit increment function
#-------------------------------------------------------------------------

def incr_8bit( x ):
  return b8(x) + b8(1)

#-------------------------------------------------------------------------
#  Directed tests for the incr_8bit function
#-------------------------------------------------------------------------

def test_incr_8bit_simple():
  assert incr_8bit( b8(1) ) == b8(2)