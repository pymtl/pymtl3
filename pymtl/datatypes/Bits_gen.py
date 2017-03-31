import py.code

class Bits1( object ):
  nbits = 1

  def __init__( self, value = 0 ):
    self.value = value & 1

  def __call__( self ):
    return self.__class__( 0 )

  # Arithmetics
  def __getitem__( self, idx ):
    if isinstance( idx, slice ):
      start, stop = int(idx.start), int(idx.stop)
      assert not idx.step and start < stop
      #FIXME
      return _bits_types[stop-start]( (self.value & ((1 << stop) - 1)) >> start )

    i = int(idx)
    assert 0 <= i < self.nbits
    return Bits1( (self.value >> i) & 1 )

  def __setitem__( self, idx, v ):
    if isinstance( idx, slice ):
      start, stop = int(idx.start), int(idx.stop)
      assert not idx.step and start < stop

      self.value = (int(self.value) & (~((1 << stop) - (1 << start)))) | ((int(v) & ((1 << stop) - 1)) << start) 
      return

    i = int(idx)
    assert 0 <= i < self.nbits
    self.value = (int(self.value) & ~(1 << i)) | ((int(v) & 1) << i)

  def __add__( self, other ):
    return self.__class__( self.value + int(other) )
  
  def __radd__( self, other ):
    return self.__add__( other )

  def __sub__( self, other ):
    return self.__class__( self.value - int(other) )

  def __and__( self, other ):
    return self.__class__( self.value & int(other) )

  def __rand__( self, other ):
    return self.__and__( other )

  def __or__( self, other ):
    return self.__class__( self.value | int(other) )

  def __ror__( self, other ):
    return self.__or__( other )

  def __xor__( self, other ):
    return self.__class__( self.value ^ int(other) )

  def __rxor__( self, other ):
    return self.__xor__( other )

  def __invert__( self ):
    return self.__class__( ~self.value )

  def __lshift__( self, other ):
    # TODO this doesn't work perfectly. We need a really smart
    # optimization that avoids the guard totally
    if int(other) >= self.nbits: return self.__class__( 0 )
    return self.__class__( self.value << int(other) )

  def __rshift__( self, other ):
    return self.__class__( self.value >> int(other) )

  def __eq__( self, other ):
    return Bits1( self.value == int(other) )

  def __ne__( self, other ):
    return Bits1( self.value != int(other) )

  def __lt__( self, other ):
    return Bits1( self.value < int(other) )

  def __le__( self, other ):
    return Bits1( self.value <= int(other) )

  def __gt__( self, other ):
    return Bits1( self.value > int(other) )

  def __ge__( self, other ):
    return Bits1( self.value >= int(other) )

  def __nonzero__( self ):
    return int(self.value) != 0

  def __int__( self ):
    return self.value

  def __index__( self ):
    return self.value

  # Print

  def __repr__(self):
    return "Bits{}( {} )".format( self.nbits, self.hex() )

  def __str__(self):
    str = "{:x}".format(self.value).zfill(((self.nbits-1)>>2)+1)
    return str

  def __oct__( self ):
    print "DEPRECATED: Please use .oct()!"
    return self.oct()

  def __hex__( self ):
    print "DEPRECATED: Please use .hex()!"
    return self.hex()

  def bin(self):
    str = "{:b}".format(self.value).zfill(self.nbits)
    return "0b"+str

  def oct( self ):
    str = "{:o}".format(self.value).zfill(((self.nbits-1)>>1)+1)
    return "0o"+str

  def hex( self ):
    str = "{:x}".format(self.value).zfill(((self.nbits-1)>>2)+1)
    return "0x"+str
    
bits_template = """
class Bits{nbits}(Bits1):
  nbits = {nbits}

  def __init__( self, value = 0 ):
    self.value = value & {mask}

_bits_types[{nbits}] = Bits{nbits}
"""

_bitwidths     = range(2, 192) + [ 384, 512, 768, 1024 ]
_bits_types    = dict()

source_str = ""
for nbits in _bitwidths: 
  mask = (1 << nbits) - 1
  source_str += bits_template.format( **vars() )
exec py.code.Source( source_str ).compile()

_bits_types[1] = Bits1
_bitwidths = [1] + _bitwidths

def mk_bits( nbits ):
  if nbits in _bits_types:  return _bits_types[ nbits ]

  mask = (1 << nbits) - 1
  exec py.code.Source( bits_template.format( **vars() ) ).compile()
  return _bits_types[ nbits ]
