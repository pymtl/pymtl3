"""
========================================================================
errors.py
========================================================================
Errors thrown by other files in this folder.

Author : Shunning Jiang
Date   : Dec 27, 2018
"""
import inspect


class SignalTypeError( Exception ):
  """ Raise when a declared signal is of wrong type """

class MultiWriterError( Exception ):
  """ Raise when a variable is written by multiple update blocks/nets """

class NoWriterError( Exception ):
  """ Raise when a net has no writer (driver) """
  def __init__( self, nets ):
    return super().__init__( \
    "The following nets need drivers.\nNet:\n - {} ".format(
      "\nNet:\n - ".join( [ "\n - ".join( [ repr(x) for x in y ] )
                            for y in nets ]) ) )

class InvalidFFAssignError( Exception ):
  """ In update_ff, raise when signal is not <<= -ed, or temp is not = -ed """
  def __init__( self, hostobj, blk, lineno, suggestion ):

    filepath = inspect.getfile( hostobj.__class__ )
    blk_src, base_lineno  = inspect.getsourcelines( blk )

    # Shunning: we need to subtract 1 from inspect's lineno when we add it
    # to base_lineno because it starts from 1!
    lineno -= 1
    error_lineno = base_lineno + lineno

    return super().__init__( \
"""
In file {}:{} in {}

{} {}
^^^ In update_ff, we only allow <<= to valid fields for constructing nonblocking assignments.
(when constructing instance {} of class \"{}\" in the hierarchy)

Suggestion: Line {} {}""".format( \
      filepath, error_lineno, blk.__name__,
      error_lineno, blk_src[ lineno ].lstrip(''),
      repr(hostobj), hostobj.__class__.__name__,
      error_lineno, suggestion )
    )

class VarNotDeclaredError( Exception ):
  """ Raise when a variable in an update block is not declared """
  def __init__( self, obj, field, blk=None, blk_hostobj=None, lineno=0 ):

    if not blk:
      return super().__init__() # this is just temporary message

    filepath = inspect.getfile( blk_hostobj.__class__ )
    blk_src, base_lineno  = inspect.getsourcelines( blk )

    # Shunning: we need to subtract 1 from inspect's lineno when we add it
    # to base_lineno because it starts from 1!
    lineno -= 1
    error_lineno = base_lineno + lineno

    return super().__init__( \
"""
In file {}:{} in {}

{} {}
^^^ Field \"{}\" of object \"{}\" (class \"{}\") is accessed in block \"{}\",
    but {} does not have field \"{}\".
(when constructing instance {} of class \"{}\" in the hierarchy)

Suggestion: fix incorrect field access at line {}, or fix the declaration somewhere.""".format( \
      filepath, error_lineno, blk.__name__,
      error_lineno, blk_src[ lineno ].lstrip(''),
      field, repr(obj), obj.__class__.__name__, blk.__name__,
      repr(obj), field,
      repr(blk_hostobj), blk_hostobj.__class__.__name__,
      error_lineno ) )

class UpblkFuncSameNameError( Exception ):
  """ Raise when two update block/function are declared with the same name """
  def __init__( self, name ):
    return super().__init__( \
      " Cannot declare two update blocks/functions with the same name {}".format( name ) )

class UpblkCyclicError( Exception ):
  """ Raise when update blocks have cyclic dependencies """

class InvalidConstraintError( Exception ):
  """ Raise when a defined constraint is of wrong format """
  def __init__( self ):
    return super().__init__( \
      "Constraints between two variables are not allowed!" )

class InvalidConnectionError( Exception ):
  """ Raise upon an inappropriate attempt to connect two variables """

class InvalidFuncCallError( Exception ):
  """ Raise upon an inappropriate @s.func function call """

class InvalidPlaceholderError( Exception ):
  """ Raise upon declaring an update block in a placeholder component. """

class NotElaboratedError( Exception ):
  """ Raise when processing a model that hasn't been elaborated yet """
  def __init__( self ):
    return super().__init__( \
    "Please elaborate the model first." )

class InvalidAPICallError( Exception ):
  """ Raise when processing a model that hasn't been elaborated yet """
  def __init__( self, api_name, obj, top ):
    return super().__init__( \
    "{} is only allowed to be called at the top module that .elaborate() "
    "was called on (an instance of {}), but this API call is on {}." \
    .format( api_name, top.__class__, "top."+repr(obj)[2:] ) )

class LeftoverPlaceholderError( Exception ):
  """ Raise upon declaring an update block in a placeholder component. """
  def __init__( self, placeholders ):
    return super().__init__( \
    "Please replace all placeholders with valid components:\n - {}".format(
      "\n - ".join( [ "top.{} (instance of {})".format( repr(x)[2:], x.__class__ ) \
                     for x in placeholders ] ) ) )
