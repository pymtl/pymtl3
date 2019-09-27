from typing import *

#-------------------------------------------------
# Bits
#-------------------------------------------------

T_Bits = TypeVar( "T_Bits" )

class Bits( Generic[T_Bits] ): ...

#-------------------------------------------------
# BitsN
#-------------------------------------------------

T_Bits1 = TypeVar( "T_Bits1" )
Bits1 = Bits[T_Bits1]

T_Bits2 = TypeVar( "T_Bits2" )
Bits2 = Bits[T_Bits2]

T_Bits4 = TypeVar( "T_Bits4" )
Bits4 = Bits[T_Bits4]

T_Bits5 = TypeVar( "T_Bits5" )
Bits5 = Bits[T_Bits5]

T_Bits8 = TypeVar( "T_Bits8" )
Bits8 = Bits[T_Bits8]

T_Bits16 = TypeVar( "T_Bits16" )
Bits16 = Bits[T_Bits16]

T_Bits32 = TypeVar( "T_Bits32" )
Bits32 = Bits[T_Bits32]
