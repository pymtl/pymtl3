#=========================================================================
# RASTType.py
#=========================================================================
# This file contains all RAST types in its type system.
#
# Author : Peitian Pan
# Date   : Jan 6, 2019

import inspect

from pymtl                import *
from pymtl.passes.Helpers import freeze, is_obj_eq

#-------------------------------------------------------------------------
# Base RAST Type
#-------------------------------------------------------------------------

class BaseRASTType( object ):
  def __new__( cls, *args, **kwargs ):
    return super( BaseRASTType, cls ).__new__( cls )

  def __init__( s ):
    super( BaseRASTType, s ).__init__()

#-------------------------------------------------------------------------
# NoneType
#-------------------------------------------------------------------------
# This type is used when a TmpVar node is visited before getting its type
# from an assignment

class NoneType( BaseRASTType ):
  def __init__( s ):
    super( NoneType, s ).__init__()

  def type_str( s ):
    ret = {}
    return ret

  def __eq__( s, other ):
    if type( s ) == type( other ):
      return True
    return False

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    """Can obj be cast into type `s`?"""
    if isinstance( obj, NoneType ):
      return True
    return False

  def __repr__( s ):
    return 'NoneType'

#-------------------------------------------------------------------------
# Signal Type
#-------------------------------------------------------------------------
# Signal expressions are used for slicing, index, attribute, etc.

class Signal( BaseRASTType ):
  def __init__( s, nbits, py_type = 'Wire' ):
    super( Signal, s ).__init__()
    s.nbits = nbits
    s.py_type = py_type

  def type_str( s ):
    ret = {
        'dtype'      : 'logic',
        'py_type'    : s.py_type,
        'vec_size'   : '[{}:{}]'.format( s.nbits-1, 0 ),
        'nbits'      : s.nbits,
        'total_bits' : s.nbits,
        'dim_size'   : '',
        'c_dim_size' : '',
        'n_dim_size' : [],
    }
    return ret

  def __eq__( s, other ):
    if type( s ) != type( other ):
      return False
    return s.nbits == other.nbits

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    """Can obj be cast into type `s`?"""
    if isinstance( obj, Signal ) and s == obj:
      return True
    if isinstance( obj, Const ) and s.nbits == obj.nbits:
      return True
    return False

  @staticmethod
  def cast( obj ):
    """Cast `obj` into Signal object or NoneType() if failed"""
    if isinstance( obj, Signal ):
      return obj

    if isinstance( obj, Const ):
      return Signal( obj.nbits )

    return NoneType()

  def __repr__( s ):
    return 'Signal'

#-------------------------------------------------------------------------
# Array Type
#-------------------------------------------------------------------------
# Packed array type. We assume all Python list translates to packed
# array because only packed structs are synthesizable.

class Array( BaseRASTType ):
  def __init__( s, length, Type ):
    super( Array, s ).__init__()
    s.length = length
    s.Type = Type

  def type_str( s ):
    sub_type_str = s.Type.type_str()
    ret = {
      'dtype'      : sub_type_str[ 'dtype' ],
      'py_type'    : sub_type_str[ 'py_type' ],
      'vec_size'   : sub_type_str[ 'vec_size' ],
      'nbits'      : sub_type_str[ 'nbits' ],
      'total_bits' : 0,
      'dim_size'   : \
        '[{}:{}]'.format( 0, s.length-1 ) + sub_type_str[ 'dim_size' ],
      'c_dim_size' : '[{}]'.format( s.length ) + sub_type_str[ 'c_dim_size' ],
      'n_dim_size' : [ s.length ] + sub_type_str[ 'n_dim_size' ]
    }

    total_vec_num = reduce( lambda x,y: x*y, ret['n_dim_size'], 1 )

    ret[ 'total_bits' ] = total_vec_num * ret[ 'nbits' ]

    return ret

  def __eq__( s, other ):
    if type( s ) != type( other ):
      return False
    if s.length == other.length and type( s.Type ) == type( other.Type ):
      if not isinstance( s.Type, Array ):
        return s.Type == other.Type
      else:
        return s.Type.__eq__( other.Type )
    else:
      return False

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    """Can obj be cast into type `s`?"""
    if isinstance( obj, Array ) and s.Type == obj.Type:
      return True
    return False

  def __repr__( s ):
    return 'Array'

#-------------------------------------------------------------------------
# Const Type
#-------------------------------------------------------------------------
# Constant expressions, used as slicing upper/lower bounds, index

class Const( BaseRASTType ):
  def __init__( s, is_static, nbits, value = None ):
    # is_static == False <=> value == None
    s.is_static = is_static
    s.nbits = nbits
    s.value = value

  def type_str( s ):
    assert not s.value is None, "Trying to declare a constant but did not\
 provide initial value!"

    ret = {
        'dtype'      : 'const logic',
        'py_type'    : 'Bits' + str(s.nbits),
        'vec_size'   : '[{}:{}]'.format( s.nbits-1, 0 ),
        'value'      : str(s.value),
        'nbits'      : s.nbits,
        'total_bits' : s.nbits,
        'dim_size'   : '',
        'c_dim_size' : '',
        'n_dim_size' : [],
    }

    return ret

  def __eq__( s, other ):
    if type( s ) != type( other ):
      return False
    return ( s.is_static and other.is_static ) and ( s.nbits == other.nbits )

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    """Can obj be cast into type `s`?"""
    if isinstance( obj, Const ) and s == obj:
      return True
    return False

  def __repr__( s ):
    return 'Const'

#-------------------------------------------------------------------------
# Bool Type
#-------------------------------------------------------------------------

class Bool( BaseRASTType ):
  def __init__( s ):
    pass

  def type_str( s ):
    return {}

  def __eq__( s, other ):
    if type( s ) != type( other ):
      return False
    return True

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    """Can obj be cast into type `s`?"""
    if isinstance( obj, ( Bool, Signal, Const ) ):
      return True
    return False

  def __repr__( s ):
    return 'Bool'

#-------------------------------------------------------------------------
# BaseAttr Type
#-------------------------------------------------------------------------
# This is the base type for all types that can serve as the base of an
# attribute operation.

class BaseAttr( BaseRASTType ):
  def __init__( s, obj, type_env ):
    super( BaseAttr, s ).__init__()
    s.obj = obj
    s.type_env = type_env

  def type_str( s ):
    raise NotImplementedError

  def __eq__( s, other ):
    return is_obj_eq( s.type_env, other.type_env )

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    raise NotImplementedError

  def __repr__( s ):
    raise NotImplementedError

#-------------------------------------------------------------------------
# Module Type
#-------------------------------------------------------------------------
# Any variable that refers to a module has this type.

class Module( BaseAttr ):
  def __init__( s, obj, type_env ):
    super( Module, s ).__init__( obj, type_env )

  def type_str( s ):
    ret = {
      'dtype'      : s.obj.__class__.__name__,
      'py_type'    : s.obj.__class__.__name__,
      'vec_size'   : '',
      'nbits'      : 0,
      'total_bits' : 0,
      'dim_size'   : '',
      'c_dim_size' : '',
      'n_dim_size' : []
    }

    return ret

  def __call__( s, obj ):
    """Can obj be cast into type `s`?"""
    if isinstance( obj, Module ) and s == obj:
      return True
    return False

  def __repr__( s ):
    return 'Module'

#-------------------------------------------------------------------------
# Struct
#-------------------------------------------------------------------------
# This is the type for packed struct in SystemVerilog

class Struct( BaseAttr ):
  def __init__( s, obj, type_env, pack_order ):
    super( Struct, s ).__init__( obj, type_env )
    s.pack_order = pack_order

  def type_str( s ):
    ret = {
      'dtype'      : s.obj._dsl.Type.__class__.__name__,
      'py_type'    : s.obj.__class__.__name__, # packed struct -> port/wire
      'vec_size'   : '',
      'nbits'      : 0,
      'total_bits' : 0,
      'dim_size'   : '',
      'c_dim_size' : '',
      'n_dim_size' : []
    }

    total_bits = 0

    for obj, Type in s.type_env.iteritems():
      type_str = Type.type_str()
      total_bits += type_str[ 'total_bits' ]

    ret['nbits'] = ret['total_bits'] = total_bits

    return ret

  def __eq__( s, u ):
    return super( Struct, s ).__eq__( u ) and \
           is_obj_eq( s.pack_order, u.pack_order )

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    """Can obj be cast into type `s`?"""
    if isinstance( obj, Struct ) and s is obj:
      return True
    return False

  def __repr__( s ):
    return 'Struct'

#-------------------------------------------------------------------------
# Interface
#-------------------------------------------------------------------------

class Interface( BaseAttr ):
  def __init__( s, obj, type_env ):
    super( Interface, s ).__init__( obj, type_env )

  def type_str( s ):
    return {}

  def __call__( s, obj ):
    """Can obj be cast into type `s`?"""
    if isinstance( obj, Interface ) and s is obj:
      return True
    return False

  def __repr__( s ):
    return 'Interface'

#-------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------

#-------------------------------------------------------------------------
# get_type
#-------------------------------------------------------------------------

def get_type( obj ):
  """return the RAST type of obj"""

  # child component of the given module
  if isinstance( obj, RTLComponent ):

    type_env = {}

    get_type_attributes( obj, type_env )

    return Module( obj, type_env )

  # Signals might be parameterized with different types
  elif isinstance( obj, ( InVPort, OutVPort, Wire ) ):
    
    # BitsX
    if is_BitsX( obj._dsl.Type ):
      nbits = obj._dsl.Type.nbits
      return Signal( nbits, obj.__class__.__name__ )

    # Struct
    type_env = {}

    get_type_attributes( obj, type_env )

    pack_order = []
    if '_pack_order' in obj._dsl.Type.__dict__:
      for field_name in obj._dsl.Type._pack_order:

        assert field_name in obj._dsl.Type.__dict__, 'Given field name is not an\
 attribute of struct ' + obj._dsl.Type.__class__.__name__ + '!'

        _obj = obj.__dict__[ field_name ]
        _Type = type_env[ _obj ]
        pack_order.append( (_obj, _Type) )

    else:
      key_order = sorted( type_env.keys(), key = repr )

      for key in key_order:
        pack_order.append( (key, type_env[ key ]) )

    # Make sure total_bits is calculated correctly
    ret = Struct( obj, type_env, pack_order )
    ret.type_str()

    return ret

  # integers have unset bitwidth (0) 
  elif isinstance( obj, int ):
    return Const( True, 0, obj )

  # Bits instances
  elif isinstance( obj, Bits ):
    return Const( True, obj.nbits, obj.value )

  # array type
  elif isinstance( obj, list ):
    assert len( obj ) > 0

    type_env = {}

    type_list = map( lambda x: get_type( x ), obj )

    assert reduce(lambda x, y: x and (y == type_list[0]), type_list, True),\
      'Elements of list ' + str(obj) + ' must have the same RAST type!'

    for _obj, _Type in zip( obj, type_list ):
      type_env[ _obj ] = _Type

    ret = Array( len( obj ), type_list[0] )
    ret.type_env = type_env

    return ret

  elif inspect.isclass( obj ):

    # BitsX
    if is_BitsX( obj ):
      nbits = obj.nbits
      return Signal( nbits )

    # Interface
    # TODO: translation support for interfaces
    if isinstance( obj, Interface ):
      type_env = {}
      
      get_type_attributes( obj, type_env )

      return Interface( obj, type_env )

  assert False, 'unsupported objet ' + str(obj) + '!'

#-------------------------------------------------------------------------
# is_BitsX
#-------------------------------------------------------------------------

def is_BitsX( obj ):
  """Is obj a BitsX class?"""

  try:
    if obj.__name__.startswith( 'Bits' ):
      try:
        n = int( obj.__name__[4:] )
        return True
      except:
        return False
  except:
    return False

  return False

#-------------------------------------------------------------------------
# get_type_attributes
#-------------------------------------------------------------------------

def get_type_attributes( obj, type_env ):

  obj_lst = [ _o for (name, _o) in obj.__dict__.iteritems()\
    if isinstance( name, basestring ) if not name.startswith( '_' )
  ]

  while obj_lst:
    o = obj_lst.pop()

    Type = get_type( o )
    type_env[ freeze( o ) ] = Type

    # Make sure total_bits of struct is calculated correctly
    Type.type_str()

    try:
      type_env.update( Type.type_env )
    except:
      pass
