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
from __future__ import absolute_import, division, print_function

import os

import py.code

# This __new__ approach has better performance
# bits_template = """
# class Bits{nbits}(object):
  # nbits = {nbits}
  # def __new__( cls, value = 0 ):
    # return Bits( {nbits}, value )

if os.getenv("PYMTL_BITS") == "1":
  from .PythonBits import Bits
  # print "[env: PYMTL_BITS=1] Use Python Bits"
  bits_template = """
class Bits{nbits}(Bits):
  nbits = {nbits}
  def __init__( s, value=0 ):
    return super( Bits{nbits}, s ).__init__( {nbits}, value )

_bits_types[{nbits}] = Bits{nbits}
b{nbits} = Bits{nbits}
"""
else:
  try:
    from mamba import Bits
    # print "[default w/  Mamba] Use Mamba Bits"
    bits_template = """
class Bits{nbits}(Bits):
  nbits = {nbits}
  def __new__( cls, value=0 ):
    return Bits.__new__( cls, {nbits}, value )

_bits_types[{nbits}] = Bits{nbits}
b{nbits} = Bits{nbits}
"""
  except ImportError:
    from .PythonBits import Bits
    # print "[default w/o Mamba] Use Python Bits"
    bits_template = """
class Bits{nbits}(Bits):
  nbits = {nbits}
  def __init__( s, value=0 ):
    return super( Bits{nbits}, s ).__init__( {nbits}, value )

_bits_types[{nbits}] = Bits{nbits}
b{nbits} = Bits{nbits}
"""

_bitwidths     = list(range(1, 256)) + [ 384, 512, 768, 1024, 1536, 2048, 4096 ]
_bits_types    = dict()

exec(py.code.Source( "".join([ bits_template.format( **vars() ) \
                        for nbits in _bitwidths ]) ).compile())

def mk_bits( nbits ):
  assert nbits < 16384, "We don't allow bitwidth to exceed 16384."
  if nbits in _bits_types:  return _bits_types[ nbits ]

  exec((py.code.Source( bits_template.format( **vars() ) ).compile()), globals())
  return _bits_types[ nbits ]
