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

from .utility import collect_objs


class BaseRTLIRDataType( object ):
  """Base abstract RTLIR data type class."""

  def __new__( cls, *args, **kwargs ):
    return super( BaseRTLIRDataType, cls ).__new__( cls )

  def __init__( s ):
    super( BaseRTLIRDataType, s ).__init__()

class Vector( BaseRTLIRDataType ):
  """RTLIR data type class for vector type."""

  def __init__( s, nbits ):
    assert nbits > 0
    super( Vector, s ).__init__()
    s.nbits = nbits

  def get_length( s ):
    return s.nbits

  def __eq__( s, other ):
    return ( type(s) == type(other) ) and ( s.nbits == other.nbits )

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __call__( s, obj ):
    """Return if type `obj` be cast into type `s`."""
    if isinstance( obj, Vector ): return True
    if isinstance( obj, Bool ): return True
    return False

  def __str__( s ):
    return 'Vector{}'.format( s.nbits )

class Struct( BaseRTLIRDataType ):
  """RTLIR data type class for struct type."""

  def __init__( s, name, properties ):
    assert len( properties ) > 0
    super( Struct, s ).__init__()
    s.name = name
    s.properties = properties

  def __eq__( s, u ):
    if type( s ) != type( u ): return False
    if s.name != u.name: return False
    return True

  def __ne__( s, other ):
    return not s.__eq__( other )

  def get_name( s ):
    return s.name

  def get_pack_order( s ):
    return map( lambda x: x[0], s.properties )

  def get_length( s ):
    return reduce( lambda s, dtype: s+dtype[1].get_length(), s.properties, 0 )

  def has_property( s, p ):
    return p in s.get_pack_order()

  def get_property( s, p ):
    assert s.has_property( p )
    for name, prop in s.properties:
      if name == p: return prop

  def get_all_properties( s ):
    return s.properties

  def __call__( s, obj ):
    """Return if obj be cast into type `s`."""
    if isinstance( obj, Struct ) and s == obj:
      return True
    return False

  def __str__( s ):
    return 'Struct'

class Bool( BaseRTLIRDataType ):
  """RTLIR data type class for struct type.
  
  Bool data type cannot be instantiated explicitly. It can only appear as
  the result of comparisons.
  """

  def __init__( s ):
    super( Bool, s ).__init__()

  def __eq__( s, other ):
    return type( s ) == type( other )

  def __ne__( s, other ):
    return not s.__eq__( other )

  def get_length( s ):
    return 1

  def __call__( s, obj ):
    """Return if obj be cast into type `s`."""
    if isinstance( obj, ( Bool, Vector ) ):
      return True
    return False

  def __str__( s ):
    return 'Bool'

class PackedArray( BaseRTLIRDataType ):
  """RTLIR data type class for packed array type."""

  def __init__( s, dim_sizes, sub_dtype ):
    assert isinstance( sub_dtype, BaseRTLIRDataType )
    assert not isinstance( sub_dtype, PackedArray )
    assert len( dim_sizes ) >= 1
    assert reduce( lambda s, i: s+i, dim_sizes, 0 ) > 0
    super( PackedArray, s ).__init__()
    s.dim_sizes = dim_sizes
    s.sub_dtype = sub_dtype

  def __eq__( s, other ):
    if type( s ) != type( other ): return False
    if len( s.dim_sizes ) != len( other.dim_sizes ): return False
    zipped_sizes = zip( s.dim_sizes, other.dim_sizes )
    if not reduce( lambda res, (x,y): res and (x==y), zipped_sizes ):
      return False
    return s.sub_dtype == other.sub_dtype

  def __ne__( s, other ):
    return not s.__eq__( other )

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
    return s.__eq__( obj )

  def __str__( s ):
    return 'PackedArray'

def _get_rtlir_dtype_struct( obj ):

  # Vector field
  if isinstance( obj, pymtl.Bits ):
    return Vector( obj.nbits )

  # PackedArray field
  elif isinstance( obj, list ):
    assert len( obj ) > 0
    ref_type = _get_rtlir_dtype_struct( obj[0] )
    assert\
      reduce(lambda res,i:res and (_get_rtlir_dtype_struct(i)==ref_type),obj),\
      'all elements of array {} must have the same type {}!'.format(
          obj, ref_type )
    dim_sizes = []
    while isinstance( obj, list ):
      assert len( obj ) > 0
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
      assert False, '__init__() of {} should take 0 argument ( you can\
        achieve this by adding default values to your arguments )!'.format(
          obj.__name__
      )
    except: raise
    fields = collect_objs( type_instance, object, grouped = True )
    for name, field in fields:
      # Exclude the static members of the type instance
      if name in map( lambda x: x[0], static_members ): continue
      all_properties[ name ] = _get_rtlir_dtype_struct( field )

    # Use user-provided pack order
    pack_order = []
    if '_pack_order' in type_instance.__dict__:
      for field_name in type_instance._pack_order:
        assert field_name in all_properties, field_name + ' is not an \
attribute of struct ' + obj.__name__ + '!'
        pack_order.append( field_name )

    # Generate default pack order ( sort by `repr` )
    else:
      pack_order = sorted( all_properties.keys(), key = repr )

    # Generate the property list according to pack order
    properties = []
    for field_name in pack_order:
      assert field_name in all_properties
      properties.append( ( field_name, all_properties[ field_name ] ) )
    return Struct( obj.__name__, properties )
  
  else: assert False, str(obj) + ' is not allowed as a field of struct!'

def get_rtlir_dtype( obj ):
  """Return the RTLIR data type of obj."""

  assert not isinstance( obj, list ),\
      'internal error: encountered non-struct field array object {}!'.format( obj )

  # Signals might be parameterized with different data types
  if isinstance( obj, ( pymtl_Signal, pymtl_Const ) ):
    Type = obj._dsl.Type
    # Vector data type
    if issubclass( Type, pymtl.Bits ):
      return Vector( Type.nbits )
    # Struct data type
    elif hasattr( Type, '__name__' ) and not Type.__name__ in dir(__builtin__):
      return _get_rtlir_dtype_struct( Type )
    else: assert False, 'cannot convert {} of type {} into RTLIR!'.format(
            obj, Type
          )

  # Python integer objects
  elif isinstance( obj, int ):
    # Following the Verilog bitwidth rule: number literals have 32 bit width
    # by default.
    return Vector( 32 )

  # PyMTL Bits objects
  elif isinstance( obj, pymtl.Bits ):
    return Vector( obj.nbits )

  else: assert False, 'cannot infer data type for object ' + str(obj) + '!'
