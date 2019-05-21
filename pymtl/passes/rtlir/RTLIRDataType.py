#=========================================================================
# RTLIRDataType.py
#=========================================================================
# Author : Peitian Pan
# Date   : Jan 6, 2019
"""RTLIR instance data types and generation methods.

This file contains all RTLIR instance data types and methods to generate
these type objects. Each instance of the type class defined in this module
is a data type object or simply a data type. RTLIR instance type Signal
can be parameterized by the generated type objects.
"""
from __future__ import absolute_import, division, print_function

import __builtin__
from functools import reduce

import pymtl
from pymtl.dsl.Connectable import Const as pymtl_Const
from pymtl.dsl.Connectable import Signal as pymtl_Signal

from .errors import RTLIRConversionError
from .utility import collect_objs


class BaseRTLIRDataType( object ):
  """Base abstract RTLIR data type class."""
  def __ne__( s, other ):
    return not s.__eq__( other )

class Vector( BaseRTLIRDataType ):
  """RTLIR data type class for vector type."""
  def __init__( s, nbits ):
    assert nbits > 0, 'vector bitwidth should be a positive integer!'
    s.nbits = nbits

  def get_length( s ):
    return s.nbits

  def __eq__( s, other ):
    return isinstance(other, Vector) and s.nbits == other.nbits

  def __call__( s, obj ):
    """Return if type `obj` be cast into type `s`."""
    return isinstance( obj, ( Vector, Bool ) )

  def __str__( s ):
    return 'Vector{}'.format( s.nbits )

class Struct( BaseRTLIRDataType ):
  """RTLIR data type class for struct type."""
  def __init__( s, name, properties, packed_order ):
    assert len( packed_order ) > 0, 'packed_order is empty!'
    s.name = name
    s.properties = properties
    s.packed_order = packed_order

  def __eq__( s, u ):
    return isinstance(u, Struct) and s.name == u.name

  def get_name( s ):
    return s.name

  def get_pack_order( s ):
    return s.packed_order

  def get_length( s ):
    return reduce(lambda s, d: s+d.get_length(), s.properties.values(), 0)

  def has_property( s, p ):
    return p in s.properties

  def get_property( s, p ):
    return s.properties[ p ]

  def get_all_properties( s ):
    return s.properties.iteritems()

  def __call__( s, obj ):
    """Return if obj be cast into type `s`."""
    return s == obj

  def __str__( s ):
    return 'Struct {}'.format( s.name )

class Bool( BaseRTLIRDataType ):
  """RTLIR data type class for struct type.
  
  Bool data type cannot be instantiated explicitly. It can only appear as
  the result of comparisons.
  """
  def __init__( s ):
    pass

  def __eq__( s, other ):
    return isinstance(other, Bool)

  def get_length( s ):
    return 1

  def __call__( s, obj ):
    """Return if obj be cast into type `s`."""
    return isinstance( obj, ( Bool, Vector ) )

  def __str__( s ):
    return 'Bool'

class PackedArray( BaseRTLIRDataType ):
  """RTLIR data type class for packed array type."""
  def __init__( s, dim_sizes, sub_dtype ):
    assert isinstance( sub_dtype, BaseRTLIRDataType ), \
      'non-RTLIR data type {} as sub type of array.'.format(sub_dtype)
    assert not isinstance( sub_dtype, PackedArray ), \
      'nested PackedArray is not allowed!'
    assert len( dim_sizes ) >= 1, \
      'PackedArray dimension count should be greater than 0!'
    assert reduce( lambda s, i: s+i, dim_sizes, 0 ) > 0, \
      'PackedArray should have at least one element!'
    s.dim_sizes = dim_sizes
    s.sub_dtype = sub_dtype

  def __eq__( s, other ):
    if not isinstance(other, PackedArray): return False
    if len( s.dim_sizes ) != len( other.dim_sizes ): return False
    zipped_sizes = zip( s.dim_sizes, other.dim_sizes )
    if not reduce( lambda res, (x,y): res and (x==y), zipped_sizes ):
      return False
    return s.sub_dtype == other.sub_dtype

  def get_length( s ):
    return s.sub_dtype.get_length()*reduce( lambda p,x: p*x, s.dim_sizes, 1 )

  def get_next_dim_type( s ):
    if len( s.dim_sizes ) == 1:
      return s.sub_dtype
    return PackedArray( s.dim_sizes[1:], s.sub_dtype )

  def get_dim_sizes( s ):
    return s.dim_sizes

  def get_sub_dtype( s ):
    return s.sub_dtype

  def __call__( s, obj ):
    """Return if obj can be cast into type `s`."""
    return s == obj

  def __str__( s ):
    return 'PackedArray{} of {}'.format( s.dim_sizes, s.sub_dtype )

def _get_rtlir_dtype_struct( obj ):

  # Vector field
  if isinstance( obj, pymtl.Bits ):
    return Vector( obj.nbits )

  # PackedArray field
  elif isinstance( obj, list ):
    assert len( obj ) > 0, 'list length should be greater than 0!'
    ref_type = _get_rtlir_dtype_struct( obj[0] )
    assert\
      reduce(lambda res,i:res and (_get_rtlir_dtype_struct(i)==ref_type),obj),\
      'all elements of array {} must have the same type {}!'.format(
          obj, ref_type )
    dim_sizes = []
    while isinstance( obj, list ):
      assert len( obj ) > 0, 'list length should be greater than 0!'
      dim_sizes.append( len( obj ) )
      obj = obj[0]
    return PackedArray( dim_sizes, _get_rtlir_dtype_struct( obj ) )

  # Struct field
  elif hasattr( obj, '__name__' ) and not obj.__name__ in dir( __builtin__ ):
    # Collect all fields of the struct object
    all_properties = {}
    static_members = collect_objs( obj, object, True )
    # Infer the type of each field from the type instance
    try:
      type_instance = obj()
    except TypeError:
      assert False, \
        '__init__() of supposed struct {} should take 0 argument ( you can \
        achieve this by adding default values to your arguments )!'.format(
          obj.__name__ )
    fields = collect_objs( type_instance, object, grouped = True )
    static_member_names = map(lambda x: x[0], static_members)
    for name, field in fields:
      # Exclude the static members of the type instance
      if name not in static_member_names:
        all_properties[ name ] = _get_rtlir_dtype_struct( field )

    # Use user-provided pack order
    pack_order = []
    if hasattr( type_instance, '_pack_order' ):
      for field_name in type_instance._pack_order:
        assert field_name in all_properties, \
          field_name + ' is not an attribute of struct ' + obj.__name__ + '!'
        pack_order.append( field_name )

    # Generate default pack order ( sort by `repr` )
    else:
      pack_order = sorted( all_properties.keys(), key = repr )

    # Generate the property list according to pack order
    properties = []
    packed_order = []
    for field_name in pack_order:
      assert field_name in all_properties, \
        '{} is not an attirubte of struct {}!'.format( field_name, obj.__name__ )
      properties.append( ( field_name, all_properties[ field_name ] ) )
      packed_order.append( field_name )
    return Struct(obj.__name__, dict(properties), packed_order)
  
  else:
    assert False, str(obj) + ' is not allowed as a field of struct!'

def get_rtlir_dtype( obj ):
  """Return the RTLIR data type of obj."""
  try:
    if isinstance( obj, list ):
      raise RTLIRConversionError( obj,
        'array datatype object should be a field of some struct!')

    # Signals might be parameterized with different data types
    if isinstance( obj, ( pymtl_Signal, pymtl_Const ) ):
      Type = obj._dsl.Type
      # Vector data type
      if issubclass( Type, pymtl.Bits ):
        return Vector( Type.nbits )
      # Struct data type
      elif hasattr( Type, '__name__' ) and not Type.__name__ in dir(__builtin__):
        return _get_rtlir_dtype_struct( Type )
      else:
        raise RTLIRConversionError( obj,
          'cannot convert object of type {} into RTLIR!'.format(Type))

    # Python integer objects
    elif isinstance( obj, int ):
      # Following the Verilog bitwidth rule: number literals have 32 bit width
      # by default.
      return Vector( 32 )

    # PyMTL Bits objects
    elif isinstance( obj, pymtl.Bits ):
      return Vector( obj.nbits )

    else:
      raise RTLIRConversionError( obj,
        'cannot infer the data type of the given object!')
  except AssertionError as e:
    msg = '' if e.args[0] is None else e.args[0]
    raise RTLIRConversionError( obj, msg )
