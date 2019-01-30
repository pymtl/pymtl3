#=======================================================================
# RASTType.py
#=======================================================================
# This file contains all RAST types in its type system.
#
# Author : Peitian Pan
# Date   : Jan 6, 2019

#-----------------------------------------------------------------------
# Base RAST Type
#-----------------------------------------------------------------------

class BaseRASTType( object ):
  def __init__( s ):
    pass

#-----------------------------------------------------------------------
# Signal Type
#-----------------------------------------------------------------------

# Signal expressions are used for slicing, index, attribute, etc.
class Signal( BaseRASTType ):
  def __init__( s, nbits ):
    super( Signal, s ).__init__()
    s.nbits = nbits

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

#-----------------------------------------------------------------------
# Array Type
#-----------------------------------------------------------------------

# Array expressions are used in the assignment to an unpacked array
# A packed array should have signal_expr type
class Array( BaseRASTType ):
  def __init__( s, length, Type ):
    super( Array, s ).__init__()
    s.length = length
    s.Type = Type

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

#-----------------------------------------------------------------------
# Const Type
#-----------------------------------------------------------------------

# Constant expressions, used as slicing upper/lower bounds, index
class Const( BaseRASTType ):
  def __init__( s, is_static, nbits, value = None ):
    # is_static == False <=> value == None
    s.is_static = is_static
    s.nbits = nbits
    s.value = value

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

#-----------------------------------------------------------------------
# Bool Type
#-----------------------------------------------------------------------

class Bool( BaseRASTType ):
  def __init__( s ):
    pass

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

#-----------------------------------------------------------------------
# Module Type
#-----------------------------------------------------------------------

# This is the type of the base of all the attributes. It looks weird 
# in the current type system but makes more sense once we've added struct
# to the system.
class Module( BaseRASTType ):
  def __init__( s, module ):
    s.module = module

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
