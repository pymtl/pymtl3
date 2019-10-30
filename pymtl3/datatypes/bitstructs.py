"""
==========================================================================
bitstruct.py
==========================================================================
APIs to generate a bitstruct type. Using decorators and type annotations
to create bit struct is much inspired by python3 dataclass implementation.
Note that the implementation (such as the _CAPITAL constants to add some
private metadata) in this file is very similar to the **original python3
dataclass implementation**. The syntax of creating bit struct is very
similar to that of python3 dataclass.
https://github.com/python/cpython/blob/master/Lib/dataclasses.py

For example,

@bitstruct
class Point:
  x : Bits4
  y : Bits4

will automatically generate some methods, such as __init__, __str__,
__repr__, for the Point class.

Similar to the built-in dataclasses module, we also provide a
mk_bitstruct function for user to dynamically generate bit struct types.
For example,

mk_bitstruct( 'Pixel',{
    'r' : Bits4,
    'g' : Bits4,
    'b' : Bits4,
  },
  name_space = {
    '__str__' : lambda self: f'({self.r},{self.g},{self.b})'
  }
)

is equivalent to:

@bitstruct
class Pixel:
  r : Bits4
  g : Bits4
  b : Bits4

  def __str__( self ):
    return f'({self.r},{self.g},{self.b})'

Author : Yanghui Ou, Shunning Jiang
  Date : Oct 19, 2019
"""
import keyword
import types
import warnings

import py

from .bits_import import *

#-------------------------------------------------------------------------
# Constants
#-------------------------------------------------------------------------

# Object with this attribute is considered as bit struct, as we assume
# only the bitstruct decorator will stamp this attribute to a class. This
# attribute also stores the field information and can be used for
# translation.
#
# The original dataclass use hasattr( cls, _FIELDS ) to check dataclass.
# We do this here as well

_FIELDS = '__bitstruct_fields__'

def is_bitstruct_inst( obj ):
  """Returns True if obj is an instance of a dataclass."""
  return hasattr(type(obj), _FIELDS)

def is_bitstruct_class(cls):
  """Returns True if obj is a dataclass ."""
  return isinstance(cls, type) and hasattr(cls, _FIELDS)

_DEFAULT_SELF_NAME = 's'
_ANTI_CONFLICT_SELF_NAME = '__bitstruct_self__'

#-------------------------------------------------------------------------
# _create_fn
#-------------------------------------------------------------------------
# A helper function that creates a function based on
# - fn_name : name of the function
# - args_lst : a list of arguments in string
# - body_lst : a list of statement of the function body in string

# Also note that this whole _create_fn thing is similar to the original
# dataclass implementation!

def _create_fn( fn_name, args_lst, body_lst, _globals=None, class_method=False ):
  # Assemble argument string and body string
  args = ', '.join(args_lst)
  body = '\n'.join(f'  {statement}' for statement in body_lst)

  # Assemble the source code and execute it
  src = '@classmethod\n' if class_method else ''
  src += f'def {fn_name}({args}):\n{body}'
  _locals = {}
  exec( py.code.Source(src).compile(), _globals, _locals )
  return _locals[fn_name]

#-------------------------------------------------------------------------
# _mk_init_arg
#-------------------------------------------------------------------------
# Creates a init argument string from a field.
#
# Shunning: I revamped the whole thing because they are indeed mutable
# objects.

def _mk_init_arg( name, type_ ):
  # default is always None
  if isinstance( type_, list ) or is_bitstruct_class( type_ ):
    return f'{name} = None'
  return f'{name} = 0'

#-------------------------------------------------------------------------
# _mk_init_body
#-------------------------------------------------------------------------
# Creates one line of __init__ body from a field
# to globals.

def _mk_init_body( self_name, name, type_ ):
  def _recursive_generate_init( x ):
    if isinstance( x, list ):
      return f"[{', '.join( [ _recursive_generate_init(x[0]) ] * len(x) )}]"
    return f"_type_{name}()"

  if isinstance( type_, list ) or is_bitstruct_class( type_ ):
    return f'{self_name}.{name} = {name} or {_recursive_generate_init(type_)}'

  assert issubclass( type_, Bits )
  return f'{self_name}.{name} = _type_{name}({name})'

#-------------------------------------------------------------------------
# _mk_tuple_str
#-------------------------------------------------------------------------
# Creates a tuple of string representations of each field. For example,
# if the self_name is 'self' and fields is [ 'x', 'y' ], it will return
# ('self.x', 'self.y'). This is used for creating the default __eq__ and
# __hash__ function.

def _mk_tuple_str( self_name, fields ):
  return f'({",".join([f"{self_name}.{name}" for name in fields])},)'

#-------------------------------------------------------------------------
# _mk_init_fn
#-------------------------------------------------------------------------
# Creates a __init__ function based on fields. For example, if fields
# contains two field x (Bits4) and y (Bits4), _mk_init_fn will return a
# function that looks like the following:
#
# def __init__( s, x = 0, y = 0, z = None, p = None ):
#   s.x = _type_x(x)
#   s.y = _type_y(y)
#   s.z = z or _type_z()
#   s.p = p or [ _type_p(), _type_p() ]
#
# NOTE:
# _mk_init_fn also takes as argument the name of self in case there is a
# field with name 's' or 'self'.
#
# TODO: should we provide a __post_init__ function like dataclass does?

def _mk_init_fn( self_name, fields ):

  # Register necessary types in _globals
  _globals = {}

  for name, type_ in fields.items():
    if isinstance( type_, list ):
      x = type_[0]
      while isinstance( x, list ):
        x = x[0]
      _globals[ f"_type_{name}" ] = x
    else:
      assert issubclass( type_, Bits ) or is_bitstruct_class( type_ )
      _globals[ f"_type_{name}" ] = type_

  return _create_fn(
    '__init__',
    [ self_name ] + [ _mk_init_arg( *field ) for field in fields.items() ],
    [ _mk_init_body( self_name, *field ) for field in fields.items() ],
    _globals = _globals,
  )

#-------------------------------------------------------------------------
# _mk_str_fn
#-------------------------------------------------------------------------
# Creates a __str__ function based on fields. For example, if fields
# contains two field x (Bits4) and y (Bits4), _mk_str_fn will return a
# function that looks like the following:
#
# def __str__( self ):
#   return f'{self.x}:{self.y}'

def _mk_str_fn( fields ):
  return _create_fn(
    '__str__',
    [ 'self' ],
    [ 'return f"' +
      ':'.join([ f'{{self.{name}}}' for name in fields ]) + '"']
  )

#-------------------------------------------------------------------------
# _mk_repr_fn
#-------------------------------------------------------------------------
# Creates a __repr__ function based on fields. For example, if fields
# contains two field x (Bits4) and y (Bits4), _mk_repr_fn will return a
# function that looks like the following:
#
# def __repr__( self ):
#  return self.__class__.qualname__ + f'(x={self.x!r}, y={self.y!r})'

def _mk_repr_fn( fields ):
  return _create_fn(
    '__repr__',
    [ 'self' ],
    [ 'return self.__class__.__qualname__ + f"(' +
      ', '.join([ f'{name}={{self.{name}!r}}' for name in fields ]) +
      ')"']
  )

#-------------------------------------------------------------------------
# _mk_eq_fn
#-------------------------------------------------------------------------
# Creates a __eq__ function based on fields. By default it just compares
# each field. For example, if fields contains two field x (Bits4) and y
# (Bits4), _mk_eq_fn will return a function that looks like the
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
    [ f'return (other.__class__ is self.__class__) and {self_tuple} == {other_tuple}' ]
  )

#-------------------------------------------------------------------------
# _mk_hash_fn
#-------------------------------------------------------------------------
# Creates a __hash__ function based on fields. By default it just hashes
# all fields. For example, if fields contains two field x (Bits4) and y
# (Bits4), _mk_hash_fn will return a function that looks like the
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
# _mk_ff_fn
#-------------------------------------------------------------------------
# Creates __ilshift__ and _flip functions that looks like the follwoing:
#
# def __ilshift__( self, other ):
#   self.x <<= other.x
#   for i in range(5):
#     for j in range(6):
#       self.y[i][j] <<= other.y[i][j]
#
# def _flip( self, other ):
#   self.x._flip()
#   for i in range(5):
#     for j in range(6):
#       self.y[i][j]._flip()

def _mk_ff_fn( fields ):
  ilshift_strs = []
  flip_strs    = []
  for name, type_ in fields.items():
    if isinstance( type_, list ):
      i = 0
      loop = f"{' '*i}for i{i} in range({len(type_)}):"
      ilshift_strs.append(loop)
      flip_strs   .append(loop)
      type_ = type_[0]
      i = 1
      while isinstance( type_, list ):
        loop = f"{' '*(i*2)}for i{i} in range({len(type_)}):"
        ilshift_strs.append(loop)
        flip_strs   .append(loop)
        type_ = type_[0]
        i += 1

      indices = ''.join( [ f'[i{k}]' for k in range(i)] )
      ilshift_strs.append( f"{' '*(i*2)}self.{name}{indices} <<= o.{name}{indices}" )
      flip_strs   .append( f"{' '*(i*2)}self.{name}{indices}._flip()" )

    else:
      ilshift_strs.append( f'self.{name} <<= o.{name}' )
      flip_strs.append( f'self.{name}._flip()' )

  return _create_fn(
    '__ilshift__',
    [ 'self', 'o' ],
    ilshift_strs + [ 'return self' ],
  ), _create_fn(
    '_flip',
    [ 'self' ],
    flip_strs,
  ),

#-------------------------------------------------------------------------
# _check_valid_array
#-------------------------------------------------------------------------

def _recursive_check_array_types( current ):
  x = current[0]
  if isinstance( x, list ):
    x_len  = len(x)
    x_type = _recursive_check_array_types( x )
    for y in current[1:]:
      assert isinstance( y, list ) and len(y) == x_len
      y_type = _recursive_check_array_types( y )
      assert y_type is x_type
    return x_type

  assert issubclass( x, Bits ) or is_bitstruct_class( x )
  for y in current[1:]:
    assert y is x
  return x

def _check_valid_array_of_types( arr ):
  # Check if the provided list is a strict multidimensional array
  try:
    return _recursive_check_array_types( arr )
  except Exception as e:
    print(e)
    return None

#-------------------------------------------------------------------------
# _check_field_annotation
#-------------------------------------------------------------------------

def _check_field_annotation( cls, name, type_ ):
  # Make sure not default is annotated
  if hasattr( cls, name ):
    default = getattr( cls, name )
    raise TypeError( "We don't allow subfields to have default value:\n"
                     f"- Field '{name}' of BitStruct {cls.__name__} has default value {default!r}." )

  # Special case if the type is an instance of list
  if isinstance( type_, list ):
    if _check_valid_array_of_types( type_ ) is None:
      raise TypeError( "The provided list spec should be a strict multidimensional ARRAY "
                       f"with no varying sizes or types. All non-list elements should be VALID types." )
  else:
    # Now we work with types
    if not isinstance( type_, type ):
      raise TypeError(f"{type_} is not a type\n"\
                      f"- Field '{name}' of BitStruct {cls.__name__} is annotated as {type_}.")

    # More specifically, Bits and BitStruct
    if not issubclass( type_, Bits ) and not is_bitstruct_class( type_ ):
      raise TypeError( "We currently only support BitsN, list, or another BitStruct as BitStruct field:\n"
                      f"- Field '{name}' of BitStruct {cls.__name__} is annotated as {type_}." )

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

_bitstruct_hash_cache = {}

def _process_class( cls, add_init=True, add_str=True, add_repr=True,
                    add_hash=True ):

  # Get annotations of the class
  cls_annotations = cls.__dict__.get('__annotations__', {})
  if not cls_annotations:
    raise AttributeError( "No field is declared in the bit struct definition.\n"
                         f"Suggestion: check the definition of {cls.__name__} to"
                          " make sure it only contains 'field_name(string): Type(type).'" )

  # Get field information from the annotation and prepare for hashing
  fields = {}
  hashable_fields = {}

  def _convert_list_to_tuple( x ):
    if isinstance( x, list ):
      return tuple( [ _convert_list_to_tuple( y ) for y in x ] )
    return x

  for a_name, a_type in cls_annotations.items():
    _check_field_annotation( cls, a_name, a_type )
    fields[ a_name ] = a_type
    hashable_fields[ a_name ] = _convert_list_to_tuple( a_type )

  cls._hash = _hash = hash( (cls.__name__, *tuple(hashable_fields.items()),
                             add_init, add_str, add_repr, add_hash) )

  if _hash in _bitstruct_hash_cache:
    return _bitstruct_hash_cache[ _hash ]

  _bitstruct_hash_cache[ _hash ] = cls

  # Stamp the special attribute so that translation pass can identify it
  # as bit struct.
  setattr( cls, _FIELDS, fields )

  # Add methods to the class

  # Create __init__. Here I follow the dataclass convention that we only
  # add our generated __init__ function when add_init is true and user
  # did not define their own init.
  if add_init:
    if not '__init__' in cls.__dict__:
      cls.__init__ = _mk_init_fn( _get_self_name(fields), fields )

  # Create __str__
  if add_str:
    if not '__str__' in cls.__dict__:
      cls.__str__ = _mk_str_fn( fields )

  # Create __repr__
  if add_repr:
    if not '__repr__' in cls.__dict__:
      cls.__repr__ = _mk_repr_fn( fields )

  # Create __eq__. There is no need for a __ne__ method as python will
  # call __eq__ and negate it.
  # NOTE: if user overwrites __eq__ it may lead to different behavior for
  # the translated verilog as in the verilog world two bit structs are
  # equal only if all the fields are equal. We always try to add __eq__

  if not '__eq__' in cls.__dict__:
    cls.__eq__ = _mk_eq_fn( fields )
  else:
    w_msg = ( f'Overwriting {cls.__qualname__}\'s __eq__ may cause the '
              'translated verilog behaves differently from PyMTL '
              'simulation.')
    warnings.warn( w_msg )

  # Create __hash__.
  if add_hash:
    if not '__hash__' in cls.__dict__:
      cls.__hash__ = _mk_hash_fn( fields )

  # Shunning: add __ilshift__ and _flip for update_ff
  assert not '__ilshift__' in cls.__dict__ and not '_flip' in cls.__dict__

  cls.__ilshift__, cls._flip = _mk_ff_fn( fields )

  assert not 'get_field_type' in cls.__dict__

  def get_field_type( cls, name ):
    if name in cls.__bitstruct_fields__:
      return cls.__bitstruct_fields__[ name ]
    raise AttributeError( f"{cls} has no field '{name}'" )

  cls.get_field_type = classmethod(get_field_type)

  # TODO: maybe add a to_bits and from bits function.

  return cls

#-------------------------------------------------------------------------
# bitstruct
#-------------------------------------------------------------------------
# The actual class decorator. We add a * in the argument list so that the
# following argument can only be used as keyword arguments.

def bitstruct( _cls=None, *, add_init=True, add_str=True, add_repr=True, add_hash=True ):

  def wrap( cls ):
    return _process_class( cls, add_init, add_str, add_repr )

  # Called as @bitstruct(...)
  if _cls is None:
    return wrap

  # Called as @bitstruct without parens.
  return wrap( _cls )

#-------------------------------------------------------------------------
# mk_bitstruct
#-------------------------------------------------------------------------
# Dynamically generate a bit struct class.
# TODO: should we add base parameters to support inheritence?

def mk_bitstruct( cls_name, fields, *, namespace=None, add_init=True,
                   add_str=True, add_repr=True, add_hash=True ):

  # copy namespace since  will mutate it
  namespace = {} if namespace is None else namespace.copy()

  # We assume fields is a dictionary and thus there won't be duplicate
  # field names. So we only check if the field names are indeed strings
  # and that they are not keywords.
  annos = {}
  for name, f in fields.items():
    if not isinstance( name, str ) or not name.isidentifier():
      raise TypeError( f'Field name {name!r} is not a valid identifier!' )
    if keyword.iskeyword( name ):
      raise TypeError( f'Field name {name!r} is a keyword!' )
    annos[ name ] = f

  namespace['__annotations__'] = annos
  cls = types.new_class( cls_name, (), {}, lambda ns: ns.update( namespace ) )
  return bitstruct( cls, add_init=add_init, add_str=add_str,
                    add_repr=add_repr, add_hash=add_hash )
