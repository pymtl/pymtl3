#=======================================================================
# Bits_test.py
#=======================================================================
# Tests for the Bits class.
# Shunning: grabbed from PyMTL2. Thanks Derek Lockhart

from copy import deepcopy

import pytest

from ..bits_import import Bits


def test_return_type():

  x = Bits( 8, 0b1100 )
  assert isinstance( x.uint(), int  )
  assert isinstance( x.int(),  int  )
  assert isinstance( x[1:2],   Bits )
  assert isinstance( x[0:4],   Bits )
  assert isinstance( x[2],     Bits )

def test_int():

  assert Bits( 4,  0 ).int() == 0
  assert Bits( 4,  2 ).int() == 2
  assert Bits( 4,  4 ).int() == 4
  assert Bits( 4, 15 ).int() == -1
  assert Bits( 4, -1 ).int() == -1
  assert Bits( 4, -2 ).int() == -2
  assert Bits( 4, -4 ).int() == -4
  assert Bits( 4, -8 ).int() == -8

def test_int_bounds_checking():

  Bits( 4, 15 )
  with pytest.raises( ValueError ): Bits( 4, 16 )

  Bits( 4, -8 )
  with pytest.raises( ValueError ): Bits( 4, -9 )
  with pytest.raises( ValueError ): Bits( 4, -16 )

  Bits( 1, 0 )
  Bits( 1, 1 )
  Bits( 1, -1 )
  # with pytest.raises( ValueError ): Bits( 1, -1 )
  with pytest.raises( ValueError ): Bits( 1, -2 )

def test_uint():

  assert Bits( 4,  0 ).uint() == 0
  assert Bits( 4,  2 ).uint() == 2
  assert Bits( 4,  4 ).uint() == 4
  assert Bits( 4, 15 ).uint() == 15
  assert Bits( 4, -1 ).uint() == 15
  assert Bits( 4, -2 ).uint() == 14
  assert Bits( 4, -4 ).uint() == 12

def test_neg_assign():

  x = Bits( 4, -1 )
  assert x        == 0b1111
  assert x.uint() == 0b1111
  x = Bits( 4, -2 )
  assert x        == 0b1110
  assert x.uint() == 0b1110

def test_get_bit():

  x = Bits( 4, 0b1100 )
  assert x[3] == 1
  assert x[2] == 1
  assert x[1] == 0
  assert x[0] == 0

def test_set_bit():

  x = Bits( 4, 0b1100 )
  x[3] = 0
  assert x.uint() == 0b0100
  x[2] = 1
  assert x.uint() == 0b0100
  x[1] = 1
  assert x.uint() == 0b0110

  x = Bits( 4, 0b100 )
  x[2] = Bits(1,0)
  assert x.uint() == 0

  with pytest.raises( ValueError ):
    x[2] = Bits(2,1)

def test_bit_bounds_checking():

  x = Bits( 4, 0b1100 )
  with pytest.raises( IndexError ):
    assert x[-1] == 1
  with pytest.raises( IndexError ):
    assert x[8] == 1
  with pytest.raises( IndexError ):
    x[-1] = 1
  with pytest.raises( IndexError ):
    x[4] = 1
  with pytest.raises( ValueError ):
    x[0] = 2
  # with pytest.raises( ValueError ):
  x[3] = -1

def test_get_slice():

  x = Bits( 4, 0b1100 )
  assert x[:] == 0b1100
  assert x[2:4] == 0b11
  assert x[0:1] == 0b0
  assert x[1:3] == 0b10
  # check open ended ranges
  assert x[1:] == 0b110
  assert x[:3] == 0b100

  with pytest.raises( IndexError ):
    x[1:3:1]

def test_set_slice():

  x = Bits( 4, 0b1100 )
  x[:] = 0b0010
  assert x.uint() == 0b0010
  x[2:4] = 0b11
  assert x.uint() == 0b1110
  x[0:1] = 0b1
  assert x.uint() == 0b1111
  x[1:3] = 0b10
  assert x.uint() == 0b1101
  # check open ended ranges
  x[1:] = 0b001
  assert x.uint() == 0b0011
  x[:3] = 0b110
  assert x.uint() == 0b0110

  with pytest.raises( ValueError ):
    x[1:3] = Bits(1,1)

  with pytest.raises( ValueError ):
    x[1:3] = Bits(3,1)

  x[1:3] = Bits(2,1)
  assert x.uint() == 0b0010

  x[:]   = 0b1111
  assert x.uint() == 0b1111

  with pytest.raises( ValueError ):
    x[:]   = 0b10000

  with pytest.raises( IndexError ):
    x[1:4:2] = 1

def test_slice_bounds_checking():

  x = Bits( 4, 0b1100 )
  with pytest.raises( IndexError ):
    assert x[1:5]  == 0b10
  with pytest.raises( IndexError ):
    assert x[-1:2] == 0b10
  with pytest.raises( IndexError ):
    assert x[2:1]  == 0b10
  with pytest.raises( IndexError ):
    x[1:5]  = 0b10
  with pytest.raises( IndexError ):
    x[-1:2] = 0b10
  with pytest.raises( IndexError ):
    x[2:1]  = 0b10
  # FIXED
  # Bits objects constructed with another Bits object provided as a value
  # parameter end up having problems when writing to slices.  This is
  # because the mask used when writing to a subslice is often a negative
  # int in Python, and we don't allow operations on Bits to be performed
  # with negative values.  Current workaround is to force the value param
  # for the Bits constructor to be an int or a long.
  #with pytest.raises( AssertionError ):
  y = Bits( 4, Bits( 4, 0 ))
  y[1:3] = 1


def test_eq():

  x = Bits( 4, 0b1010 )
  assert x.uint() == x.uint()
  # Compare objects by value, not id
  assert x == x
  # Check the value
  assert x.uint() == 0b1010
  assert x.uint() == 0xA
  assert x.uint() == 10
  # Checking the equality operator
  assert x == 0b1010
  assert x == 0xA
  assert x == 10
  # Checking comparison with another bit container
  y = Bits( 4, 0b1010 )
  assert x.uint() == y.uint()
  assert x == y
  y = Bits( 8 , 0b1010 )
  assert x.uint() == y.uint()
  # TODO: How should equality between Bits objects work?
  #       Just same value or same value and width?
  #assert x == y
  # Check the negatives
  x = Bits( 4, -1 )
  assert x.uint() == 0b1111
  assert x.uint() == 0xF
  assert x.uint() == 15
  # Checking the equality operator
  assert x == 0b1111
  assert x == 0xF
  assert x == 15
  assert x.uint() == Bits(4, -1).uint()
  assert x == Bits( 4, -1 ).uint()
  assert 15 == x

  assert not x == None
  assert not Bits( 4, 0 ) == None
  with pytest.raises( ValueError ):
    Bits(4,3) == Bits(3, 2)

def test_ne():

  x = Bits( 4, 0b1100 )
  y = Bits( 4, 0b0011 )
  # TODO: check width?
  assert x.uint() != y.uint()
  assert x != y
  # added for bug
  z = Bits( 1, 0 )
  assert z.uint() != 1
  assert z != 1
  assert 5 != x

  assert z != None
  assert Bits( 4, 0 ) != None

def test_compare_neg_assert():

  x = Bits( 4, -2 )
  # We don't allow comparison with negative numbers,
  # although you can construct a new Bits object with one...
  with pytest.raises( ValueError ):
    assert x != -1
  with pytest.raises( ValueError ):
    assert x == -2
  with pytest.raises( ValueError ):
    assert x >  -3
  with pytest.raises( ValueError ):
    assert x >= -3
  with pytest.raises( ValueError ):
    assert x <  -1
  with pytest.raises( ValueError ):
    assert x >= -1
  assert x != Bits( 4, -1 )
  assert x == Bits( 4, -2 )
  assert x >  Bits( 4, -3 )
  assert x >= Bits( 4, -3 )
  assert x <  Bits( 4, -1 )
  assert x <= Bits( 4, -1 )

def test_compare_uint_neg():

  x = Bits( 4, 2 )
  assert x.uint() != -1
  assert x.uint()  > -1
  assert x.uint() >= -1

def test_compare_int_neg():

  x = Bits( 4, -2 )
  assert x.int() == -2
  assert x.int()  < -1
  assert x.int() <= -1

def test_lt():

  x = Bits( 4, 0b1100 )
  y = Bits( 4, 0b0011 )
  assert y.uint() < x.uint()
  assert y.uint() < 10
  assert y < x.uint()
  assert y < 10
  assert y < x
  assert 1 < y
  with pytest.raises( ValueError ):
    x < -1
  with pytest.raises( ValueError ):
    Bits(4,3) < Bits(3, 2)

def test_gt():

  x = Bits( 4, 0b1100 )
  y = Bits( 4, 0b0011 )
  assert x.uint() > y.uint()
  assert x.uint() > 2
  assert x > y.uint()
  assert x > 2
  assert x > y
  assert 9 > y
  with pytest.raises( ValueError ):
    x > -1
  with pytest.raises( ValueError ):
    Bits(4,3) > Bits(3, 2)

def test_lte():

  x = Bits( 4, 0b1100 )
  y = Bits( 4, 0b0011 )
  z = Bits( 4, 0b0011 )
  assert y.uint() <= x.uint()
  assert y.uint() <= 10
  assert y.uint() <= z.uint()
  assert y.uint() <= 0b0011
  assert y <= x.uint()
  assert y <= 10
  assert y <= z.uint()
  assert y <= 0b0011
  assert y <= x
  assert y <= z
  assert z <= x
  assert z <= z
  assert 1 <= y
  assert 3 <= y
  with pytest.raises( ValueError ):
    x <= -1
  with pytest.raises( ValueError ):
    Bits(4,3) <= Bits(3, 2)

def test_gte():

  x = Bits( 4, 0b1100 )
  y = Bits( 4, 0b0011 )
  z = Bits( 4, 0b1100 )
  assert x.uint() >= y.uint()
  assert x.uint() >= 2
  assert x.uint() >= z.uint()
  assert x.uint() >= 0b1100
  assert x >= y.uint()
  assert x >= 2
  assert x >= z.uint()
  assert x >= 0b1100
  assert x >= y
  assert x >= z
  assert z >= y
  assert z >= x
  assert x >= x
  assert 5 >= y
  assert 3 <= y
  with pytest.raises( ValueError ):
    x >= -1
  with pytest.raises( ValueError ):
    Bits(4,3) >= Bits(3, 2)

def test_invert():

  x = Bits( 4, 0b0001 )
  assert ~x == 0b1110
  x = Bits( 4, 0b1001 )
  assert ~x == 0b0110
  x = Bits( 16, 0b1111000011110000 )
  assert ~x == 0b0000111100001111

def test_add():

  x = Bits( 4, 4 )
  y = Bits( 4, 4 )
  assert x + y == 8
  assert x + Bits( 4, 4 ) == 8
  assert x + 4 == 8
  y = Bits( 4, 14 )
  assert x + y == 2
  assert x + 14 == 2
  assert 14 + x == 2

  a = Bits( 4, 1 )
  b = Bits( 4, 1 )
  c = Bits( 4, 1 )
  assert a + b + 1 == 3
  assert a + b + c == 3
  assert c + b + a == 3
  with pytest.raises( ValueError ):
    x + -1
  with pytest.raises( ValueError ):
    x + 100000000000000000000000000

  with pytest.raises( ValueError ):
    a = Bits(4,3) + Bits(3,1)

def test_sub():

  x = Bits( 4, 5 )
  y = Bits( 4, 4 )
  assert x - y == 1
  assert x - Bits(4, 4) == 1
  assert x - 4 == 1
  y = Bits( 4, 5 )
  assert x - y == 0
  assert x - 5 == 0
  y = Bits( 4, 7 )
  assert x - y == 0b1110
  assert x - 7 == 0b1110
  assert 9 - x == 0b0100
  with pytest.raises( ValueError ):
    x - -1
  with pytest.raises( ValueError ):
    x - 100000000000000000000000000

  with pytest.raises( ValueError ):
    a = Bits(4,3) - Bits(3,1)

def test_rsub():
  x = Bits(4, 5)
  y = 8
  z = y - x
  assert z.nbits == 4 and z.uint() == 3
  y = 16
  with pytest.raises( ValueError ):
    z = y - x

def test_floordiv():

  x = Bits( 4, 5 )
  y = Bits( 4, 4 )
  assert x // y == 1
  assert x // Bits(4, 4) == 1
  assert x // 4 == 1
  y = Bits( 4, 6 )
  assert x // y == 0
  assert x // 6 == 0
  assert 6 // x == 1
  with pytest.raises( ValueError ):
    x // -1
  with pytest.raises( ValueError ):
    x // 100000000000000000000000000

  with pytest.raises( ValueError ):
    a = Bits(4,3) // Bits(3,1)

def test_rfloordiv():
  x = Bits(4, 3)
  y = 8
  z = y // x
  assert z.nbits == 4 and z.uint() == 2
  y = 16
  with pytest.raises( ValueError ):
    z = y // x

def test_mod():

  x = Bits( 4, 5 )
  y = Bits( 4, 4 )
  assert x % y == 1
  assert x % Bits(4, 4) == 1
  assert x % 4 == 1
  y = Bits( 4, 6 )
  assert x % y == 5
  assert x % 6 == 5
  assert 6 % x == 1
  with pytest.raises( ValueError ):
    x % -1
  with pytest.raises( ValueError ):
    x % 100000000000000000000000000

  with pytest.raises( ValueError ):
    a = Bits(4,3) % Bits(3,1)

def test_rmod():
  x = Bits(4, 3)
  y = 8
  z = y % x
  assert z.nbits == 4 and z.uint() == 2
  y = 16
  with pytest.raises( ValueError ):
    z = y % x

def test_lshift():

  x = Bits( 8, 0b1100 )
  y = Bits( 8, 4 )
  assert x << y == 0b11000000
  assert x << 4 == 0b11000000
  assert x << 6 == 0b00000000
  assert y << x == 0b00000000
  assert y << 0 == 0b00000100
  assert y << 1 == 0b00001000
  assert x << 255 == 0

  with pytest.raises( ValueError ):
    a = Bits(4,3) << Bits(3,1)
  with pytest.raises( ValueError ):
    a = x << 256


def test_rshift():

  x = Bits( 8, 0b11000000 )
  y = Bits( 8, 4 )
  assert x >> y  == 0b00001100
  assert x >> 7  == 0b00000001
  assert x >> 8  == 0b00000000
  assert x >> 10 == 0b00000000
  x = Bits( 8, 2 )
  assert y >> x == 0b00000001
  assert y >> 0 == 0b00000100
  assert y >> 2 == 0b00000001
  assert y >> 5 == 0b00000000
  assert x >> 255 == 0

  with pytest.raises( ValueError ):
    a = Bits(4,3) >> Bits(3,1)
  with pytest.raises( ValueError ):
    a = x >> 256

def test_and():

  x = Bits( 8, 0b11001100 )
  y = Bits( 8, 0b11110000 )
  assert x & y      == 0b11000000
  assert x & 0b1010 == 0b00001000
  assert 0b1010 & x == 0b00001000
  with pytest.raises( ValueError ):
    x & -1
  with pytest.raises( ValueError ):
    x & 100000000000000000000000000

  with pytest.raises( ValueError ):
    a = Bits(4,3) & Bits(3,1)

def test_or():

  x = Bits( 8, 0b11001100 )
  y = Bits( 8, 0b11110000 )
  assert x | y      == 0b11111100
  assert x | 0b1010 == 0b11001110
  assert 0b1010 | x == 0b11001110
  with pytest.raises( ValueError ):
    x | -1
  with pytest.raises( ValueError ):
    x | 100000000000000000000000000
  with pytest.raises( ValueError ):
    a = Bits(4,3) | Bits(3,1)

def test_xor():

  x = Bits( 8, 0b11001100 )
  y = Bits( 8, 0b11110000 )
  assert x ^ y      == 0b00111100
  assert x ^ 0b1010 == 0b11000110
  assert 0b1010 ^ x == 0b11000110
  a = Bits( 1, 1 )
  b = Bits( 1, 0 )
  c = Bits( 1, 1 )
  assert ( a ^ b ) ^ c == 0
  with pytest.raises( ValueError ):
    x ^ -1
  with pytest.raises( ValueError ):
    x ^ 100000000000000000000000000
  with pytest.raises( ValueError ):
    a = Bits(4,3) ^ Bits(3,1)

# Now we always require the user to perform sext/zext of the multiply operand
def test_mult():

  x = Bits( 8, 0b00000000 )
  y = Bits( 8, 0b00000000 )
  assert x * y == 0b0000000000000000
  assert x * 0b1000 == 0b0000000000000000
  x = Bits( 8, 0b11111111 )
  y = Bits( 8, 0b11111111 )
  assert Bits( 16, x.uint() ) * Bits( 16, y.uint() ) == 0b0000000000000001111111000000001
  assert Bits( 16, x.uint() ) * 0b11111111 == 0b0000000000000001111111000000001
  assert 0b11111111 * Bits(16, x.uint() ) == 0b0000000000000001111111000000001

  # TODO: Currently fails as the second operand is larger than the Bits
  # object x. Should update the test when we define the behaviour
  #assert x * 0b1111111111 == 0b0000000000000001111111000000001

  y = Bits( 8, 0b10000000 )
  assert Bits( 16, x.uint() ) * Bits( 16, y.uint() ) == 0b0000000000000000111111110000000
  with pytest.raises( ValueError ):
    x * -1
  with pytest.raises( ValueError ):
    x * 100000000000000000000000000
  with pytest.raises( ValueError ):
    a = Bits(4,3) * Bits(3,1)

def test_constructor():

  assert Bits( 4,  2 ).uint() == 2
  assert Bits( 4,  4 ).uint() == 4
  assert Bits( 4, 15 ).uint() == 15
  assert Bits( 4, 17, trunc_int=True ).uint() == 1

  assert Bits( 4, -2 ).uint() == 0b1110
  assert Bits( 4, -4 ).uint() == 0b1100

  assert Bits( 4 ) == Bits( 4, 0 )
  assert Bits( 4 ).uint() == 0

  with pytest.raises( ValueError ):
    a = Bits(4,17)

def test_construct_from_bits():

  assert Bits( 4, Bits(4, -2) ).uint() == 0b1110
  assert Bits( 4, Bits(4, -4) ).uint() == 0b1100

  with pytest.raises( ValueError ):
    a = Bits( 4, Bits(3, -4) )
  with pytest.raises( ValueError ):
    a = Bits( 4, Bits(5, -4) )

  a = Bits( 8, 5 )
  assert a                                  == 0x05
  assert Bits( 16, a.uint() ).uint()        == 0x0005
  assert Bits( 16, (~a + 1).uint() ).uint() == 0x00FB
  b = Bits( 32, 5 )
  assert b                         == 0x00000005
  assert Bits( 32, ~b + 1 ).uint() == 0xFFFFFFFB
  c = Bits( 32, 0 )
  assert c                         == 0x00000000
  assert Bits( 32, ~c )            == 0xFFFFFFFF
  assert Bits( 32, ~c + 1 )        == 0x00000000
  d = Bits( 4, -1 )
  assert Bits( 8, d.uint() )              == 0x0F

  assert Bits( Bits(4,4), 1 ).uint() == 1

def test_str():

  assert Bits(  4,        0x2 ).__str__() == "2"
  assert Bits(  8,       0x1f ).__str__() == "1f"
  assert Bits( 32, 0x0000beef ).__str__() == "0000beef"
  with pytest.raises( ValueError ):
    assert Bits(  4, Bits(32,2) ).__str__() == "2"

def test_index_array():

  data = range( 2**4 )

  # Indexing into an array
  x = Bits( 4, 3  )
  assert data[ x ] == 3

  # Note, this converts -2 to unsigned, so 14!
  y = Bits( 4, -2 )
  assert data[ y ] == 14

  # Larger bitwidths work as long as the list is big enough
  a = Bits( 8, 4  )
  assert data[ a ] == 4

  # If not, regular indexing error
  b = Bits( 8, 20 )
  with pytest.raises( IndexError ):
    data[ b ]

  # Same with negative that become out of range when converted to unsigned
  c = Bits( 8, -1 )
  with pytest.raises( IndexError ):
    data[ c ]

def test_index_bits():

  data = Bits( 8, 0b11001010 )

  # Indexing into a bits
  x = Bits( 4, 3  )
  assert data[ x ] == 1

  # Note, this converts -8 to unsigned, so 8! Out of range!
  y = Bits( 4, -8 )
  with pytest.raises( IndexError ):
    data[ y ]

  # Larger bitwidths work as long as the list is big enough
  a = Bits( 8, 4  )
  assert data[ a ] == 0

  # If not, regular indexing error
  b = Bits( 8, 20 )
  with pytest.raises( IndexError ):
    data[ b ]

  # Same with negative that become out of range when converted to unsigned
  c = Bits( 8, -1 )
  with pytest.raises( IndexError ):
    data[ c ]

def test_slice_bits():

  data = Bits( 8, 0b1101 )

  # Indexing into a bits
  x = Bits( 4, 2  )
  assert data[ : ]   == 0b1101
  assert data[x: ]   == 0b11
  assert data[ :x]   == 0b01
  with pytest.raises( IndexError ):
    assert data[x:x] == 0b1

def test_clone():
  a = Bits(4,3)
  b = a.clone()
  assert a is not b
  assert a == b

def test_deepcopy():
  a = Bits(4,3)
  b = deepcopy( a )
  assert a is not b
  assert a == b

def test_ilshift():

  a = Bits(8,12)
  with pytest.raises( ValueError ):
    a <<= 256
  a <<= 2
  a <<= Bits(8,1)
  with pytest.raises( ValueError ):
    a <<= Bits(7,1)
  with pytest.raises( ValueError ):
    a <<= Bits(9,1)
  a._flip()
  assert a == 1

def test_imatmul():

  a = Bits(8,12)

  with pytest.raises( TypeError ):
    a @ 1

  with pytest.raises( ValueError ):
    a @= 256
  a @= 2
  a @= Bits(8,1)
  assert a == 1
  with pytest.raises( ValueError ):
    a @= Bits(7,1)
  with pytest.raises( ValueError ):
    a @= Bits(9,1)

def test_hash():
  a = Bits(4,12)
  assert hash(a) == hash( (4,12) )

def test_repr():
  assert repr( Bits(15,35) ) == 'Bits15(0x0023)'
  assert repr( Bits(16,35) ) == 'Bits16(0x0023)'
  assert repr( Bits(17,35) ) == 'Bits17(0x00023)'

def test_bin_oct_hex():
  assert Bits(15,35).bin() == "0b000000000100011"
  assert Bits(15,35).oct() == "0o00043"
  assert Bits(15,35).hex() == "0x0023"
