"""
==========================================================================
strategies.py
==========================================================================
Hypothesis strategies for built-in data types.

Author : Yanghui Ou
  Date : June 16, 2019
"""

import hypothesis
import pytest

from pymtl3.datatypes import strategies as pst
from pymtl3.datatypes.bits_import import *


@pytest.mark.parametrize( 'nbits', [1, 3, 4, 8, 16, 32] )
def test_unsiged( nbits ):
  print("")
  @hypothesis.given(
    bits = pst.bits(nbits)
  )
  @hypothesis.settings( max_examples=16 )
  def actual_test( bits ):
    assert bits.nbits == nbits
    print( bits, bits.uint() )
  actual_test()

@pytest.mark.parametrize( 'nbits', [1, 3, 4, 8, 16, 32] )
def test_signed( nbits ):
  print("")
  @hypothesis.given(
    bits = pst.bits(nbits, True)
  )
  @hypothesis.settings( max_examples=16 )
  def actual_test( bits ):
    assert bits.nbits == nbits
    print( bits, bits.int() )
  actual_test()
