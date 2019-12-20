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

def add_attributes( _cls, *args ):
  assert len( args ) % 2 == 0
  cls = copy( _cls )
  for attr, obj in zip( args[::2], args[1::2] ):
    setattr( cls, attr, dedent(obj) if isinstance(obj, str) else obj )
  return cls

#-------------------------------------------------------------------------
# Helper functions that create tv_in and tv_out
#-------------------------------------------------------------------------

# args: [attr, Bits, idx]
def _set( *args ):
  local_dict = {}
  assert len(args) % 3 == 0
  _tv_in_str = 'def tv_in( m, tv ):  \n'
  if len(args) == 0:
    _tv_in_str += '  pass'
  for attr, Bits, idx in zip( args[0::3], args[1::3], args[2::3] ):
    _tv_in_str += f'  m.{attr} = {Bits.__name__}( tv[{idx}] )\n'
  exec( _tv_in_str, globals(), local_dict )
  return local_dict['tv_in']

# args: [attr, Bits, idx]
def _check( *args ):
  local_dict = {}
  assert len(args) % 3 == 0
  _tv_out_str = 'def tv_out( m, tv ):  \n'
  if len(args) == 0:
    _tv_out_str += '  pass'
  for attr, Bits, idx in zip( args[0::3], args[1::3], args[2::3] ):
    if isinstance(Bits, str):
      _tv_out_str += f'  assert m.{attr} == {Bits}( tv[{idx}] )\n'
    else:
      _tv_out_str += f'  assert m.{attr} == {Bits.__name__}( tv[{idx}] )\n'
  exec( _tv_out_str, globals(), local_dict )
  return local_dict['tv_out']
