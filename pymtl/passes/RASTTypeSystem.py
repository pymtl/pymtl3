#========================================================================
# RASTTypeSystem.py
#========================================================================
# This file contains all RAST types in its type system.
#
# Author : Peitian Pan
# Date   : Jan 6, 2019

class BaseRASTType( object ):
  def __init__( s ):
    pass

class signal( BaseRASTType ):
  def __init__( s, nbits ):
    s.nbits = nbits

  def __eq__( s, other ):
    return s.nbits == other.nbits

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __repr__( s ):
    return 'signal'

class constant( BaseRASTType ):
  def __init__( s, nbits ):
    s.nbits = nbits

  def __eq__( s, other ):
    return s.nbits == other.nbits

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __repr__( s ):
    return 'constant'

class module( BaseRASTType ):
  def __init__( s, module ):
    s.module = module

  def __eq__( s, other ):
    # We will compare the type of module objects!
    return type(s.module) == type(other.module)

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __repr__( s ):
    return 'module'

class array( BaseRASTType ):
  def __init__( s, length, Type ):
    s.length = length
    s.Type = Type

  def __eq__( s, other ):
    if s.length == other.length and type( s.Type ) == type( other.Type ):
      if not isinstance( s.Type, array ):
        return s.Type == other.Type
      else:
        return s.Type.__eq__( other.Type )
    else:
      return False

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __repr__( s ):
    return 'array'

