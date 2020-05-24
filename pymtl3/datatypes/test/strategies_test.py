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

  actual_test()

@pytest.mark.parametrize( 'length', [5,10,15,20] )
def test_bitslist( length ):
  print("")
  @hypothesis.given(
    blist = pst.bitslists([mk_bits(i+10) for i in range(length)])
  )
  @hypothesis.settings( max_examples=16 )
  def actual_test( blist ):
    for i in range(length):
      assert blist[i].nbits == 10+i
    # print out the fraction of generated random value versus the full range
    print( blist, [ f'{(int(blist[i])/(2**(10+i))*100):.2f}%' for i in range(length)] )

  actual_test()

def test_bitslist_nested_limit():
  type_ = [ [Bits10, Bits11, Bits12], [Bits13, Bits14] ]
  limit_dict = {
    0: {
      0: range(0xa0,0xb0),
      2: range(0xb0,0xc0),
    },
    1: {
      1: range(0xc0,0xd0),
    },
  }
  print("")
  @hypothesis.given(
    blist = pst.bitslists(type_, limit_dict)
  )
  @hypothesis.settings( max_examples=16 )
  def actual_test( blist ):
    assert blist[0][0].nbits == 10
    assert blist[0][1].nbits == 11
    assert blist[0][2].nbits == 12
    assert blist[1][0].nbits == 13
    assert blist[1][1].nbits == 14
    assert 0xa0 <= blist[0][0] <= 0xaf
    assert 0xb0 <= blist[0][2] <= 0xbf
    assert 0xc0 <= blist[1][1] <= 0xcf
    print(blist)

  actual_test()

def test_bitslist_nested_user_strategy():
  type_ = [ [Bits10, Bits11, Bits12], Bits13 ]
  limit_dict = {
    1: pst.bits(13, min_value=0, max_value=10)
  }
  print("")
  @hypothesis.given(
    blist = pst.bitslists(type_, limit_dict)
  )
  @hypothesis.settings( max_examples=16 )
  def actual_test( blist ):
    assert blist[0][0].nbits == 10
    assert blist[0][1].nbits == 11
    assert blist[0][2].nbits == 12
    assert blist[1].nbits == 13
    assert 0 <= blist[1] <= 10
    print(blist)

  actual_test()

def test_bitslist_nested_user_strategy_wrong_type():
  type_ = [ [Bits10, Bits11, Bits12], Bits13 ]
  limit_dict = {
    0: 123,
  }

  try:
    bs = pst.bitslists( type_, limit_dict )
  except TypeError as e:
    print(e)
    return
  raise Exception("Should've thrown TypeError")

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
    bs = pst.bitstructs(T)
  )
  @hypothesis.settings( max_examples=16 )
  def actual_test( bs ):
    assert isinstance( bs, T )
    print( bs )

  actual_test()

def test_nested_point_limited():
  limit_dict = {
    'p1': {
      'x': range(0xe0,0xf0),
    },
    'p2': {
      'y': range(0xf0,0x100),
    }
  }

  print("")
  @hypothesis.given(
    bs = pst.bitstructs(NestedPoint, limit_dict)
  )
  @hypothesis.settings( max_examples=16 )
  def actual_test( bs ):
    assert isinstance( bs, NestedPoint )
    assert 0xe0 <= bs.p1.x <= 0xef
    assert 0xf0 <= bs.p2.y <= 0xff
    print( bs )

  actual_test()

def test_nnested_point_limited():
  limit_dict = {
    'p1': {
      'x': range(0xe0,0xef),
    },
    'p2': {
      'y': range(0xf0,0xff),
    },
    'p3': {
      0: {
        'z': {
          0: range(0xa0, 0xaf),
          1: range(0xb0, 0xbf),
        }
      }
    }
  }

  print("")
  @hypothesis.given(
    bs = pst.bitstructs(NNestedPoint, limit_dict)
  )
  @hypothesis.settings( max_examples=16 )
  def actual_test( bs ):
    assert isinstance( bs, NNestedPoint )
    assert 0xe0 <= bs.p1.x < 0xef
    assert 0xf0 <= bs.p2.y < 0xff
    assert 0xa0 <= bs.p3[0].z[0] < 0xaf
    assert 0xb0 <= bs.p3[0].z[1] < 0xbf
    print( bs )

  actual_test()

def test_nested_point_user_strategy():
  limit_dict = {
    'p1': {
      'x': range(0xe0,0xf0),
    },
    'p2': pst.bitstructs( Point2D, {'x':range(0,2),'y':range(2,4)} )
  }

  print("")
  @hypothesis.given(
    bs = pst.bitstructs(NestedPoint, limit_dict)
  )
  @hypothesis.settings( max_examples=16 )
  def actual_test( bs ):
    assert isinstance( bs, NestedPoint )
    assert 0xe0 <= bs.p1.x <= 0xef
    assert 0 <= bs.p2.x < 2
    assert 2 <= bs.p2.y < 4
    print( bs )

  actual_test()

def test_nested_point_user_strategy_wrong_type():
  limit_dict = {
    'p1': {
      'x': range(0xe0,0xf0),
    },
    'p2': 123
  }

  try:
    bs = pst.bitstructs(NestedPoint, limit_dict)
  except TypeError as e:
    print(e)
    return
  raise Exception("Should've thrown TypeError")
