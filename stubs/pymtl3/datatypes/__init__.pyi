from typing import *

#-------------------------------------------------
# Bits
#-------------------------------------------------

# T_Bits is covariant because we want BitsN to be
# the top in the Bits data type hierarchy
T_Bits = TypeVar( "T_Bits", covariant=True )

class Bits( Generic[T_Bits] ): ...

#-------------------------------------------------
# BitsN
#-------------------------------------------------

class _BitsN: ...
BitsN = Bits[_BitsN]

class _Bits1(_BitsN): ...
Bits1 = Bits[_Bits1]

class _Bits2(_BitsN): ...
Bits2 = Bits[_Bits2]

class _Bits3(_BitsN): ...
Bits3 = Bits[_Bits3]

class _Bits4(_BitsN): ...
Bits4 = Bits[_Bits4]

class _Bits5(_BitsN): ...
Bits5 = Bits[_Bits5]

class _Bits6(_BitsN): ...
Bits6 = Bits[_Bits6]

class _Bits7(_BitsN): ...
Bits7 = Bits[_Bits7]

class _Bits8(_BitsN): ...
Bits8 = Bits[_Bits8]

class _Bits9(_BitsN): ...
Bits9 = Bits[_Bits9]

class _Bits10(_BitsN): ...
Bits10 = Bits[_Bits10]

class _Bits16(_BitsN): ...
Bits16 = Bits[_Bits16]

class _Bits17(_BitsN): ...
Bits17 = Bits[_Bits17]

class _Bits32(_BitsN): ...
Bits32 = Bits[_Bits32]

class _Bits33(_BitsN): ...
Bits33 = Bits[_Bits33]

#-------------------------------------------------
# clog2
#-------------------------------------------------

def clog2(n: int) -> int: ...

#-------------------------------------------------
# mk_bits
#-------------------------------------------------

def mk_bits( nbits: int ) -> BitsN: ...

#--------------------------------------------------
# get_nbits
#--------------------------------------------------

def get_nbits( Type: int ) -> int: ...
