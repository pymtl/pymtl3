#=========================================================================
# RASTType.py
#=========================================================================
# This file contains all RAST types in its type system.
#
# Author : Peitian Pan
# Date   : Jan 6, 2019

import inspect

from pymtl import *

#-------------------------------------------------------------------------
# Base RAST Type
#-------------------------------------------------------------------------

class BaseRASTType( object ):
  def __init__( s ):
    pass

#-------------------------------------------------------------------------
# Signal Type
#-------------------------------------------------------------------------
# Signal expressions are used for slicing, index, attribute, etc.

class Signal( BaseRASTType ):
  def __init__( s, nbits ):
    super( Signal, s ).__init__()
    s.nbits = nbits

  def type_str( s ):
    ret = {
        'dtype' : 'logic', 'vec_size' : '[{}:{}]'.format( s.nbits-1, 0 ),
        'dim_size' : ''
    }
    return ret

  def __eq__( s, other ):
    if type( s ) != type( other ):
      return False
    return s.nbits == other.nbits

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    """Can obj be cast into RASTType.Signal?"""
    if isinstance( obj, Signal ) and s == obj:
      return True
    if isinstance( obj, Const ) and s.nbits == obj.nbits:
      return True
    return False

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
    ret = {
    }
    sub_type_str = s.Type.type_str()
    ret[ 'dtype' ] = sub_type_str[ 'dtype' ]
    ret[ 'dim_size' ] =\
      '[{}:{}]'.format( 0, s.length-1 ) + sub_type_str[ 'dim_size' ]
    ret[ 'vec_size' ] = sub_type_str[ 'vec_size' ]

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
    """Can obj be cast into RASTType.Array?"""
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
    ret = {}
    ret[ 'dtype' ] = 'parameter int'
    if not s.value is None:
      ret[ 'value' ] = str( s.value )
    return ret

  def __eq__( s, other ):
    if type( s ) != type( other ):
      return False
    return ( s.is_static and other.is_static ) and ( s.nbits == other.nbits )

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    """Can obj be cast into RASTType.Const?"""
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
    """Can obj be cast into RASTType.Bool?"""
    if isinstance( obj, ( Bool, Signal, Const ) ):
      return True
    return False

  def __repr__( s ):
    return 'Bool'

#-------------------------------------------------------------------------
# Module Type
#-------------------------------------------------------------------------
# This is the type of the base of all the attributes. It looks weird 
# in the current type system but makes more sense once we've added struct
# to the system.

class Module( BaseRASTType ):
  def __init__( s, module ):
    s.module = module

  def type_str( s ):
    return {}

  def __eq__( s, other ):
    if type( s ) != type( other ):
      return False
    # We will compare the type of module objects!
    return type(s.module) == type(other.module)

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    """Can obj be cast into RASTType.Module?"""
    if isinstance( obj, Module ) and s == obj:
      return True
    return False

  def __repr__( s ):
    return 'Module'

#-------------------------------------------------------------------------
# PythonClass Type
#-------------------------------------------------------------------------

class PythonClass( BaseRASTType ):
  def __init__( s, obj ):
    s.obj = obj

  def type_str( s ):
    return {}

  def __eq__( s, other ):
    if type( s ) != type( other ):
      return False
    return s is other

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    """Can obj be cast into RASTType.PythonClass?"""
    if isinstance( obj, PythonClass ) and s is obj:
      return True
    return False

  def __repr__( s ):
    return 'PythonClass'

#-------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------

def get_type( obj ):
  """return the RAST type of obj"""

  # child component of the given module
  if isinstance( obj, RTLComponent ):
    return Module( obj )

  # signals refer to in/out ports and wires
  elif isinstance( obj, ( InVPort, OutVPort, Wire ) ):
    try:
      nbits = obj._dsl.Type.nbits

    except AttributeError:
      assert False, 'signal instance' + str(obj) + \
         ' must have Bits as their .Type field'

    return Signal( nbits )

  # integers have unset bitwidth (0) 
  elif isinstance( obj, int ):
    return Const( True, 0, obj )

  # Bits instances
  elif isinstance( obj, Bits ):
    return Const( True, obj.nbits, obj.value )

  # array type
  elif isinstance( obj, list ):
    assert len( obj ) > 0

    type_list = map( lambda x: get_type( x ), obj )

    assert reduce(lambda x, y: x and (y == type_list[0]), type_list, True),\
      'Elements of list ' + str(obj) + ' must have the same RAST type!'

    return Array( len( obj ), type_list[0] )

  # python class
  elif inspect.isclass( obj ):
    return PythonClass( obj )

  assert False, 'unsupported objet ' + str(obj) + '!'
