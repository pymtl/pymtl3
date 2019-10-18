"""
========================================================================
Bits.py
========================================================================
Pure-Python implementation of fixed-bitwidth data type.

Author : Shunning Jiang
Date   : Oct 31, 2017
"""


class Bits:
  __slots__ = ( "nbits", "value" )

  def __init__( self, nbits=32, value=0 ):
    self.nbits = nbits
    self.value = int(value) & ((1 << nbits) - 1)

  def __ilshift__( self, x ):
    try:
      assert x.nbits == self.nbits, "Bitwidth mismatch during <<="
    except AttributeError:
      raise TypeError(f"Assign {type(x)} to Bits")
    self._next = x.value
    return self

  def _flip( self ):
    self.value = self._next

  def __call__( self ):
    return Bits( self.nbits )

  # Arithmetics
  def __getitem__( self, idx ):
    sv = int(self.value)

    if isinstance( idx, slice ):
      start, stop = int(idx.start), int(idx.stop)
      assert not idx.step and start < stop and start >= 0 and stop <= self.nbits, \
            "Invalid access: [{}:{}] in a Bits{} instance".format( start, stop, self.nbits )
      return Bits( stop-start, (sv & ((1 << stop) - 1)) >> start )

    i = int(idx)
    assert 0 <= i < self.nbits
    return Bits( 1, (sv >> i) & 1 )

  def __setitem__( self, idx, v ):
    sv = int(self.value)

    if isinstance( idx, slice ):
      start, stop = int(idx.start), int(idx.stop)
      assert not idx.step and start < stop and start >= 0 and stop <= self.nbits, \
            "Invalid access: [{}:{}] in a Bits{} instance".format( start, stop, self.nbits )

      self.value = (sv & (~((1 << stop) - (1 << start)))) | \
                   ((int(v) & ((1 << (stop - start)) - 1)) << start)
      return

    i = int(idx)
    assert 0 <= i < self.nbits
    self.value = (sv & ~(1 << i)) | ((int(v) & 1) << i)

  def __add__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) + int(other) )
    except: return Bits( self.nbits, int(self.value) + int(other) )

  def __radd__( self, other ):
    return self.__add__( other )

  def __sub__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) - int(other) )
    except: return Bits( self.nbits, int(self.value) - int(other) )

  def __rsub__( self, other ):
    return Bits( self.nbits, other ) - self

  def __mul__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) * int(other) )
    except: return Bits( self.nbits, int(self.value) * int(other) )

  def __rmul__( self, other ):
    return self.__mul__( other )

  def __and__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) & int(other) )
    except: return Bits( self.nbits, int(self.value) & int(other) )

  def __rand__( self, other ):
    return self.__and__( other )

  def __or__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) | int(other) )
    except: return Bits( self.nbits, int(self.value) | int(other) )

  def __ror__( self, other ):
    return self.__or__( other )

  def __xor__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) ^ int(other) )
    except: return Bits( self.nbits, int(self.value) ^ int(other) )

  def __rxor__( self, other ):
    return self.__xor__( other )

  def __div__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) / int(other) )
    except: return Bits( self.nbits, int(self.value) / int(other) )

  def __floordiv__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) / int(other) )
    except: return Bits( self.nbits, int(self.value) / int(other) )

  def __mod__( self, other ):
    try:    return Bits( max(self.nbits, other.nbits), int(self.value) % int(other) )
    except: return Bits( self.nbits, int(self.value) % int(other) )

  def __invert__( self ):
    return Bits( self.nbits, ~int(self.value) )

  def __lshift__( self, other ):
    nb = int(self.nbits)
    # TODO this doesn't work perfectly. We need a really smart
    # optimization that avoids the guard totally
    if int(other) >= nb: return Bits( nb )
    return Bits( nb, int(self.value) << int(other) )

  def __rshift__( self, other ):
    return Bits( self.nbits, int(self.value) >> int(other) )

  def __eq__( self, other ):
    try:
      other = int(other)
    except ValueError:
      return False
    return Bits( 1, int(self.value) == other )

  def __hash__( self ):
    return hash((self.nbits, self.value))

  def __ne__( self, other ):
    try:
      other = int(other)
    except ValueError:
      return True
    return Bits( 1, int(self.value) != other )

  def __lt__( self, other ):
    return Bits( 1, int(self.value) < int(other) )

  def __le__( self, other ):
    return Bits( 1, int(self.value) <= int(other) )

  def __gt__( self, other ):
    return Bits( 1, int(self.value) > int(other) )

  def __ge__( self, other ):
    return Bits( 1, int(self.value) >= int(other) )

  def __bool__( self ):
    return int(self.value) != 0

  def __int__( self ):
    return int(self.value)

  def int( self ):
    if self.value >> (self.nbits - 1):
      return -int(~self + 1)
    return int(self.value)

  def uint( self ):
    return int(self.value)

  def __index__( self ):
    return int(self.value)

  # Print

  def __repr__(self):
    return "Bits{}( {} )".format( self.nbits, self.hex() )

  def __str__(self):
    str = "{:x}".format(int(self.value)).zfill(((self.nbits-1)>>2)+1)
    return str

  def __oct__( self ):
    # print("DEPRECATED: Please use .oct()!")
    return self.oct()

  def __hex__( self ):
    # print("DEPRECATED: Please use .hex()!")
    return self.hex()

  def bin(self):
    str = "{:b}".format(int(self.value)).zfill(self.nbits)
    return "0b"+str

  def oct( self ):
    str = "{:o}".format(int(self.value)).zfill(((self.nbits-1)>>1)+1)
    return "0o"+str

  def hex( self ):
    str = "{:x}".format(int(self.value)).zfill(((self.nbits-1)>>2)+1)
    return "0x"+str
