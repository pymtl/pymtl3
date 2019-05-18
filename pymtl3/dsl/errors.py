"""
========================================================================
errors.py
========================================================================
Errors thrown by other files in this folder.

Author : Shunning Jiang
Date   : Dec 27, 2018
"""
from __future__ import absolute_import, division, print_function

import inspect


class SignalTypeError( Exception ):
  """ Raise when a declared signal is of wrong type """

class MultiWriterError( Exception ):
  """ Raise when a variable is written by multiple update blocks/nets """

class NoWriterError( Exception ):
  """ Raise when a net has no writer (driver) """
  def __init__( self, nets ):
    return super( NoWriterError, self ).__init__( \
    "The following nets need drivers.\nNet:\n - {} ".format(
      "\nNet:\n - ".join( [ "\n - ".join( [ repr(x) for x in y ] )
                            for y in nets ]) ) )

class NotElaboratedError( Exception ):
  """ Raise when processing a model that hasn't been elaborated yet """
  def __init__( self ):
    return super( NotElaboratedError, self ).__init__( \
    "Please elaborate the model first." )

class VarNotDeclaredError( Exception ):
  """ Raise when a variable in an update block is not declared """
  def __init__( self, obj, field, blk=None, blk_hostobj=None, lineno=0 ):
    self.obj    = obj
    self.field  = field
    self.blk    = blk

    if not self.blk:
      return super( VarNotDeclaredError, self ).__init__() # this is just temporary message

    filepath = inspect.getfile( blk_hostobj.__class__ )
    blk_src, base_lineno  = inspect.getsourcelines( blk )

    # Shunning: we need to subtract 1 from inspect's lineno when we add it
    # to base_lineno because it starts from 1!
    lineno -= 1
    error_lineno = base_lineno + lineno

    return super( VarNotDeclaredError, self ).__init__( \
"""
In file {}:{} in {}
When constructing instance {} of class \"{}\" in the hierarchy:

{} {}
^^^ Block \"{}\" tries to access field \"{}\" of object \"{}\" (class \"{}\"),
    but {} does not have field \"{}\".

Suggestion: fix incorrect field access at line {}, or fix the declaration somewhere.""".format( \
      filepath, error_lineno, blk.__name__,
      repr(blk_hostobj), blk_hostobj.__class__.__name__,
      error_lineno, blk_src[ lineno ].lstrip(''),
      blk.__name__, field, repr(obj), obj.__class__.__name__,
      repr(obj), field, error_lineno ) )

class UpblkFuncSameNameError( Exception ):
  """ Raise when two update block/function are declared with the same name """
  def __init__( self, name ):
    return super( UpblkFuncSameNameError, self ).__init__( \
      " Cannot declare two update blocks/functions with the same name {}".format( name ) )

class UpblkCyclicError( Exception ):
  """ Raise when update blocks have cyclic dependencies """

class InvalidConstraintError( Exception ):
  """ Raise when a defined constraint is of wrong format """
  def __init__( self ):
    return super( InvalidConstraintError, self ).__init__( \
      "Constraints between two variables are not allowed!" )

class InvalidConnectionError( Exception ):
  """ Raise upon an inappropriate attempt to connect two variables """

class InvalidFuncCallError( Exception ):
  """ Raise upon an inappropriate @s.func function call """
