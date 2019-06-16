"""
==========================================================================
strategies.py
==========================================================================
Hypothesis strategies for built-in data types.

Author : Yanghui Ou
  Date : June 16, 2019
"""
from __future__ import absolute_import, division, print_function

import hypothesis
import pytest

from pymtl3.datatypes.bits_import import *
from pymtl3.datatypes.strategies import bits_strat


@pytest.mark.parametrize( 'nbits', [3, 4, 8, 16, 32] )
def test_unsiged_pro( nbits ):
  print("")
  @hypothesis.given(
    bits = bits_strat(nbits)
  )
  @hypothesis.settings( max_examples=16 )
  def actual_test( bits ):
    assert bits.nbits == nbits
    print( bits, bits.uint() )
  actual_test()

@pytest.mark.parametrize( 'nbits', [1, 3, 4, 8, 16, 32] )
def test_signed_pro( nbits ):
  print("")
  @hypothesis.given(
    bits = bits_strat(nbits, True)
  )
  @hypothesis.settings( max_examples=16 )
  def actual_test( bits ):
    assert bits.nbits == nbits
    print( bits, bits.int() )
  actual_test()
