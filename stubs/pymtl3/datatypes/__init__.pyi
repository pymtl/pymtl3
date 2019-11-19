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

class _Bits4(_BitsN): ...
Bits4 = Bits[_Bits4]

class _Bits5(_BitsN): ...
Bits5 = Bits[_Bits5]

class _Bits8(_BitsN): ...
Bits8 = Bits[_Bits8]

class _Bits16(_BitsN): ...
Bits16 = Bits[_Bits16]

class _Bits32(_BitsN): ...
Bits32 = Bits[_Bits32]

#-------------------------------------------------
# clog2
#-------------------------------------------------

def clog2(n: int) -> int: ...
