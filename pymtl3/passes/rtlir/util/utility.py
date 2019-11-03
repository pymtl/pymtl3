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
    if isinstance( name, str ) and name[0] != '_':
      if _is_of_type( obj, Type ):
        ret.append( ( name, obj ) )
  return ret

def get_component_full_name( c_rtype ):

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

def get_ordered_upblks( m ):
  """Return a list of non-update-ff update blocks that have deterministic order"""

  upblks = m.get_update_blocks() - m.get_update_ff()
  return [ x for x in m.get_update_block_order() if x in upblks ]

def get_ordered_update_ff( m ):
  """Return a list of update-ff update blocks that have deterministic order"""

  return [ x for x in m.get_update_block_order() if x in m.get_update_ff() ]
