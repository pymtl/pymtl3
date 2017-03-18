class Bits(int):
  def __new__( cls, nbits, value=0 ):
    inst = int.__new__( cls, value & ((1 << nbits) - 1) )
    inst.nbits = nbits
    return inst

  def __call__( self ):
    return Bits( self.nbits )

  # Arithmetics and its reversed form

  def __add__( self, other ):
    nbits = max( self.nbits, other.nbits )
    # print (int(self) + int(other)), ((1 << nbits) - 1)
    return Bits( nbits, (int(self) + int(other)) & ((1 << nbits) - 1) )
  def __radd__( self, other ):
    return self.__add__( other )

  def __sub__( self, other ):
    nbits = max( self.nbits, other.nbits )
    # print (int(self) - int(other) + (1<<nbits) ), ((1<<nbits) - 1)
    return Bits( nbits, (int(self) - int(other) + (1<<nbits) ) & ((1 << nbits) - 1) )

  def __and__( self, other ):
    nbits = max( self.nbits, other.nbits )
    return Bits( nbits, int(self) & int(other) )
  def __rand__( self, other ):
    return self.__and__( other )

  def __or__( self, other ):
    nbits = max( self.nbits, other.nbits )
    return Bits( nbits, int(self) | int(other) )
  def __ror__( self, other ):
    return self.__or__( other )

  def __xor__( self, other ):
    nbits = max( self.nbits, other.nbits )
    return Bits( nbits, int(self) ^ int(other) )
  def __rxor__( self, other ):
    return self.__xor__( other )

  def __invert__( self ):
    return Bits( self.nbits, ~int(self) )

  def __lshift__( self, other ):
    return Bits( self.nbits, 0 if int(other) > self.nbits else (int(self) << (int(other)) & ((1 << self.nbits) - 1) ) )

  def __rshift__( self, other ):
    return Bits( self.nbits, (int(self) >> int(other)) )

