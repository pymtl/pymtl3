"""
========================================================================
bits_import.py
========================================================================
Import RPython Bits from PyPy mamba module if the environment variable
that forces the use of Python Bits is set, and there is actually an
importable Bits in mamba module. Otherwise import the Pure-Python
implementation in Bits.py. Then generate a bunch of fixed-width BitsN
types for PyMTL use.

Author : Shunning Jiang
Date   : Aug 23, 2018
"""
import os

# This __new__ approach has better performance
# bits_template = """
# class Bits{nbits}:
  # nbits = {nbits}
  # def __new__( cls, value = 0 ):
    # return Bits( {nbits}, value )

if os.getenv("PYMTL_BITS") == "1":
  from .PythonBits import Bits
  # print "[env: PYMTL_BITS=1] Use Python Bits"
  bits_template = """
class Bits{0}(Bits):
  nbits = {0}
  def __init__( s, value=0 ):
    return super().__init__( {0}, value )
_bits_types[{nbits}] = b{nbits} = Bits{nbits}
"""
else:
  try:
    from mamba import Bits
    # print "[default w/  Mamba] Use Mamba Bits"
    bits_template = """
class Bits{0}(Bits):
  nbits = {0}
  def __new__( cls, value=0 ):
    return Bits.__new__( cls, {0}, value )
_bits_types[{0}] = b{0} = Bits{0}
"""
  except ImportError:
    from .PythonBits import Bits
    # print "[default w/o Mamba] Use Python Bits"
    bits_template = """
class Bits{0}(Bits):
  nbits = {0}
  def __init__( s, value=0 ):
    return super().__init__( {0}, value )
_bits_types[{0}] = b{0} = Bits{0}
"""

_bitwidths  = list(range(1, 256)) + [ 384, 512 ]
_bits_types = dict()

exec(compile( "".join([ bits_template.format(nbits) for nbits in _bitwidths ]),
              filename="bits_import.py", mode="exec") )

def mk_bits( nbits ):
  assert nbits < 512, "We don't allow bitwidth to exceed 512."
  if nbits not in _bits_types:
    exec(compile( bits_template.format(nbits), filename=f"Bits{nbits}", mode="exec" ))
  return _bits_types[nbits]
