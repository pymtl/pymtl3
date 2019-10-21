"""
==========================================================================
bit_struct.py
==========================================================================
APIs to generate a bit struct type. Using decorators and type annotations
to create bit struct is much inspired by python3 dataclass implementation.
Note that the implementation (such as the _CAPITAL constants to add some
private metadata) in this file is very similar to the **original python3
dataclass implementation**. The syntax of creating bit struct is very
similar to that of python3 dataclass.
https://github.com/python/cpython/blob/master/Lib/dataclasses.py

For example,

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
    'r' : Bits4,
    'g' : Bits4,
    'b' : Bits4,
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

#-------------------------------------------------------------------------
# Field
#-------------------------------------------------------------------------
# Field instances are used for holding the name and type of each field of
# the bit struct. Since we only accept Bits, BitStruct and list, and
# all of them don't allow default, we just need two fields, while type_
# can be a list _object_.

class Field:
  # Here we use __slots__ to declare date members to potentially save
  # space and improve look up time.
  __slots__ = ( 'name', 'type_' )

  def __init__( self, name=None, type_=None ):
    self.name  = name
    self.type_ = type_

  def __repr__( self ):
    return f'(Field(name={self.name!r},type_={self.type_!r})'

#-------------------------------------------------------------------------
# field
#-------------------------------------------------------------------------
# Public APIs for creating a Field object. This is used for supporting
# dictionary-like syntax for mk_bit_struct like
#
# mk_bit_struct( 'Point',{
#   'x' : Bits4,
#   'y' : Bits4,
# }

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
  print(src)
  exec( py.code.Source(src).compile(), _globals, _locals )
  return _locals[fn_name]

#-------------------------------------------------------------------------
# _mk_init_arg
#-------------------------------------------------------------------------
# Creates a init argument string from a field.
#
# Shunning: I revamped the whole thing because they are indeed mutable
# objects.
#
# x: Bits4 = None

def _mk_init_arg( f ):
  # default is always None
  if isinstance( f.type_, list ): return f'{f.name}: list = None'
  return f'{f.name}: _type_{f.name} = None'

#-------------------------------------------------------------------------
# _mk_init_body
#-------------------------------------------------------------------------
# Creates one line of __init__ body from a field and add its default value
# to globals.

def _mk_init_body( self_name, f ):
  def _recursive_generate_init( x ):
    if isinstance( x, list ):
      return f"[{', '.join( [ _recursive_generate_init(x[0]) ] * len(x) )}]"
    return f"_type_{f.name}()"

  type_ = f.type_
  if isinstance( type_, list ):
    return f'{self_name}.{f.name} = {f.name} or {_recursive_generate_init(f.type_)}'

  assert issubclass( type_, Bits ) or is_bit_struct( type_ )
  return f'{self_name}.{f.name} = {f.name} or _type_{f.name}()'

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
# def __init__( s, x: Bits4 = None, y: Bits4 = None ):
#   s.x = x or Bits4()
#   s.y = y or Bits4()
#
# NOTE:
# _mk_init_fn also takes as argument the name of self in case there is a
# field with name 's' or 'self'.
#
# TODO: should we provide a __post_init__ function like dataclass does?

def _mk_init_fn( self_name, fields ):

  # Register necessary types in _globals
  _globals = {}

  for f in fields:
    if isinstance( f.type_, list ):
      x = f.type_[0]
      while isinstance( x, list ):
        x = x[0]
      _globals[ f"_type_{f.name}" ] = x
    else:
      assert issubclass( f.type_, Bits ) or is_bit_struct( f.type_ )
      _globals[ f"_type_{f.name}" ] = f.type_

  return _create_fn(
    '__init__',
    [ self_name ] + [ _mk_init_arg( f ) for f in fields ],
    [ _mk_init_body( self_name, f ) for f in fields ],
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
    [ f'return (other.__class__ is self.__class__) and {self_tuple} == {other_tuple}' ]
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
# _mk_mk_msg
#-------------------------------------------------------------------------
# __init__ doesn't perform casting and is usually used for constructing an
# empty message. mk_msg does casting for Bits fields and preserve
# list/BitStruct field, and is a class method
#
# @classmethod
# def mk_msg(cls, x, y, some_struct_inst):
#   return cls(Bits4(x), Bits8(y), some_struct_inst)

def _mk_mk_msg( fields ):

  # Register necessary types in _globals
  _globals = {}

  assign_strs = []
  for f in fields:
    type_ = f.type_
    if isinstance( type_, list ) or is_bit_struct( type_ ):
      assign_strs.append( f'{f.name}' )
    else:
      assert issubclass( type_, Bits )
      _globals[ type_.__name__ ] = type_
      assign_strs.append( f'{type_.__name__}({f.name})' )

  return _create_fn(
    'mk_msg',
    [ "cls" ] + [ f.name for f in fields ],
    [ f"return cls({ ', '.join(assign_strs) })" ],
    _globals = _globals,
    class_method = True,
  )

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

  assert issubclass( x, Bits ) or is_bit_struct( x )
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
# _get_field
#-------------------------------------------------------------------------
# Extract field information from cls based on annotations.

def _get_field( cls, name, type_ ):
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
    return Field( name, type_ )

  # Now we work with types
  if not isinstance( type_, type ):
    raise TypeError(f"{type_} is not a type\n"\
                    f"- Field '{name}' of BitStruct {cls.__name__} is annotated as {type_}.")

  # More specifically, Bits and BitStruct
  if not issubclass( type_, Bits ) and not is_bit_struct( type_ ):
    raise TypeError( "We currently only support BitsN, list, or another BitStruct as BitStruct field:\n"
                    f"- Field '{name}' of BitStruct {cls.__name__} is annotated as {type_}." )

  return Field( name, type_ )

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
    raise AttributeError( "No field is declared in the bit struct definition.\n"
                         f"Suggestion: check the definition of {cls.__name__} to"
                          " make sure it only contains 'field_name(string): Type(type).'" )

  # Get field information from the annotation
  for a_name, a_type in cls_annotations.items():
    f = _get_field( cls, a_name, a_type )
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
      cls.__init__ = _mk_init_fn( _get_self_name(fields), fields.values() )

  # Create __str__
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

  # Create mk_msg.
  assert not 'mk_msg' in cls.__dict__
  cls.mk_msg = _mk_mk_msg( fields.values() )

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

  # Called as @bit_struct(...)
  if _cls is None:
    return wrap

  # Called as @bit_struct without parens.
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
    annos[ name ] = f

  namespace['__annotations__'] = annos
  cls = types.new_class( cls_name, (), {}, lambda ns: ns.update( namespace ) )
  ret = bit_struct( cls, add_init=add_init, add_str=add_str, add_repr=add_repr,
                    add_hash=True )

  return ret
