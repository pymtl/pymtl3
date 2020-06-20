"""
========================================================================
Bits.py
========================================================================
Pure-Python implementation of fixed-bitwidth data type.

Author : Shunning Jiang
Date   : Oct 31, 2017
"""

# lower <= value <= upper
_upper = [ 0,  1 ]
_lower = [ 0, -1 ]

for i in range(2, 1024):
  _upper.append( (_upper[i-1] << 1) + 1 )
  _lower.append(  _lower[i-1] << 1      )

object_new = object.__new__
def _new_valid_bits( nbits, uint ):
  ret = object_new( Bits )
  ret._nbits = nbits
  ret._uint  = uint
  return ret

class Bits:
  __slots__ = ( "_nbits", "_uint", "_next" )

  @property
  def nbits( self ):
    return self._nbits

  def __init__( self, nbits, v=0, trunc_int=False ):
    nbits = int(nbits)
    if nbits < 1 or nbits >= 1024: raise ValueError(f"Only support 1 <= nbits < 1024, not {nbits}")

    self._nbits = nbits

    if isinstance( v, Bits ):
      if nbits != v.nbits:
        if nbits < v.nbits:
          raise ValueError( f"The Bits{v.nbits} object on RHS is too wide to be used to construct Bits{nbits}!\n"
                            f"- Suggestion: directly use trunc( value, {nbits}/Bits{nbits} )" )
        else:
          raise ValueError( f"The Bits{v.nbits} object on RHS is too narrow to be used to construct Bits{nbits}!\n"
                            f"- Suggestion: directly use zext/sext(value, {nbits}/Bits{nbits} )" )
      self._uint = v._uint
    else:
      v = int(v)
      up = _upper[nbits]

      if not trunc_int:
        lo = _lower[nbits]
        if v < lo or v > up:
          raise ValueError( f"Value {hex(v)} is too wide for Bits{nbits}!\n" \
                            f"(Bits{nbits} only accepts {hex(lo)} <= value <= {hex(up)})" )
      self._uint = v & up

  # PyMTL simulation specific

  def __ilshift__( self, v ):
    nbits = self._nbits
    try:
      # Bits/Bitstruct
      if v.nbits != nbits:
        if v.nbits < nbits:
          raise ValueError( f"Bitwidth of LHS must be equal to RHS during <<= non-blocking assignment, " \
                            f"but here LHS Bits{nbits} > RHS Bits{v.nbits}.\n"
                            f"- Suggestion: LHS @= zext/sext(RHS, nbits/Type)" )
        else:
          raise ValueError( f"Bitwidth of LHS must be equal to RHS during <<= non-blocking assignment, " \
                            f"but here LHS Bits{nbits} < RHS Bits{v.nbits}.\n"
                            f"- Suggestion: LHS @= trunc(RHS, nbits/Type)" )
      self._next = v.to_bits()._uint
    except AttributeError:
      # Cast to int
      v = int(v)
      lo = _lower[nbits]
      up = _upper[nbits]

      if v < lo or v > up:
        raise ValueError( f"RHS value {hex(v)} of <<= is too wide for LHS Bits{nbits}!\n" \
                          f"(Bits{nbits} only accepts {hex(lo)} <= value <= {hex(up)})" )
      self._next = v & up

    return self

  def _flip( self ):
    self._uint = self._next

  def clone( self ):
    return _new_valid_bits( self._nbits, self._uint )

  def __deepcopy__( self, memo ):
    return _new_valid_bits( self._nbits, self._uint )

  def __imatmul__( self, v ):
    nbits = self._nbits
    try:
      # Bits/Bitstruct
      if v.nbits != nbits:
        if v.nbits < nbits:
          raise ValueError( f"Bitwidth of LHS must be equal to RHS during @= blocking assignment, " \
                            f"but here LHS Bits{nbits} > RHS Bits{v.nbits}.\n"
                            f"- Suggestion: LHS @= zext/sext(RHS, nbits/Type)" )
        else:
          raise ValueError( f"Bitwidth of LHS must be equal to RHS during @= blocking assignment, " \
                            f"but here LHS Bits{nbits} < RHS Bits{v.nbits}.\n"
                            f"- Suggestion: LHS @= trunc(RHS, nbits/Type)" )
      self._uint = v.to_bits()._uint
    except AttributeError:
      # Cast to int
      v = int(v)

      lo = _lower[nbits]
      up = _upper[nbits]

      if v < lo or v > up:
        raise ValueError( f"RHS value {hex(v)} of @= is too wide for LHS Bits{nbits}!\n" \
                          f"(Bits{nbits} only accepts {hex(lo)} <= value <= {hex(up)})" )
      self._uint = v & up

    return self

  def to_bits( self ):
    return self

  # Arithmetics
  def __getitem__( self, idx ):

    if isinstance( idx, slice ):
      if idx.step:
        raise IndexError( "Index cannot contain step" )
      try:
        start, stop = int(idx.start or 0), int(idx.stop or self._nbits)
        assert 0 <= start < stop <= self._nbits
      except:
        raise IndexError( f"Invalid access: [{idx.start}:{idx.stop}] in a Bits{self._nbits} instance" )

      # Bypass check
      nbits = stop - start
      return _new_valid_bits( stop-start, (self._uint >> start) & _upper[nbits] )

    i = int(idx)
    if i >= self._nbits or i < 0:
      raise IndexError( f"Invalid access: [{i}] in a Bits{self._nbits} instance" )

    # Bypass check
    return _new_valid_bits( 1, (self._uint >> i) & 1 )

  def __setitem__( self, idx, v ):
    sv = int(self._uint)

    if isinstance( idx, slice ):
      if idx.step:
        raise IndexError( "Index cannot contain step" )
      try:
        start, stop = int(idx.start or 0), int(idx.stop or self._nbits)
        assert 0 <= start < stop <= self._nbits
      except:
        raise IndexError( f"Invalid access: [{idx.start}:{idx.stop}] in a Bits{self._nbits} instance" )

      slice_nbits = stop - start
      if isinstance( v, Bits ):
        if v.nbits != slice_nbits:
          if v.nbits < slice_nbits:
            raise ValueError( f"Cannot fit a Bits{v.nbits} object into a {slice_nbits}-bit slice [{start}:{stop}]\n"
                              f"- Suggestion: sext/zext the RHS")
          else:
            raise ValueError( f"Cannot fit a Bits{v.nbits} object into a {slice_nbits}-bit slice [{start}:{stop}]\n"
                              f"- Suggestion: trunc the RHS")

        self._uint = (sv & (~((1 << stop) - (1 << start)))) | \
                     ((v._uint & _upper[slice_nbits]) << start)
      else:
        # Cast to int
        v = int(v)
        lo = _lower[slice_nbits]
        up = _upper[slice_nbits]

        if v < lo or v > up:
          raise ValueError( f"Cannot fit {v} into a Bits{slice_nbits} slice\n" \
                            f"(Bits{slice_nbits} only accepts {hex(lo)} <= value <= {hex(up)})" )

        self._uint = (sv & (~((1 << stop) - (1 << start)))) | \
                     ((v & _upper[slice_nbits]) << start)
      return

    i = int(idx)
    if i >= self._nbits or i < 0:
      raise IndexError( f"Invalid access: [{i}] in a Bits{self._nbits} instance" )

    if isinstance( v, Bits ):
      if v.nbits > 1:
        raise ValueError( f"Cannot fit a Bits{v.nbits} object into the 1-bit slice" )
      self._uint = (sv & ~(1 << i)) | ((v._uint & 1) << i)
    else:
      v = int(v)
      if abs(v) > 1:
        raise ValueError( f"Value {hex(v)} is too big for the 1-bit slice!\n" )
      self._uint = (sv & ~(1 << i)) | ((int(v) & 1) << i)

  def __add__( self, other ):
    nbits = self._nbits
    try:
      if other.nbits != nbits:
        raise ValueError( f"Operands of '+' (add) operation must have matching bitwidth, "\
                          f"but here Bits{nbits} != Bits{other.nbits}.\n" )
      return _new_valid_bits( nbits, (self._uint + other._uint) & _upper[nbits] )
    except AttributeError:
      other = int(other)
      up = _upper[ nbits ]
      if other < 0 or other > up:
        raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{nbits}!\n"
                          f"Suggestion: 0 <= x <= {hex(up)}" )
      return _new_valid_bits( nbits, (self._uint + other) & up )

  def __radd__( self, other ):
    return self.__add__( other )

  def __sub__( self, other ):
    nbits = self._nbits
    try:
      if other.nbits != nbits:
        raise ValueError( f"Operands of '-' (sub) operation must have matching bitwidth, "\
                          f"but here Bits{nbits} != Bits{other.nbits}.\n" )
      return _new_valid_bits( nbits, (self._uint - other._uint) & _upper[nbits] )
    except AttributeError:
      other = int(other)
      up = _upper[ nbits ]
      if other < 0 or other > up:
        raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{nbits}!\n"
                          f"Suggestion: 0 <= x <= {hex(up)}" )
      return _new_valid_bits( nbits, (self._uint - other) & up )

  def __rsub__( self, other ):
    nbits = self._nbits
    # Shouldn't be Bits
    other = int(other)
    up = _upper[ nbits ]
    if other < 0 or other > up:
      raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{nbits}!\n"
                        f"Suggestion: 0 <= x <= {hex(up)}" )
    return _new_valid_bits( nbits, (other - self._uint) & up )

  def __mul__( self, other ):
    nbits = self._nbits
    try:
      if other.nbits != nbits:
        raise ValueError( f"Operands of '*' (mul) operation must have matching bitwidth, "\
                          f"but here Bits{nbits} != Bits{other.nbits}.\n" )
      return _new_valid_bits( nbits, (self._uint * other._uint) & _upper[nbits] )
    except AttributeError:
      other = int(other)
      up = _upper[ nbits ]
      if other < 0 or other > up:
        raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{nbits}!\n"
                          f"Suggestion: 0 <= x <= {hex(up)}" )
      return _new_valid_bits( nbits, (self._uint * other) & up)

  def __rmul__( self, other ):
    return self.__mul__( other )

  # no need to AND mask
  def __and__( self, other ):
    nbits = self._nbits
    try:
      if other.nbits != nbits:
        raise ValueError( f"Operands of '&' (and) operation must have matching bitwidth, "\
                          f"but here Bits{nbits} != Bits{other.nbits}.\n" )
      return _new_valid_bits( nbits, self._uint & other._uint )
    except AttributeError:
      other = int(other)
      if other < 0 or other > _upper[ nbits ]:
        raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{nbits}!\n"
                          f"Suggestion: 0 <= x <= {hex(_upper[ nbits ])}" )
      return _new_valid_bits( nbits, self._uint & other )

  def __rand__( self, other ):
    return self.__and__( other )

  # no need to AND mask
  def __or__( self, other ):
    nbits = self._nbits
    try:
      if other.nbits != nbits:
        raise ValueError( f"Operands of '|' (or) operation must have matching bitwidth, "\
                          f"but here Bits{nbits} != Bits{other.nbits}.\n" )
      return _new_valid_bits( nbits, self._uint | other._uint )
    except AttributeError:
      other = int(other)
      if other < 0 or other > _upper[ nbits ]:
        raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{nbits}!\n"
                          f"Suggestion: 0 <= x <= {hex(_upper[ nbits ])}" )
      return _new_valid_bits( nbits, self._uint | other )

  def __ror__( self, other ):
    return self.__or__( other )

  def __xor__( self, other ):
    nbits = self._nbits
    try:
      if other.nbits != nbits:
        raise ValueError( f"Operands of  '^' (xor) operation must have matching bitwidth, "\
                          f"but here Bits{nbits} != Bits{other.nbits}.\n" )
      return _new_valid_bits( nbits, self._uint ^ other._uint )
    except AttributeError:
      other = int(other)
      if other < 0 or other > _upper[ self._nbits ]:
        raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{nbits}!\n"
                          f"Suggestion: 0 <= x <= {hex(_upper[ nbits ])}" )
      return _new_valid_bits( nbits, self._uint ^ other )

  def __rxor__( self, other ):
    return self.__xor__( other )

  def __floordiv__( self, other ):
    nbits = self._nbits
    try:
      if other.nbits != nbits:
        raise ValueError( f"Operands of '//' (div) operation must have matching bitwidth, "\
                          f"but here Bits{nbits} != Bits{other.nbits}.\n" )
      return _new_valid_bits( nbits, (self._uint // other._uint) & _upper[nbits] )
    except AttributeError:
      other = int(other)
      if other < 0 or other > _upper[ self._nbits ]:
        raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{nbits}!\n"
                          f"Suggestion: 0 <= x <= {hex(_upper[ nbits ])}" )
      return _new_valid_bits( nbits, self._uint // other )

  def __rfloordiv__( self, other ):
    nbits = self._nbits
    other = int(other)
    up = _upper[ nbits ]
    if other < 0 or other > up:
      raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{nbits}!\n"
                        f"Suggestion: 0 <= x <= {hex(up)}" )
    return _new_valid_bits( nbits, other // self._uint )

  def __mod__( self, other ):
    nbits = self._nbits
    try:
      if other.nbits != nbits:
        raise ValueError( f"Operands of '%' (mod) operation must have matching bitwidth, "\
                          f"but here Bits{nbits} != Bits{other.nbits}.\n" )
      return _new_valid_bits( nbits, (self._uint % other._uint) & _upper[nbits] )
    except AttributeError:
      other = int(other)
      if other < 0 or other > _upper[ nbits ]:
        raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{nbits}!\n"
                          f"Suggestion: 0 <= x <= {hex(_upper[ nbits ])}" )
      return _new_valid_bits( nbits, self._uint % other )

  def __rmod__( self, other ):
    nbits = self._nbits
    other = int(other)
    up = _upper[ nbits ]
    if other < 0 or other > up:
      raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{nbits}!\n"
                        f"Suggestion: 0 <= x <= {hex(up)}" )
    return _new_valid_bits( nbits, other % self._uint )

  def __invert__( self ):
    nbits = self._nbits
    return _new_valid_bits( nbits, ~self._uint & _upper[nbits] )

  def __lshift__( self, other ):
    nbits = self._nbits
    try:
      if other.nbits != nbits:
        raise ValueError( f"Operands of '<<' (lshift) operation must have matching bitwidth, "\
                          f"but here Bits{nbits} != Bits{other.nbits}.\n" )
      uint = other._uint
      if uint >= nbits:
        return _new_valid_bits( self._nbits, 0 )
      return _new_valid_bits( nbits, (self._uint << uint) & _upper[nbits] )
    except AttributeError:
      other = int(other)
      if other < 0 or other > _upper[ nbits ]:
        raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{nbits}!\n"
                          f"Suggestion: 0 <= x <= {hex(_upper[ nbits ])}" )
      if other >= nbits:
        return _new_valid_bits( self._nbits, 0 )
      return _new_valid_bits( nbits, (self._uint << other) & _upper[nbits] )

  def __rshift__( self, other ):
    nbits = self._nbits
    try:
      if other.nbits != nbits:
        raise ValueError( f"Operands of '>>' (rshift) operation must have matching bitwidth, "\
                          f"but here Bits{nbits} != Bits{other.nbits}.\n" )
      return _new_valid_bits( nbits, self._uint >> other._uint )
    except AttributeError:
      other = int(other)
      if other < 0 or other > _upper[ nbits ]:
        raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{nbits}!\n"
                          f"Suggestion: 0 <= x <= {hex(_upper[ nbits ])}" )
      return _new_valid_bits( nbits, self._uint >> other )

  def __eq__( self, other ):
    nbits = self._nbits
    try:
      if other.nbits != nbits:
        raise ValueError( f"Operands of '==' (eq) operation must have matching bitwidth, "\
                          f"but here Bits{nbits} != Bits{other.nbits}.\n" )
      return _new_valid_bits( 1, self._uint == other._uint )
    except AttributeError:
      try:
        other = int(other)
      except:
        return _new_valid_bits( 1, 0 )

      if other < 0 or other > _upper[ nbits ]:
        raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{nbits}!\n"
                          f"Suggestion: 0 <= x <= {hex(_upper[ nbits ])}" )
      return _new_valid_bits( 1, self._uint == other )

  # No need for __ne__

  def __lt__( self, other ):
    nbits = self._nbits
    try:
      if other.nbits != nbits:
        raise ValueError( f"Operands of '<' (lt) operation must have matching bitwidth, "\
                          f"but here Bits{nbits} != Bits{other.nbits}.\n" )
      return _new_valid_bits( 1, self._uint < other._uint )
    except AttributeError:
      other = int(other)
      if other < 0 or other > _upper[ self._nbits ]:
        raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{self._nbits}!\n"
                          f"Suggestion: 0 <= x <= {hex(_upper[ self._nbits ])}" )
      return _new_valid_bits( 1, self._uint < other )

  def __le__( self, other ):
    nbits = self._nbits
    try:
      if other.nbits != nbits:
        raise ValueError( f"Operands of '<=' (le) operation must have matching bitwidth, "\
                          f"but here Bits{nbits} != Bits{other.nbits}.\n" )
      return _new_valid_bits( 1, self._uint <= other._uint )
    except AttributeError:
      other = int(other)
      if other < 0 or other > _upper[ self._nbits ]:
        raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{self._nbits}!\n"
                          f"Suggestion: 0 <= x <= {hex(_upper[ self._nbits ])}" )
      return _new_valid_bits( 1, self._uint <= other )

  def __gt__( self, other ):
    nbits = self._nbits
    try:
      if other.nbits != nbits:
        raise ValueError( f"Operands of '>' (gt) operation must have matching bitwidth, "\
                          f"but here Bits{nbits} != Bits{other.nbits}.\n" )
      return _new_valid_bits( 1, self._uint > other._uint )
    except AttributeError:
      other = int(other)
      if other < 0 or other > _upper[ self._nbits ]:
        raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{self._nbits}!\n"
                          f"Suggestion: 0 <= x <= {hex(_upper[ self._nbits ])}" )
      return _new_valid_bits( 1, self._uint > other )

  def __ge__( self, other ):
    nbits = self._nbits
    try:
      if other.nbits != nbits:
        raise ValueError( f"Operands of '>=' (ge) operation must have matching bitwidth, "\
                          f"but here Bits{nbits} != Bits{other.nbits}.\n" )
      return _new_valid_bits( 1, self._uint >= other._uint )
    except AttributeError:
      other = int(other)
      if other < 0 or other > _upper[ self._nbits ]:
        raise ValueError( f"Integer {hex(other)} is not a valid binop operand with Bits{self._nbits}!\n"
                          f"Suggestion: 0 <= x <= {hex(_upper[ self._nbits ])}" )
      return _new_valid_bits( 1, self._uint >= other )

  def __bool__( self ):
    return self._uint != 0

  def __int__( self ):
    return int(self._uint)

  def int( self ):
    if self._uint >> (self._nbits - 1):
      return -int(~self + 1)
    return self._uint

  def uint( self ):
    return self._uint

  def __index__( self ):
    return int(self._uint)

  def __hash__( self ):
    return hash((self._nbits, self._uint))

  # Print

  def __repr__(self):
    return "Bits{}(0x{})".format( self._nbits, "{:x}".format(int(self._uint)).zfill(((self._nbits-1)//4)+1) )

  def __str__(self):
    str = "{:x}".format(int(self._uint)).zfill(((self._nbits-1)//4)+1)
    return str

  def bin(self):
    str = "{:b}".format(int(self._uint)).zfill(self._nbits)
    return "0b"+str

  def oct( self ):
    str = "{:o}".format(int(self._uint)).zfill(((self._nbits-1)//3)+1)
    return "0o"+str

  def hex( self ):
    str = "{:x}".format(int(self._uint)).zfill(((self._nbits-1)//4)+1)
    return "0x"+str
