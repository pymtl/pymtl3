#=========================================================================
# Helpers.py
#=========================================================================
# This file includes the helper functions that might be useful for
# translation or other passes.
#
# Author : Peitian Pan
# Date   : Feb 22, 2019

from pymtl.passes.rast import get_type

#-------------------------------------------------------------------------
# collect_ports
#-------------------------------------------------------------------------
# Return a list of members of `m` that are or include `Type` ports.

def collect_ports( m, Type ):

  def is_of_type( obj, Type ):
    """Is obj Type or contains Type?"""
    if isinstance( obj, Type ):
      return True
    if isinstance( obj, list ):
      return reduce( lambda x, y: x and is_of_type( y, Type ), obj, True )
    return False

  ret = []
  for name, obj in m.__dict__.iteritems():
    if isinstance( name, basestring ) and not name.startswith( '_' ):
      if is_of_type( obj, Type ):
        ret.append( ( name, obj ) )
  return ret

#-------------------------------------------------------------------------
# generate_signal_decl
#-------------------------------------------------------------------------
# Generate a string that conforms to SystemVerilog style signal
# declaration of `port`, and displays its name as `name`.

def generate_signal_decl( name, port ):

  type_str = get_type( port ).type_str()

  return '{dtype} {vec_size} {name} {dim_size}'.format(
    dtype = type_str[ 'dtype' ], vec_size = type_str[ 'vec_size' ],
    name = name,                 dim_size = type_str[ 'dim_size' ]
  )

#-------------------------------------------------------------------------
# get_model_parameters
#-------------------------------------------------------------------------

def get_model_parameters( model ):

  ret = {}

  kwargs = model._dsl.kwargs.copy()
  if "elaborate" in model._dsl.param_dict:
    kwargs.update(
      { x: y\
        for x, y in model._dsl.param_dict[ "elaborate" ].iteritems() if x 
    } )

  ret[ '' ] = model._dsl.args

  ret.update( kwargs )

  return ret

#-------------------------------------------------------------------------
# is_param_equal
#-------------------------------------------------------------------------

def is_param_equal( src, dst ):

  if len( src[''] ) != len( dst[''] ): return False
  if src.keys() != dst.keys(): return False

  for s, d in zip( src[''], dst[''] ):
    if s != d:
      return False

  for key in src.keys():
    if src[key] != dst[key]:
      return False

  return True
