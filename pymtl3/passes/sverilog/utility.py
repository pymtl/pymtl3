#=========================================================================
# utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 27, 2019
"""Provide helper methods that might be useful to sverilog passes."""

from __future__ import absolute_import, division, print_function


def make_indent( src, nindent ):
  """Add nindent indention to every line in src."""
  indent = '  '
  for idx, s in enumerate( src ):
    src[ idx ] = nindent * indent + s

def get_component_unique_name( c_rtype ):

  def get_string( obj ):
    """Return the string that identifies `obj`"""
    if isinstance(obj, type): return obj.__name__
    return str( obj )

  comp_name = c_rtype.get_name()
  comp_params = c_rtype.get_params()
  assert comp_name
  for arg_name, arg_value in comp_params:
    assert arg_name != ''
    comp_name += '__' + arg_name + '_' + get_string(arg_value)
  return comp_name
