#=========================================================================
# utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 13, 2019
"""Helper methods for RTLIR."""

from __future__ import absolute_import, division, print_function

from functools import reduce


def _is_of_type( obj, Type ):
  if isinstance(obj, Type):
    return True
  if isinstance(obj, list):
    return reduce( lambda x, y: x and _is_of_type( y, Type ), obj, True )
  return False

def _ungroup_list( obj ):
  assert isinstance( obj, list )
  ret = []
  for _obj in obj:
    if isinstance( _obj, list ):
      ret += ungroup_list( _obj )
    else:
      ret.append( ( _obj._dsl.my_name, _obj ) )
  return ret

def collect_objs( m, Type, grouped=False ):
  """Return a list of members of `m` that are of type `Type`."""
  ret = []
  for name, obj in vars(m).iteritems():
    if isinstance( name, basestring ) and not name.startswith( '_' ):
      if _is_of_type( obj, Type ):
        if isinstance( obj, list ) and not grouped:
          ret.extend( _ungroup_list( obj ) )
        else:
          ret.append( ( name, obj ) )
  return ret

def freeze( obj ):
  """Return immutable version of `obj`."""
  if isinstance( obj, list ):
    return tuple( freeze( o ) for o in obj )
  return obj
