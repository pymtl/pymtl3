import py.code, os

_use_pymtl_bits = ( os.getenv("PYMTL_BITS") == "1" ) or \
                 ( 'Bits' not in dir(__builtins__) )

if _use_pymtl_bits:
  from Bits import Bits
  print "Use python Bits"
else:
  print "Use builtin Bits"

bits_template = """
class Bits{nbits}(object):
  nbits = {nbits}
  def __new__( cls, value = 0 ):
    return Bits( {nbits}, value )

_bits_types[{nbits}] = Bits{nbits}
"""

_bitwidths     = range(1, 256) + [ 384, 512, 768, 1024, 1536, 2048, 4096 ]
_bits_types    = dict()

exec py.code.Source( "".join([ bits_template.format( **vars() ) \
                        for nbits in _bitwidths ]) ).compile()

def mk_bits( nbits ):
  assert nbits < 16384, "We don't allow bitwidth to exceed 16384."
  if nbits in _bits_types:  return _bits_types[ nbits ]

  exec py.code.Source( bits_template.format( **vars() ) ).compile()
  return _bits_types[ nbits ]
