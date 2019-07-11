#=========================================================================
# utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 13, 2019
"""Helper methods for RTLIR."""

from __future__ import absolute_import, division, print_function

from functools import reduce


def collect_objs( m, Type ):
  """Return a list of members of `m` that are of type `Type`."""

  def _is_of_type( obj, Type ):
    if isinstance(obj, Type):
      return True
    if isinstance(obj, list):
      return reduce( lambda x, y: x and _is_of_type( y, Type ), obj, True )
    return False

  ret = []
  for name, obj in vars(m).iteritems():
    if isinstance( name, basestring ) and not name.startswith( '_' ):
      if _is_of_type( obj, Type ):
        ret.append( ( name, obj ) )
  return ret
