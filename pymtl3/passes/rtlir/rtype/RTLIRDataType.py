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

import inspect
from functools import reduce

import pymtl3.dsl as dsl
from pymtl3.datatypes import Bits, BitStruct

from ..errors import RTLIRConversionError
from ..util.utility import collect_objs


class BaseRTLIRDataType( object ):
  """Base abstract RTLIR data type class."""
  def __ne__( s, other ):
    return not s.__eq__( other )

  def __hash__( s ):
    return hash(type(s))

class Vector( BaseRTLIRDataType ):
  """RTLIR data type class for vector type."""
  def __init__( s, nbits ):
    assert nbits > 0, 'vector bitwidth should be a positive integer!'
    s.nbits = nbits

  def get_length( s ):
    return s.nbits

  def __eq__( s, other ):
    return (isinstance(other, Vector) and s.nbits == other.nbits) or \
           (s.nbits == 1 and isinstance(other, Bool))

  def __hash__( s ):
    return hash((type(s), s.nbits))

  def __call__( s, obj ):
    """Return if type `obj` be cast into type `s`."""
    return isinstance( obj, ( Vector, Bool ) )

  def __str__( s ):
    return 'Vector{}'.format( s.nbits )

class Struct( BaseRTLIRDataType ):
  """RTLIR data type class for struct type."""
  def __init__( s, name, properties, packed_order, cls = None ):
    assert len( packed_order ) > 0, 'packed_order is empty!'
    s.name = name
    s.properties = properties
    s.packed_order = packed_order
    s.cls = cls
    if cls is not None:
      try:
        file_name = inspect.getsourcefile( cls )
        line_no = inspect.getsourcelines( cls )[1]
        s.file_info = "File: {file_name}, Line: {line_no}".format( **locals() )
      except IOError:
        s.file_info = "Dynamically generated class " + cls.__name__
    else:
      s.file_info = "Not available"

  def __eq__( s, u ):
    return isinstance(u, Struct) and s.name == u.name

  def __hash__( s ):
    return hash((type(s), s.name))

  def get_name( s ):
    return s.name

  def get_file_info( s ):
    return s.file_info

  def get_class( s ):
    return s.cls

  def get_pack_order( s ):
    return s.packed_order

  def get_length( s ):
    return reduce(lambda s, d: s+d.get_length(), s.properties.values(), 0)

  def has_property( s, p ):
    return p in s.properties

  def get_property( s, p ):
    return s.properties[ p ]

  def get_all_properties( s ):
    order = { key : i for i, key in enumerate(s.packed_order) }
    return sorted(s.properties.iteritems(), key = lambda x: order[x[0]])

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
    return isinstance(other, Bool) or \
           (isinstance(other, Vector) and other.nbits==1)

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
    if not reduce( lambda res, xy: res and (xy[0] == xy[1]), zipped_sizes ):
      return False
    return s.sub_dtype == other.sub_dtype

  def __hash__( s ):
    return hash((type(s), tuple(s.dim_sizes), s.sub_dtype))

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
  if isinstance( obj, Bits ):
    return Vector( obj.nbits )

  # PackedArray field
  elif isinstance( obj, list ):
    assert len( obj ) > 0, 'list length should be greater than 0!'
    ref_type = _get_rtlir_dtype_struct( obj[0] )
    assert \
      reduce(lambda res,i:res and (_get_rtlir_dtype_struct(i)==ref_type),obj, True), \
      'all elements of array {} must have the same type {}!'.format( obj, ref_type )
    dim_sizes = []
    while isinstance( obj, list ):
      assert len( obj ) > 0, 'list length should be greater than 0!'
      dim_sizes.append( len( obj ) )
      obj = obj[0]
    return PackedArray( dim_sizes, _get_rtlir_dtype_struct( obj ) )

  # Struct field
  elif isinstance( obj, BitStruct ):
    cls = obj.__class__
    all_properties = {}

    # Collect all fields of the struct object
    static_members = collect_objs( cls, object )

    # Infer the type of each field from the type instance
    try:
      type_instance = cls()
    except TypeError:
      assert False, \
        '__init__() of supposed struct {} should take 0 argument ( you can \
        achieve this by adding default values to your arguments )!'.format(
          cls.__name__ )
    fields = collect_objs( type_instance, object )
    static_member_names = map(lambda x: x[0], static_members)
    for name, field in fields:
      # Exclude the static members of the type instance
      if name not in static_member_names:
        all_properties[ name ] = _get_rtlir_dtype_struct( field )

    # Use user-provided pack order
    pack_order = []
    if hasattr( cls, "fields" ) and cls.fields != []:
      assert len(cls.fields) == len(all_properties.keys()), \
        "{}.fields does not match the attributes of its instance!". \
          format( cls.__name__ )
      for field_name, field in cls.fields:
        assert field_name in all_properties, \
          field_name + ' is not an attribute of struct ' + cls.__name__ + '!'
        pack_order.append( field_name )

    # Generate default pack order ( sort by `repr` )
    else:
      pack_order = sorted( all_properties.keys(), key = repr )

    # Generate the property list according to pack order
    properties = []
    packed_order = []
    for field_name in pack_order:
      assert field_name in all_properties, \
        '{} is not an attirubte of struct {}!'.format( field_name, cls.__name__ )
      properties.append( ( field_name, all_properties[ field_name ] ) )
      packed_order.append( field_name )
    return Struct(cls.__name__, dict(properties), packed_order, cls)

  else:
    assert False, str(obj) + ' is not allowed as a field of struct!'

def get_rtlir_dtype( obj ):
  """Return the RTLIR data type of obj."""
  try:
    assert not isinstance(obj, list), \
      'array datatype object should be a field of some struct!'

    # Signals might be parameterized with different data types
    if isinstance( obj, ( dsl.Signal, dsl.Const ) ):
      Type = obj._dsl.Type

      # Vector data type
      if issubclass( Type, Bits ):
        return Vector( Type.nbits )

      # python int object
      elif Type is int:
        return Vector( 32 )

      # Struct data type
      elif issubclass( Type, BitStruct ):
        try:
          return _get_rtlir_dtype_struct( Type() )
        except TypeError:
          assert False, \
            '__init__() of supposed struct {} should take 0 argument ( you can \
            achieve this by adding default values to your arguments )!'.format(
              Type.__name__ )

      else:
        assert False, 'cannot convert object of type {} into RTLIR!'.format(Type)

    # Python integer objects
    elif isinstance( obj, int ):
      # Following the Verilog bitwidth rule: number literals have 32 bit width
      # by default.
      return Vector( 32 )

    # PyMTL Bits objects
    elif isinstance( obj, Bits ):
      return Vector( obj.nbits )

    # PyMTL BitStruct objects
    elif isinstance( obj, BitStruct ):
      return _get_rtlir_dtype_struct( obj )

    else:
      assert False, 'cannot infer the data type of the given object!'
  except AssertionError as e:
    msg = '' if e.args[0] is None else e.args[0]
    raise RTLIRConversionError( obj, msg )
