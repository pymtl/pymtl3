"""
========================================================================
errors.py
========================================================================
Errors thrown by other files in this folder.

Author : Shunning Jiang
Date   : Dec 27, 2018
"""
import inspect


class FieldReassignError( Exception ):
  """ Raise when a deprecated API is called"""

class PyMTLDeprecationError( Exception ):
  """ Raise when a deprecated API is called"""

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

class WriteNonSignalError( Exception ):
  """ In update/update_ff, raise when a component is assigned """
  def __init__( self, hostobj, blk, lineno, obj ):

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
^^^ Cannot Assign to {} of type {}.
In update block, assigning values to components/interfaces/method ports is forbidden.
(when constructing instance {} of class \"{}\" in the hierarchy)

Suggestion: check the declaration of the variables, or fix this assignment.""".format( \
      filepath, error_lineno, blk.__name__,
      error_lineno, blk_src[ lineno ].lstrip(''),
      repr(obj), obj.__class__.__name__,
      repr(hostobj), hostobj.__class__.__name__ )
    )

class UpdateBlockWriteError( Exception ):
  """ In update, raise when signal is not @= -ed """
  def __init__( self, hostobj, blk, op, lineno, suggestion ):

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
^^^ In update, only '@=' statements can assign value to signals, not {}
(when constructing instance {} of class \"{}\" in the hierarchy)

Suggestion: Line {} {}""".format( \
      filepath, error_lineno, blk.__name__,
      error_lineno, blk_src[ lineno ].lstrip(''), op,
      repr(hostobj), hostobj.__class__.__name__,
      error_lineno, suggestion )
    )

class UpdateFFBlockWriteError( Exception ):
  """ In update_ff, raise when signal is not <<= -ed"""
  def __init__( self, hostobj, blk, op, lineno, suggestion ):

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
^^^ In update_ff, only '<<=' statements can assign value to signals, not {}
(when constructing instance {} of class \"{}\" in the hierarchy)

Suggestion: Line {} {}""".format( \
      filepath, error_lineno, blk.__name__,
      error_lineno, blk_src[ lineno ].lstrip(''), op,
      repr(hostobj), hostobj.__class__.__name__,
      error_lineno, suggestion )
    )

class UpdateFFNonTopLevelSignalError( Exception ):
  """ In update_ff, raise when non-top signal is <<= -ed"""
  def __init__( self, hostobj, blk, lineno ):
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
^^^ In update_ff, currently only top level signals (not a slice or a subfield) can appear on the left-hand side of '<<='
(when constructing instance {} of class \"{}\" in the hierarchy)
""".format( \
      filepath, error_lineno, blk.__name__,
      error_lineno, blk_src[ lineno ].lstrip(''),
      repr(hostobj), hostobj.__class__.__name__,
      )
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

class InvalidIndexError( Exception ):
  """ Raise when a variable in an update block is not declared """
  def __init__( self, obj, idx, blk=None, blk_hostobj=None, lineno=0 ):

    if not blk:
      return super().__init__() # this is just temporary message

    filepath = inspect.getfile( blk_hostobj.__class__ )
    blk_src, base_lineno  = inspect.getsourcelines( blk )

    # Shunning: we need to subtract 1 from inspect's lineno when we add it
    # to base_lineno because it starts from 1!
    lineno -= 1
    error_lineno = base_lineno + lineno

    if isinstance( idx, tuple ):
      idx_str = f"[{idx.start}:{idx.stop}]"
    else:
      idx_str = f"[{idx}]"

    from pymtl3.datatypes import Bits
    return super().__init__( \
"""
In file {}:{} in {}

{} {}
^^^ Slice {} of object \"{}\" (class \"{}\") is accessed in block \"{}\",
    but {} has \"{}\" type{}.
(when constructing instance {} of class \"{}\" in the hierarchy)

Suggestion: fix incorrect field access at line {}, or fix the declaration somewhere.""".format( \
      filepath, error_lineno, blk.__name__,
      error_lineno, blk_src[ lineno ].lstrip(''),
      idx_str, repr(obj), obj.__class__.__name__, blk.__name__,
      repr(obj), obj._dsl.Type.__name__, "" if issubclass( obj._dsl.Type, Bits ) else ", not BitsN type",
      repr(blk_hostobj), blk_hostobj.__class__.__name__,
      error_lineno ) )

class UnmarkedUpdateOnceError( Exception ):
  """ In update, raise when signal is not @= -ed """
  def __init__( self, hostobj, blk, objs ):

    filepath = inspect.getfile( hostobj.__class__ )
    blk_src, base_lineno  = inspect.getsourcelines( blk )
    return super().__init__( \
"""
In file {}:{} (component {}):
Since update block {} calls the CL/FL method ports/interfaces below, it should be marked as @update_once
- {}

Suggestion: Mark update block {} as @update_once""".format( \
      filepath, base_lineno, repr(hostobj), blk.__name__,
      "\n- ".join( sorted( [repr(x) for x in objs] ) ),
      blk.__name__ )
    )

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

class UnsetMetadataError( Exception ):
  """ Raised when the value of a given metadata key is not set. """
  def __init__( self, key, obj ):
    return super().__init__(
        f"\nAttempting to retrieve unset metadata {key} from component {obj}!" )

class LeftoverPlaceholderError( Exception ):
  """ Raise upon declaring an update block in a placeholder component. """
  def __init__( self, placeholders ):
    return super().__init__( \
    "Please replace all placeholders with valid components:\n - {}".format(
      "\n - ".join( [ "top.{} (instance of {})".format( repr(x)[2:], x.__class__ ) \
                     for x in placeholders ] ) ) )
