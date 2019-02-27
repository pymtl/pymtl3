#=========================================================================
# Helpers.py
#=========================================================================
# This file includes the helper functions that might be useful for
# translation or other passes.
#
# Author : Peitian Pan
# Date   : Feb 22, 2019

from pymtl.passes.rast          import get_type
from pymtl.passes.Helpers       import make_indent
from pymtl.passes.rast.RASTType import Struct

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

  name = get_verilog_name( name )

  # TODO: support struct signals

  type_str = get_type( port ).type_str()

  return '{dtype} {vec_size} {name} {dim_size}'.format(
    dtype = type_str[ 'dtype' ], vec_size = type_str[ 'vec_size' ],
    name = name,                 dim_size = type_str[ 'dim_size' ]
  )

#-------------------------------------------------------------------------
# generate_struct_defs
#-------------------------------------------------------------------------

def generate_struct_defs( type_env ):

  ret = ''

  # Generate struct dependency DAG
  
  dag = {}
  in_degree = {}

  for obj, Type in type_env.iteritems():
    if isinstance( Type, Struct ):
      if not (obj, Type) in dag:
        dag[ (obj, Type) ] = []
      if not (obj, Type) in in_degree:
        in_degree[ (obj, Type) ] = 0

      _env = Type.type_env
      for _obj, _Type in _env.iteritems():
        if isinstance( _Type, Struct ):
          if not (_obj, _Type) in dag:
            dag[ (_obj, _Type) ] = []
          if not (obj, Type) in in_degree:
            in_degree[ (obj, Type) ] = 0

          dag[ (_obj, _Type) ].append( (obj, Type) )
          in_degree[ (obj, Type) ] += 1

  # Topo sort on dag

  q = []
  visited = {}

  for vertex, ind in in_degree.iteritems():
    if ind == 0:
      q.append( vertex )

  while q:
    vertex = q.pop()

    ret += generate_struct_def( vertex[0], vertex[1] )

    visited[ vertex ] = True

    for _vertex in dag[ vertex ]:
      in_degree[ _vertex ] -= 1
      if in_degree[ _vertex ] == 0:
        q.append( _vertex )

  assert len( visited.keys() ) == len( dag.keys() )

  return ret

#-------------------------------------------------------------------------
# generate_struct_def
#-------------------------------------------------------------------------
# Generate the definition for a single struct object

def generate_struct_def( obj, Type ):

  type_str = Type.type_str()

  tplt = """typedef struct packed {{
{defs} 
}} {name};
"""

  defs = []

  # generate declarations for each field in the struct
  for _obj, _Type in Type.type_env.iteritems():
    defs.append(
      generate_signal_decl( get_verilog_name( _obj._dsl.my_name ),
        _obj ) + ';'
    )
    pass

  make_indent( defs, 1 )

  return tplt.format(
    defs = '\n'.join( defs ), name = type_str[ 'dtype' ]
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

#-------------------------------------------------------------------------
# get_verilog_name
#-------------------------------------------------------------------------

def get_verilog_name( name ):
  return name.replace( '[', '__' ).replace( ']', '__' )
