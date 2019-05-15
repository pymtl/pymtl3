#=========================================================================
# utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 13, 2019
"""Helper methods for RTLIR."""

import inspect, copy
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
  for name, obj in m.__dict__.iteritems():
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

def is_BitsX( obj ):
  """Return if `obj` is a BitsX class."""
  try:
    assert obj.__name__.startswith('Bits')
    n = int(obj.__name__[4:])
    return True
  except:
    return False
