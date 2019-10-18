"""
==========================================================================
bit_struct.py
==========================================================================
APIs to generate a bit struct type. Using decorators and type annotations
to create bit struct is much inspired by python3 dataclass implementation.
Note that the implementation (such as the _CAPITAL constants to add some
private metadata) in this file is very similar to the **original python3
dataclass implementation**.
https://github.com/python/cpython/blob/master/Lib/dataclasses.py

The syntax of creating bit struct is very similar to that of python3
dataclass. For example,

@bit_struct
class Point:
  x : Bits4
  y : Bits4

will automatically generate some methods, such as __init__, __str__,
__repr__, for the Point class.

Similar to the built-in dataclasses module, we also provide a
mk_bit_struct function for user to dynamically generate bit struct types.
For example,

mk_bit_struct( 'Pixel',{
    'r' : field( Bits4 )
    'g' : field( Bits4 )
    'b' : field( Bits4, default=b4(5) )
  },
  name_space = {
    '__str__' : lambda self: f'({self.r},{self.g},{self.b})'
  }
)

is equivalent to:

@bit_struct
class Pixel:
  r : Bits4
  g : Bits4
  b : Bits4 = b4(5)

  def __str__( self ):
    return f'({self.r},{self.g},{self.b})'

Author : Yanghui Ou
  Date : July 25, 2019
"""
import keyword
import types
import warnings

#-------------------------------------------------------------------------
# Errors
#-------------------------------------------------------------------------

class NoFieldDeclaredError( AttributeError ):
  ...

#-------------------------------------------------------------------------
# Constants
#-------------------------------------------------------------------------

# Object with this attribute is considered as bit struct, as we assume
# only the bit_struct decorator will stamp this attribute to a class. This
# attribute also stores the field information and can be used for
# translation.
#
# The original dataclass use hasattr( cls, _FIELDS ) to check dataclass.
# We do this here as well
_FIELDS = '__bit_struct_fields__'

def _is_bit_struct_instance(obj):
  """Returns True if obj is an instance of a dataclass."""
  return hasattr(type(obj), _FIELDS)

def is_bit_struct(obj):
  """Returns True if obj is a dataclass or an instance of a
  dataclass."""
  cls = obj if isinstance(obj, type) else type(obj)
  return hasattr(cls, _FIELDS)

_DEFAULT_SELF_NAME = 's'
_ANTI_CONFLICT_SELF_NAME = '__bit_struct_self__'

# A sentinel object to detect if a parameter is supplied or not.  Use
# a class to give it a better repr.
class _MISSING_TYPE:
  ...
MISSING = _MISSING_TYPE()

#-------------------------------------------------------------------------
# Field
#-------------------------------------------------------------------------
# Field instances are used for holding the name, type, and default value
# of each field of the bit struct.

class Field:
  # Here we use __slots__ to declare date members to potentially save
  # space and improve look up time.
  __slots__ = (
    'name',
    'type_',
    'default',
  )

  def __init__( self, name=None, type_=None, default=MISSING ):
    self.name    = name
    self.type_   = type_
    self.default = default

  def __repr__( self ):
    return (
      'Field('
      f'name={self.name!r},'
      f'type_={self.type_!r},'
      f'default={self.default!r}'
      ')'
    )

#-------------------------------------------------------------------------
# field
#-------------------------------------------------------------------------
# Public APIs for creating a Field object. This is used for supporting
# dictionary-like syntax for mk_bit_struct like
#
# mk_bit_struct( 'Point',{
#   'x' : field( Bits4 )
#   'y' : field( Bits4, default=b4(f) )
# }

def field( type_, default=MISSING ):
  return Field( None, type_, default )

#-------------------------------------------------------------------------
# _create_fn
#-------------------------------------------------------------------------
# A helper function that creates a function based on
# - fn_name : name of the function
# - args_lst : a list of arguments in string
# - body_lst : a list of statement of the function body in string
#
# Note: this function mutates _locals and should only be called internally
# to this module.

# Also note that this whole _create_fn thing is similar to the original
# dataclass implementation!

def _create_fn( fn_name, args_lst, body_lst, _globals=None, _locals=None ):

  # Lazily construct empty dictionary. We don't pass None to exec because
  # if locals is None, then exec will mutate the current locals().
  if _locals is None:
    _locals = {}

  # Assemble argument string and body string
  args = ', '.join(args_lst)
  body = '\n'.join(f'  {statement}' for statement in body_lst)

  # Assemble the source code and execute it
  src  = f'def {fn_name}({args}):\n{body}'
  # print(src)
  exec( src, _globals, _locals )

  return _locals[fn_name]

#-------------------------------------------------------------------------
# _mk_init_arg
#-------------------------------------------------------------------------
# Creates a init argument string from a field.
#
# Notes:
#
# We store the default value in _globals by adding a _deflt_ prefix to the
# field name. This seems dangerous as our Bits and bit structs objects are
# all mutable. Another idea is to use repr to re-construct a new instance
# but that seems to be too much to ask.

def _mk_init_arg( f ):

  # Call the default constructor if no default value specified
  if f.default is MISSING:
    default = f'_type_{f.name}()'

  # Use the default value if it is specified by user
  else:
    default = f'_deflt_{f.name}'

  return f'{f.name} : _type_{f.name} = {default}'

#-------------------------------------------------------------------------
# _mk_init_body
#-------------------------------------------------------------------------
# Creates one line of __init__ body from a field and add its default value
# to globals.

def _mk_init_body( self_name, f ):
  return f'{self_name}.{f.name} = {f.name}'

#-------------------------------------------------------------------------
# _mk_tuple_str
#-------------------------------------------------------------------------
# Creates a tuple of string representations of each field. For example,
# if the self_name is 'self' and fields is [ 'x', 'y' ], it will return
# ('self.x', 'self.y'). This is used for creating the default __eq__ and
# __hash__ function.

def _mk_tuple_str( self_name, fields ):
  return f'({",".join([f"{self_name}.{f.name}" for f in fields])},)'

#-------------------------------------------------------------------------
# _mk_init_fn
#-------------------------------------------------------------------------
# Creates a __init__ function based on fields. For example, if fields
# contains two field x (Bits4) and y (Bits4), _mk_init_fn will return a
# function that looks like the following:
#
# def __init__( s, x=_type_x(), y=_type_y() ):
#   s.x = x
#   s.y = y
#
# NOTE:
# _mk_init_fn also takes as argument the name of self in case there is a
# field with name 's' or 'self'.
#
# TODO: should we provide a __post_init__ function like dataclass does?

def _mk_init_fn( self_name, fields ):

  # Sanity check: make sure no postional argument after keyword argument
  seen_kwarg = False
  for f in fields:
    if not f.default is MISSING:
      seen_kwarg = True
    elif seen_kwarg:
      raise TypeError( f'Non keyword argument {f.name} '
                       'follows keyword argument' )

  _globals = { 'MISSING' : MISSING }

  # Register default values to _globals
  for f in fields:
    if not (f.default is MISSING):
      _globals[f'_deflt_{f.name}'] = f.default

  # Register types in _locals
  _locals = { f'_type_{f.name}' : f.type_ for f in fields }

  return _create_fn(
    '__init__',
    [ self_name ] + [ _mk_init_arg( f ) for f in fields ],
    [ _mk_init_body( self_name, f ) for f in fields ],
    _locals  = _locals,
    _globals = _globals,
  )

#-------------------------------------------------------------------------
# _mk_str_fn
#-------------------------------------------------------------------------
# Creates a __str__ function based on fields. For example, if fields
# contains two field x (Bits4) and y (Bits4), _mk_init_fn will return a
# function that looks like the following:
#
# def __str__( self ):
#   return f'{self.x}:{self.y}'

def _mk_str_fn( fields ):
  return _create_fn(
    '__str__',
    [ 'self' ],
    [ 'return f"' +
      ':'.join([ f'{{self.{f.name}}}' for f in fields ]) + '"']
  )

#-------------------------------------------------------------------------
# _mk_repr_fn
#-------------------------------------------------------------------------
# Creates a __repr__ function based on fields. For example, if fields
# contains two field x (Bits4) and y (Bits4), _mk_init_fn will return a
# function that looks like the following:
#
# def __repr__( self ):
#  return self.__class__.qualname__ + f'(x={self.x!r}, y={self.y!r})'

def _mk_repr_fn( fields ):
  return _create_fn(
    '__repr__',
    [ 'self' ],
    [ 'return self.__class__.__qualname__ + f"(' +
      ', '.join([ f'{f.name}={{self.{f.name}!r}}' for f in fields ]) +
      ')"']
  )

#-------------------------------------------------------------------------
# _mk_eq_fn
#-------------------------------------------------------------------------
# Creates a __eq__ function based on fields. By default it just compares
# each field. For example, if fields contains two field x (Bits4) and y
# (Bits4), _mk_init_fn will return a function that looks like the
# following:
#
# def __eq__( self, other ):
#   if other.__class__ is self.__class__:
#     return (self.x,self.y,) == (other.x,other.y,)
#   else:
#     raise NotImplemented

def _mk_eq_fn( fields ):
  self_tuple  = _mk_tuple_str( 'self', fields )
  other_tuple = _mk_tuple_str( 'other', fields )
  return _create_fn(
    '__eq__',
    [ 'self', 'other' ],
    [ 'if other.__class__ is self.__class__:',
      f'  return {self_tuple} == {other_tuple}',
      'else:',
      '  raise NotImplemented']
  )

#-------------------------------------------------------------------------
# _mk_hash_fn
#-------------------------------------------------------------------------
# Creates a __hash__ function based on fields. By default it just hashes
# all fields. For example, if fields contains two field x (Bits4) and y
# (Bits4), _mk_init_fn will return a function that looks like the
# following:
#
# def __hash__( self ):
#   return hash((self.x,self.y,))

def _mk_hash_fn( fields ):
    self_tuple = _mk_tuple_str( 'self', fields )
    return _create_fn(
      '__hash__',
      [ 'self' ],
      [ f'return hash({self_tuple})' ]
    )

#-------------------------------------------------------------------------
# _get_field
#-------------------------------------------------------------------------
# Extract field information from cls based on annotations.

def _get_field( cls, a_name, a_type ):
  default = getattr( cls, a_name, MISSING )
  f = field( a_type, default=default )
  f.name = a_name
  # Yanghui: Should we check default must be instances of Bits or bit
  # struct here?
  return f

#-------------------------------------------------------------------------
# _get_self_name
#-------------------------------------------------------------------------
# Return a self name based on fields.

def _get_self_name( fields ):
  return( _ANTI_CONFLICT_SELF_NAME if _DEFAULT_SELF_NAME in fields else
          _DEFAULT_SELF_NAME )

#-------------------------------------------------------------------------
# _process_cls
#-------------------------------------------------------------------------
# Process the input cls and add methods to it.

def _process_class( cls, add_init=True, add_str=True, add_repr=True,
                    add_hash=True ):

  fields = {}
  add_eq = True

  # Get annotations of the class
  cls_annotations = cls.__dict__.get('__annotations__', {})
  if not cls_annotations:
    raise NoFieldDeclaredError('No field is declared in the bit struct definition' )

  # Get field information from the annotation
  cls_fields = [ _get_field( cls, a_name, a_type )
                 for a_name, a_type in cls_annotations.items() ]

  # Create a dictionary of fields
  for f in cls_fields:
    fields[ f.name ] = f

  # Stamp the special attribute so that translation pass can identify it
  # as bit struct.
  setattr( cls, _FIELDS, fields )

  # Sanity check: is there any Field instance that doesn't have an
  # annotation?
  for name, value in cls.__dict__.items():
    if isinstance( value, Field ) and not name in cls_annotations:
      raise TypeError(f'{name} is a field but has no type annotation!')

  # Add methods to the class

  # Create __init__. Here I follow the dataclass convention that we only
  # add our generated __init__ function when add_init is true and user
  # did not define their own init.
  if add_init:
    if not '__init__' in cls.__dict__:
      self_name = _get_self_name( fields )
      cls.__init__ = _mk_init_fn( self_name, fields.values() )

  # Create __str
  if add_str:
    if not '__str__' in cls.__dict__:
      cls.__str__ = _mk_str_fn( fields.values() )

  # Create __repr__
  if add_repr:
    if not '__repr__' in cls.__dict__:
      cls.__repr__ = _mk_repr_fn( fields.values() )

  # Create __eq__. There is no need for a __ne__ method as python will
  # call __eq__ and negate it.
  # NOTE: if user overwrites __eq__ it may lead to different behavior for
  # the translated verilog as in the verilog world two bit structs are
  # equal only if all the fields are equal.
  if add_eq:
    if not '__eq__' in cls.__dict__:
      cls.__eq__ = _mk_eq_fn( fields.values() )
    else:
      w_msg = ( f'Overwriting {cls.__qualname__}\'s __eq__ may cause the '
                'translated verilog behaves differently from PyMTL '
                'simulation.')
      warnings.warn( w_msg )

  # Create __hash__.
  if add_hash:
    if not '__hash__' in cls.__dict__:
      cls.__hash__ = _mk_hash_fn( fields.values() )

  # TODO: maybe add a to_bits and from bits function.

  return cls

#-------------------------------------------------------------------------
# bit_struct
#-------------------------------------------------------------------------
# The actual class decorator. We add a * in the argument list so that the
# following argument can only be used as keyword arguments.

def bit_struct( _cls=None, *, add_init=True, add_str=True, add_repr=True,
                add_hash=True ):

  def wrap( cls ):
    return _process_class( cls, add_init, add_str, add_repr )

  # Called as @bitstruct(...)
  if _cls is None:
    return wrap

  # Called as @dataclass without parens.
  return wrap( _cls )

#-------------------------------------------------------------------------
# mk_bit_struct
#-------------------------------------------------------------------------
# Dynamically generate a bit struct class.
# TODO: should we add base parameters to support inheritence?

def mk_bit_struct( cls_name, fields, *, namespace=None, add_init=True,
                   add_str=True, add_repr=True, add_hash=True ):

  # Lazily construct empty dictionary
  if namespace is None:
    namespace = {}

  # Copy namespace since we are going to mutate it
  else:
    namespace = namespace.copy()

  # We assume fields is a dictionary and thus there won't be duplicate
  # field names. So we only check if the field names are indeed strings
  # and that they are not keywords.
  annos = {}
  for name, f in fields.items():
    if not isinstance( name, str ) or not name.isidentifier():
      raise TypeError( f'Field name {name!r} is not a valid identifier!' )
    if keyword.iskeyword( name ):
      raise TypeError( f'Field name {name!r} is a keyword!' )

    if not isinstance( f, Field ):
      annos[ name ] = f
    else:
      annos[ name ] = f.type_
      if f.default is not MISSING:
        namespace[ name ] = f.default

  namespace['__annotations__'] = annos

  cls = types.new_class( cls_name, (), {}, lambda ns: ns.update( namespace ) )
  return bit_struct( cls, add_init=add_init, add_str=add_str, add_repr=add_repr,
                     add_hash=True )
