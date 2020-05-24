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
import functools
import keyword
import operator
import types
import warnings

import py

from pymtl3.extra.pypy import custom_exec

from .bits_import import *
from .helpers import concat

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

def get_bitstruct_inst_all_classes( obj ):
  # list: put all types together
  if isinstance( obj, list ):
    return functools.reduce( operator.or_, [ get_bitstruct_inst_all_classes(x) for x in obj ] )
  ret = { obj.__class__ }
  # BitsN or int
  if isinstance( obj, (Bits, int) ):
    return ret
  # BitStruct
  assert is_bitstruct_inst( obj ), f"{obj} is not a valid PyMTL Bitstruct!"
  return ret | functools.reduce( operator.or_, [ get_bitstruct_inst_all_classes(getattr(obj, v))
                                                for v in obj.__bitstruct_fields__.keys() ] )

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

def _create_fn( fn_name, args_lst, body_lst, _globals=None ):
  # Assemble argument string and body string
  args = ', '.join(args_lst)
  body = '\n'.join(f'  {statement}' for statement in body_lst)

  # Assemble the source code and execute it
  src = f'def {fn_name}({args}):\n{body}'
  if _globals is None: _globals = {}
  _locals = {}
  custom_exec( py.code.Source(src).compile(), _globals, _locals )
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
#  return self.__class__.__name__ + f'(x={self.x!r}, y={self.y!r})'

def _mk_repr_fn( fields ):
  return _create_fn(
    '__repr__',
    [ 'self' ],
    [ 'return self.__class__.__name__ + f"(' +
      ','.join([ f'{{self.{name}!r}}' for name in fields ]) +
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

#--------------------------PyMTL3 specific--------------------------------

#-------------------------------------------------------------------------
# _mk_ff_fn
#-------------------------------------------------------------------------
# Creates __ilshift__ and _flip functions that looks like the following:
#
# def __ilshift__( self, other ):
#   if self.__class__ is not other.__class__:
#     other = self.__class__.from_bits( other.to_bits() )
#   self.x <<= other.x
#   self.y[0][0] <<= other.y[0][0]
#
# def _flip( self ):
#   self.x._flip()
#   self.y[i][j]._flip()

def _mk_ff_fn( fields ):

  def _gen_list_ilshift_strs( type_, prefix='' ):
    if isinstance( type_, list ):
      ilshift_strs, flip_strs = [], []
      for i in range(len(type_)):
        ils, fls = _gen_list_ilshift_strs( type_[0], f"{prefix}[{i}]" )
        ilshift_strs.extend( ils )
        flip_strs.extend( fls )
      return ilshift_strs, flip_strs
    else:
      return [ f"self.{prefix} <<= other.{prefix}" ], [f"self.{prefix}._flip()"]

  ilshift_strs = [ 'if self.__class__ is not other.__class__:',
                   '  other = self.__class__.from_bits( other.to_bits() )']
  flip_strs = []
  for name, type_ in fields.items():
    ils, fls = _gen_list_ilshift_strs( type_, name )
    ilshift_strs.extend( ils )
    flip_strs.extend( fls )

  return _create_fn(
    '__ilshift__',
    [ 'self', 'other' ],
    ilshift_strs + [ "return self" ],
  ), _create_fn(
    '_flip',
    [ 'self' ],
    flip_strs,
  ),

#-------------------------------------------------------------------------
# _mk_clone_fn
#-------------------------------------------------------------------------
# Creates clone function that looks like the following:
# Use this clone function in any place that you need to perform a
# deepcopy on a bitstruct.
#
# def clone( self ):
#   return self.__class__( self.x.clone(), [ self.y[0].clone(), self.y[1].clone() ]  )

def _gen_list_clone_strs( type_, prefix='' ):
  if isinstance( type_, list ):
    return "[" + ",".join( [ _gen_list_clone_strs( type_[0], f"{prefix}[{i}]" )
                        for i in range(len(type_)) ] ) + "]"
  else:
    return f"{prefix}.clone()"

def _mk_clone_fn( fields ):
  clone_strs = [ 'return self.__class__(' ]

  for name, type_ in fields.items():
    clone_strs.append( "  " + _gen_list_clone_strs( type_, f'self.{name}' ) + "," )

  return _create_fn(
    'clone',
    [ 'self' ],
    clone_strs + [ ')' ],
  )

def _mk_deepcopy_fn( fields ):
  clone_strs = [ 'return self.__class__(' ]

  for name, type_ in fields.items():
    clone_strs.append( "  " + _gen_list_clone_strs( type_, f'self.{name}' ) + "," )

  return _create_fn(
    '__deepcopy__',
    [ 'self', 'memo' ],
    clone_strs + [ ')' ],
  )

#-------------------------------------------------------------------------
# _mk_imatmul_fn
#-------------------------------------------------------------------------
# Creates @= function that copies the value over ...
# TODO create individual from_bits for imatmul and ilshift

# def __imatmul__( self, other ):
#   if self.__class__ is not other.__class__:
#     other = self.__class__.from_bits( other.to_bits() )
#   self.x @= other.x
#   self.y[0] @= other.y[0]
#   self.y[1] @= other.y[1]

def _mk_imatmul_fn( fields ):

  def _gen_list_imatmul_strs( type_, prefix='' ):
    if isinstance( type_, list ):
      ret = []
      for i in range(len(type_)):
        ret.extend( _gen_list_imatmul_strs( type_[0], f"{prefix}[{i}]" ) )
      return ret
    else:
      return [ f"self.{prefix} @= other.{prefix}" ]

  imatmul_strs = [ 'if self.__class__ is not other.__class__:',
                   '  other = self.__class__.from_bits( other.to_bits() )']
  for name, type_ in fields.items():
    imatmul_strs.extend( _gen_list_imatmul_strs( type_, name ) )

  return _create_fn(
    '__imatmul__',
    [ 'self', 'other' ],
    imatmul_strs + [ "return self" ],
  )

#-------------------------------------------------------------------------
# _mk_nbits_to_bits_fn
#-------------------------------------------------------------------------
# Creates nbits, to_bits function that copies the value over ...
#
# def to_bits( self ):
#   return concat( self.x, self.y[0], self.y[1] )
#
# TODO packing order of array? x[0] is LSB or MSB of a list
# current we do LSB

def _mk_nbits_to_bits_fn( fields ):

  def _gen_to_bits_strs( type_, prefix, start_bit ):

    if isinstance( type_, list ):
      to_strs = []
      # The packing order is LSB, so we need to reverse the list to make x[-1] higher bits
      for i in reversed(range(len(type_))):
        start_bit, tos = _gen_to_bits_strs( type_[0], f"{prefix}[{i}]", start_bit )
        to_strs.extend( tos )
      return start_bit, to_strs

    elif is_bitstruct_class( type_ ):
      to_strs = []
      for name, typ in getattr(type_, _FIELDS).items():
        start_bit, tos = _gen_to_bits_strs( typ, f"{prefix}.{name}", start_bit )
        to_strs.extend( tos )
      return start_bit, to_strs

    else:
      end_bit = start_bit + type_.nbits
      return end_bit, [ f"self.{prefix}" ]

  to_bits_strs = []
  total_nbits  = 0
  for name, type_ in fields.items():
    total_nbits, tos = _gen_to_bits_strs( type_, name, total_nbits )
    to_bits_strs.extend( tos )

  return total_nbits, _create_fn( 'to_bits', [ 'self' ],
                                  [ f"return concat({', '.join(to_bits_strs)})" ],
                                  _globals={'concat':concat} )

#-------------------------------------------------------------------------
# _mk_from_bits_fn
#-------------------------------------------------------------------------
# Creates static method from_bits that creates a new bitstruct based on Bits
# and instance method _from_bits that copies the value over
#
# @staticmethod
# def from_bits( other ):
#   return self.__class__( other[16:32], other[0:16] )

def _mk_from_bits_fns( fields, total_nbits ):

  def _gen_from_bits_strs( type_, end_bit ):

    if isinstance( type_, list ):
      from_strs = []
      # Since we are doing LSB for x[0], we need to unpack from the last
      # element of the list, and then reverse it again to construct a list ...
      for i in range(len(type_)):
        end_bit, fs = _gen_from_bits_strs( type_[0], end_bit )
        from_strs.extend( fs )
      return end_bit, [ f"[{','.join(reversed(from_strs))}]" ]

    elif is_bitstruct_class( type_ ):
      if type_ in type_name_mapping:
        type_name = type_name_mapping[ type_ ]
      else:
        type_name = f"_type{len(type_name_mapping)}"
        type_name_mapping[ type_ ] = type_name

      from_strs = []
      for name, typ in getattr(type_, _FIELDS).items():
        end_bit, fs = _gen_from_bits_strs( typ, end_bit )
        from_strs.extend( fs )
      return end_bit, [ f"{type_name}({','.join(from_strs)})" ]

    else:
      if type_ not in type_name_mapping:
        type_name_mapping[ type_ ] = type_.__name__
      else:
        assert type_name_mapping[ type_ ] == type_.__name__
      start_bit = end_bit - type_.nbits
      return start_bit, [ f"other[{start_bit}:{end_bit}]" ]

  from_bits_strs = []
  end_bit = total_nbits

  # This is to make sure we capture two types with the same name but different
  # attributes
  type_name_mapping = {}
  type_count = 0

  for _, type_ in fields.items():
    end_bit, fs = _gen_from_bits_strs( type_, end_bit )
    from_bits_strs.extend( fs )

  assert end_bit == 0
  _globals = { y: x for x,y in type_name_mapping.items() }
  assert len(_globals) == len(type_name_mapping)

  # TODO add assertion in bits
  return _create_fn( 'from_bits', [ 'cls', 'other' ],
                     [ "assert cls.nbits == other.nbits, f'LHS bitstruct {cls.nbits}-bit <> RHS other {other.nbits}-bit'",
                       "other = other.to_bits()",
                       f"return cls({','.join(from_bits_strs)})" ], _globals )
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
                       "with no varying sizes or types. All non-list elements should be VALID types." )
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

  reserved_fields = ['to_bits', 'from_bits', 'nbits']
  for x in reserved_fields:
    assert x not in cls.__dict__, f"Currently a bitstruct cannot have {reserved_fields}, but "\
                                  f"{x} is provided as {cls.__dict__[x]}"


  for a_name, a_type in cls_annotations.items():
    assert a_name not in reserved_fields, f"Currently a bitstruct cannot have {reserved_fields}, but "\
                                          f"{a_name} is annotated as {a_type}"
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

  # Shunning: add clone
  assert not 'clone' in cls.__dict__ and not '__deepcopy__' in cls.__dict__

  cls.clone = _mk_clone_fn( fields )

  cls.__deepcopy__ = _mk_deepcopy_fn( fields )

  # Shunning: add imatmul for assignment, as well as nbits/to_bits/from_bits
  assert '__imatmul__' not in cls.__dict__ and 'to_bits' not in cls.__dict__ and \
         'nbits' not in cls.__dict__ and 'from_bits' not in cls.__dict__

  cls.__imatmul__ = _mk_imatmul_fn( fields )
  cls.nbits, cls.to_bits = _mk_nbits_to_bits_fn( fields )

  from_bits = _mk_from_bits_fns( fields, cls.nbits )
  cls.from_bits = classmethod(from_bits)

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
