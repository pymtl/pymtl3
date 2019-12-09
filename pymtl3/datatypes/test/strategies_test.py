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
from pymtl3.datatypes.bitstructs import bitstruct


@pytest.mark.parametrize( 'nbits', [1, 3, 4, 8, 16, 32] )
def test_bits_unsigned( nbits ):
  print("")
  @hypothesis.given(
    bits = pst.bits(nbits)
  )
  @hypothesis.settings( max_examples=16 )
  def actual_test( bits ):
    assert bits.nbits == nbits
    print( bits, bits.uint() )

  print("-"*10,nbits,"-"*10)
  actual_test()

@pytest.mark.parametrize( 'nbits', [1, 3, 4, 8, 16, 32] )
def test_bits_signed( nbits ):
  print("")
  @hypothesis.given(
    bits = pst.bits(nbits, True)
  )
  @hypothesis.settings( max_examples=16 )
  def actual_test( bits ):
    assert bits.nbits == nbits
    print( bits, bits.int() )

  print("-"*10,nbits,"-"*10)
  actual_test()

def test_bits16_limited():
  print("")
  @hypothesis.given(
    bits = pst.bits(16, min_value=2, max_value=11)
  )
  @hypothesis.settings( max_examples=16 )
  def actual_test( bits ):
    assert bits.nbits == 16
    assert 2 <= bits.uint() <= 11
    print( bits, bits.uint() )

  print("-"*10,16,'limited',"-"*10)
  actual_test()
@bitstruct
class Point1D:
  x: Bits12

@bitstruct
class Point2D:
  x: Bits16
  y: Bits20

@bitstruct
class Point3D:
  x: Bits100
  y: Bits4
  z: Bits8

@bitstruct
class Point3Dx2:
  x: [ Bits100, Bits100 ]
  y: [ Bits4, Bits4 ]
  z: [ Bits8, Bits8 ]

@bitstruct
class NestedPoint:
  p1: Point1D
  p2: Point2D
  p3: Point3D

@bitstruct
class NNestedPoint:
  p1: Point1D
  p2: Point2D
  p3: [ Point3Dx2, Point3Dx2 ]

@pytest.mark.parametrize( 'T', [Point1D, Point2D, Point3D, Point3Dx2, NestedPoint , NNestedPoint] )
def test_bitstruct( T ):
  print("")
  @hypothesis.given(
    bs = pst.bitstruct(T)
  )
  @hypothesis.settings( max_examples=16 )
  def actual_test( bs ):
    assert isinstance( bs, T )
    print( bs )

  print("-"*10,T,"-"*10)
  actual_test()
