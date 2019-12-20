"""
=========================================================================
TestCase.py
=========================================================================
Implement the base TestCase class.

Author : Peitian Pan
Date   : Dec 12, 2019
"""

from copy import copy
from textwrap import dedent


class AliasOf:
  def __init__( s, alias_name = 'A' ):
    s.alias_name = alias_name

  def __get__( s, instance, owner ):
    return getattr( owner, s.alias_name )

  def __set__( s, instance, value ):
    # Overwriting an existing alias is not supported yet
    raise NotImplementedError

def set_attributes( _cls, *args ):
  assert len( args ) % 2 == 0
  cls = copy( _cls )
  for attr, obj in zip( args[::2], args[1::2] ):
    setattr( cls, attr, dedent(obj) if isinstance(obj, str) else obj )
  return cls
