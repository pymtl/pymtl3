#=========================================================================
# utility.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 13, 2019
"""Helper methods for RTLIR."""

def collect_objs( m, Type ):
  """Return a list of members of `m` that are of type `Type`."""

  def _is_of_type( obj, Type ):
    if isinstance(obj, Type):
      return True
    if isinstance(obj, list):
      return all( _is_of_type( x, Type ) for x in obj )
    return False

  ret = []
  for name, obj in vars(m).items():
    if isinstance( name, str ) and not name.startswith( '_' ):
      if _is_of_type( obj, Type ):
        ret.append( ( name, obj ) )
  return ret
