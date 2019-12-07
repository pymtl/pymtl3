"""
==========================================================================
helpers_test.py
==========================================================================
Test cases for helper functions

Author : Shunning Jiang
  Date : Nov 30, 2019
"""

from pymtl3.datatypes import *
from pymtl3.datatypes.helpers import get_bitstruct_inst_all_classes


def test_concat():
  x = concat( Bits128(0x1234567890abcdef1234567890abcdef),
              Bits252(0xffffffffff22222222222222222444441234567890abcdef1234567890abcdef) )
  assert x.nbits == 380
  assert x == mk_bits(380)(0x1234567890abcdef1234567890abcdeffffffffff22222222222222222444441234567890abcdef1234567890abcdef)

def test_zext():
  assert zext( Bits8(0xe), 24 ) == Bits24(0xe)

def test_sext():
  assert zext( Bits8(0xe), 24 ) == Bits24(0xe)

def test_clog2():
  assert clog2(7) == 3
  assert clog2(8) == 3
  assert clog2(9) == 4

def test_reduce_and():
  for i in range(255):
    assert not reduce_and( b8(i) )
  assert reduce_and( b8(255) )
  assert reduce_and( b512((2**512)-1) )

def test_reduce_or():
  for i in range(1, 256):
    assert reduce_or(i)
  assert not reduce_or( b8(0) )
  assert reduce_or( b512((2**512)-1) )

def test_reduce_xor():
  assert reduce_xor( b8(0b10101011) ) == 1
  assert reduce_xor( b8(0b10101010) ) == 0

def test_get_nbits():

  @bitstruct
  class SomeMsg:
    c: [ Bits3, Bits3 ]
    d: [ Bits5, Bits5 ]

  assert get_nbits( SomeMsg ) == 16

def test_to_bits():

  @bitstruct
  class SomeMsg:
    c: [ Bits4, Bits4 ]
    d: [ Bits8, Bits8 ]

  assert to_bits( SomeMsg([b4(0x2),b4(0x3)],[b8(0x45), b8(0x67)]) ) == b24(0x234567)

def test_get_bitstruct_inst_all_classes():

  @bitstruct
  class SomeMsg1:
    a: [ Bits4, Bits4 ]
    b: Bits8

  @bitstruct
  class SomeMsg2:
    c: [ SomeMsg1, SomeMsg1 ]
    d: [ Bits6, Bits6 ]

  a = SomeMsg2()
  print()
  print(get_bitstruct_inst_all_classes( a ))
  print({Bits4, Bits8, SomeMsg1, Bits6, SomeMsg2})
  assert get_bitstruct_inst_all_classes( a ) == {Bits4, Bits8, SomeMsg1, Bits6, SomeMsg2}
