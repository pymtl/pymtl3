#=========================================================================
# RTLIRType.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 31, 2019
"""RTLIR instance types and generation methods.

This file contains the definitions of RTLIR instance types and methods
that generate RTLIR instances. Each instance of the non-abstract class
listed in this module is a type instance or simply a type in the RTLIR
type system. Signal types is parameterized by data types defined in the
RTLIR data type module.
"""
from __future__ import absolute_import, division, print_function

import copy
import inspect
from functools import reduce

import pymtl

from .RTLIRDataType import *
from .utility import collect_objs


class BaseRTLIRType( object ):
  """Base abstract class for all RTLIR instance types."""
  def __ne__( s, other ):
    return not s.__eq__( other )

def _is_of_type( obj, Type ):
  assert issubclass( Type, BaseRTLIRType )
  if isinstance( obj, Type ):
    return True
  if isinstance( obj, Array ) and isinstance( obj.get_sub_type(), Type ):
    return True
  return False

class NoneType( BaseRTLIRType ):
  """Type for not yet typed RTLIR temporary variables."""
  def __eq__( s, other ):
    return type( s ) is type( other )

  def __str__( s ):
    return 'NoneType'

  def __repr__( s ):
    return 'NoneType'

class Array( BaseRTLIRType ):
  """Unpacked RTLIR array type."""
  def __init__( s, dim_sizes, sub_type, unpacked = False ):
    assert isinstance( sub_type, BaseRTLIRType )
    assert not isinstance( sub_type, Array )
    assert len( dim_sizes ) >= 1
    assert reduce( lambda s, i: s+i, dim_sizes, 0 ) > 0
    s.dim_sizes = dim_sizes
    s.sub_type = sub_type
    s.unpacked = unpacked

  def _is_unpacked( s ):
    return s.unpacked

  def __eq__( s, other ):
    if type( s ) is not type( other ): return False
    if s.dim_sizes != other.dim_sizes: return False
    return s.sub_type == other.sub_type

  def get_next_dim_type( s ):
    if len( s.dim_sizes ) == 1: return copy.copy( s.sub_type )
    _s = copy.copy( s )
    _s.dim_sizes = s.dim_sizes[1:]
    return _s

  def get_dim_sizes( s ):
    return s.dim_sizes

  def get_sub_type( s ):
    return s.sub_type

  def __call__( s, obj ):
    """Return if obj be cast into type `s`."""
    return s.__eq__( obj )

  def __str__( s ):
    return 'Array'

  def __repr__( s ):
    return 'Array{} of {}'.format( s.dim_sizes, s.sub_type )

class Signal( BaseRTLIRType ):
  """Signal abstract RTLIR instance type.
  
  A Signal can be a Port, a Wire, or a Const.
  """
  def __init__( s, dtype, unpacked = False ):
    assert isinstance( dtype, BaseRTLIRDataType )
    s.dtype = dtype
    s.unpacked = unpacked

  def __eq__( s, other ):
    if type( s ) is not type( other ): return False
    return s.dtype == other.dtype

  def is_packed_indexable( s ):
    return isinstance( s.dtype, PackedArray )

  def get_dtype( s ):
    return s.dtype

  def _is_unpacked( s ):
    return s.unpacked

class Port( Signal ):
  """Port RTLIR instance type."""
  def __init__( s, direction, dtype, unpacked = False ):
    super( Port, s ).__init__( dtype, unpacked )
    s.direction = direction

  def __eq__( s, other ):
    return super( Port, s ).__eq__( other ) and s.direction == other.direction

  def __str__( s ):
    return 'Port'

  def __repr__( s ):
    return 'Port of {}'.format( s.dtype )

  def get_direction( s ):
    return s.direction

  def get_next_dim_type( s ):
    assert s.is_packed_indexable()
    return Port( s.direction, s.dtype.get_next_dim_type(), s.unpacked )

class Wire( Signal ):
  """Wire RTLIR instance type."""
  def __init__( s, dtype, unpacked = False ):
    super( Wire, s ).__init__( dtype, unpacked )

  def __str__( s ):
    return 'Wire'

  def __repr__( s ):
    return 'Wire of {}'.format( s.dtype )

  def get_next_dim_type( s ):
    assert s.is_packed_indexable()
    return Wire( s.dtype.get_next_dim_type(), s.unpacked )

class Const( Signal ):
  """Const RTLIR instance type."""
  def __init__( s, dtype, unpacked = False ):
    super( Const, s ).__init__( dtype, unpacked )

  def __str__( s ):
    return 'Const'

  def __repr__( s ):
    return 'Const of {}'.format( s.dtype )

  def get_next_dim_type( s ):
    assert s.is_packed_indexable()
    return Const( s.dtype.get_next_dim_type(), s.unpacked )

class Interface( BaseRTLIRType ):
  """Interface RTLIR instance type."""
  def __init__( s, name, views = [] ):
    assert s._check_views( views ),\
        '{} does not belong to interface {}!'.format( views, name )
    s.name = name
    s.views = views
    s.properties = s._gen_properties( views )

  def __str__( s ):
    return 'Interface'

  def __repr__( s ):
    return 'Interface {}'.format( s.name )

  def _set_name( s, name ):
    s.name = name

  def _gen_properties( s, views ):
    _properties = {}
    for view in views:
      assert isinstance( view, InterfaceView )
      for id_, rtype in view.get_all_ports_packed():
        if isinstance( rtype, Array ):
          _properties[ id_ ] = Array( rtype.get_dim_sizes(),
            Wire( rtype.get_subcomps().get_dtype() ), rtype.unpacked )
        else:
          _properties[ id_ ] = Wire( rtype.get_dtype(), rtype.unpacked )
    return _properties

  def _check_views( s, views ):
    _properties = s._gen_properties( views )
    for view in views:
      assert isinstance( view, InterfaceView )
      props = view.get_all_ports()
      if len( props ) != len( _properties.keys() ):
        return False
      for prop_id, prop_rtype in props:
        if not prop_id in _properties: return False
        if Wire(prop_rtype.get_dtype()) != _properties[prop_id]: return False
    return True

  def get_name( s ):
    return s.name

  def get_all_views( s ):
    return s.views

  def get_all_wires( s ):
    return filter(
      lambda name_wire: isinstance( name_wire[1], Wire ),
      s.properties.iteritems()
    )

  def get_all_wires_packed( s ):
    return filter(
      lambda id__t:\
        ( isinstance( id__t[1], Wire ) and not id__t[1]._is_unpacked() ) or\
        ( isinstance( id__t[1], Array ) and isinstance( id__t[1].get_sub_type(), Wire )\
          and not id__t[1]._is_unpacked() ),
      s.properties.iteritems()
    )

  def can_add_view( s, view ):
    return s._check_views( s.views + [ view ] )

  def add_view( s, view ):
    if s.can_add_view( view ):
      s.views.append( view )
      s.properties = s._gen_properties( s.views )

class InterfaceView( BaseRTLIRType ):
  """RTLIR instance type for a view of an interface."""
  def __init__( s, name, properties, unpacked = False ):
    s.name = name
    s.interface = None
    s.properties = properties
    s.unpacked = unpacked

    # Sanity check
    for name, rtype in properties.iteritems():
      assert isinstance( name, str ) and _is_of_type( rtype, Port )

  def __str__( s ):
    return 'InterfaceView'

  def __repr__( s ):
    return 'InterfaceView {}'.format( s.name )

  def _set_interface( s, interface ):
    s.interface = interface

  def _is_unpacked( s ):
    return s.unpacked

  def __eq__( s, other ):
    return type(s) is type(other) and s.name == other.name

  def get_name( s ):
    return s.name

  def get_interface( s ):
    if s.interface is None:
      assert False, 'internal error: {} has no interface!'.format( s )
    return s.interface

  def get_input_ports( s ):
    return filter(
      lambda id__port: id__port[1].direction == 'input',
      s.properties.iteritems()
    )

  def get_output_ports( s ):
    return filter(
      lambda id__port1: id__port1[1].direction == 'output',
      s.properties.iteritems()
    )

  def has_property( s, p ):
    return p in s.properties

  def get_property( s, p ):
    return s.properties[ p ]

  def get_all_ports( s ):
    return filter(
      lambda name_port: isinstance( name_port[1], Port ),
      s.properties.iteritems()
    )

  def get_all_ports_packed( s ):
    return filter(
      lambda id__t2:\
        ( isinstance( id__t2[1], Port ) and not id__t2[1]._is_unpacked() ) or\
        ( isinstance( id__t2[1], Array ) and isinstance( id__t2[1].get_sub_type(), Port )\
          and not id__t2[1]._is_unpacked() ),
      s.properties.iteritems()
    )

class Component( BaseRTLIRType ):
  """RTLIR instance type for a component."""
  def __init__( s, obj, properties, unpacked = False ):
    s.name = obj.__class__.__name__
    s.argspec = inspect.getargspec( getattr( obj, 'construct' ) )
    s.params = s._gen_parameters( obj )
    s.properties = properties
    s.unpacked = unpacked

  def _gen_parameters( s, obj ):
    defaults = s.argspec.defaults if s.argspec.defaults else ()
    # The non-keyword parameters are indexed by an empty string
    ret = { '' : obj._dsl.args }
    default_len = len(s.argspec.args[1:])-len(ret[''])
    assert default_len <= len( defaults ),\
      'varargs are not allowed at construct() of {}!'.format( obj )
    if not default_len == 0:
      ret[''] = ret[''] + defaults[-default_len:]
    kwargs = obj._dsl.kwargs.copy()
    if 'elaborate' in obj._dsl.param_dict:
      kwargs.update( {
        x:y for x, y in obj._dsl.param_dict['elaborate'].iteritems() if x
      } )
    ret.update( kwargs )
    return ret

  def _is_unpacked( s ):
    return s.unpacked

  def __eq__( s, other ):
    if type( s ) is type( other ): return False
    if s.name != other.name or s.params != other.params: return False
    return True

  def __str__( s ):
    return 'Component'

  def __repr__( s ):
    return 'Component {}'.format( s.name )

  def get_name( s ):
    return s.name

  def get_params( s ):
    return s.params

  def get_argspec( s ):
    return s.argspec

  def get_ports( s ):
    return filter(
      lambda id__port3: isinstance( id__port3[1], Port ),
      s.properties.iteritems()
    )

  def get_ports_packed( s ):
    return filter(
      lambda id__t4:\
        ( isinstance( id__t4[1], Port ) and not id__t4[1]._is_unpacked() ) or\
        ( isinstance( id__t4[1], Array ) and isinstance( id__t4[1].get_sub_type(), Port )\
          and not id__t4[1]._is_unpacked() ),
      s.properties.iteritems()
    )

  def get_wires( s ):
    return filter(
      lambda id__wire: isinstance( id__wire[1], Wire ),
      s.properties.iteritems()
    )

  def get_wires_packed( s ):
    return filter(
      lambda id__t5:\
        ( isinstance( id__t5[1], Wire ) and not id__t5[1]._is_unpacked() ) or\
        ( isinstance( id__t5[1], Array ) and isinstance( id__t5[1].get_sub_type(), Wire )\
          and not id__t5[1]._is_unpacked() ),
      s.properties.iteritems()
    )

  def get_consts( s ):

    return filter(
      lambda id__const: isinstance( id__const[1], Const ),
      s.properties.iteritems()
    )

  def get_consts_packed( s ):
    return filter(
      lambda id__t6:\
        ( isinstance( id__t6[1], Const ) and not id__t6[1]._is_unpacked() ) or\
        ( isinstance( id__t6[1], Array ) and isinstance( id__t6[1].get_sub_type(), Const )\
          and not id__t6[1]._is_unpacked() ),
      s.properties.iteritems()
    )

  def get_ifc_views( s ):
    return filter(
      lambda id__ifc: isinstance( id__ifc[1], InterfaceView ),
      s.properties.iteritems()
    )

  def get_ifc_views_packed( s ):
    return filter(
      lambda id__t7:\
        ( isinstance( id__t7[1], InterfaceView ) and not id__t7[1]._is_unpacked() ) or\
        ( isinstance( id__t7[1], Array ) and isinstance( id__t7[1].get_sub_type(),InterfaceView )\
          and not id__t7[1]._is_unpacked() ),
      s.properties.iteritems()
    )

  def get_ifcs( s ):
    return filter(
      lambda id__ifc8: isinstance( id__ifc8[1], Interface ),
      s.properties.iteritems()
    )

  def get_subcomps( s ):
    return filter(
      lambda id__subcomp: isinstance( id__subcomp[1], Component ),
      s.properties.iteritems()
    )

  def get_subcomps_packed( s ):
    return filter(
      lambda id__t9:\
        ( isinstance( id__t9[1], Component ) and not id__t9[1]._is_unpacked() ) or\
        ( isinstance( id__t9[1], Array ) and isinstance( id__t9[1].get_sub_type(), Component )\
          and not id__t9[1]._is_unpacked() ),
      s.properties.iteritems()
    )

  def has_property( s, p ):
    return p in s.properties

  def get_property( s, p ):
    return s.properties[ p ]

  def get_all_properties( s ):
    return s.properties

def is_rtlir_convertible( obj ):
  """Return if `obj` can be converted into an RTLIR instance."""
  pymtl_constructs = (
    pymtl.InPort, pymtl.OutPort, pymtl.Wire, pymtl.Bits, pymtl.Interface,
    pymtl.Component
  )
  if isinstance( obj, list ):
    while isinstance( obj, list ):
      assert len( obj ) > 0
      obj = obj[0]
    return is_rtlir_convertible( obj )
  elif isinstance( obj, pymtl_constructs ):
    return True
  elif isinstance( obj, int ):
    return True
  else: return False

def get_rtlir( obj ):
  """Return an RTLIR instance corresponding to `obj`."""
  def is_rtlir_ifc_convertible( obj ):
    pymtl_ports = ( pymtl.InPort, pymtl.OutPort )
    if isinstance( obj, list ):
      while isinstance( obj, list ):
        assert len( obj ) > 0
        obj = obj[0]
      return is_rtlir_ifc_convertible( obj )
    elif isinstance( obj, pymtl_ports ): return True
    else: return False

  def unpack( id_, Type ):
    if not isinstance( Type, Array ): return [ ( id_, Type ) ]
    ret = []
    for idx in xrange( Type.get_dim_sizes()[0] ):
      ret.append( ( id_+'[{}]'.format(idx), Type.get_next_dim_type() ) )
      ret.extend(unpack(id_+'[{}]'.format( idx ), Type.get_next_dim_type()))
    return ret

  def add_packed_instances( id_, Type, properties ):
    assert isinstance( Type, Array )
    for _id, _Type in unpack( id_, Type ):
      assert hasattr( _Type, 'unpacked' )
      _Type.unpacked = True
      properties[ _id ] = _Type

  # A list of instances
  if isinstance( obj, list ):
    assert len( obj ) > 0
    ref_type = get_rtlir( obj[0] )
    assert\
      reduce( lambda res,i: res and (get_rtlir(i)==ref_type),obj ),\
      'all elements of array {} must have the same type {}!'.format(
        obj, ref_type )
    dim_sizes = []
    while isinstance( obj, list ):
      assert len( obj ) > 0
      dim_sizes.append( len( obj ) )
      obj = obj[0]
    return Array( dim_sizes, get_rtlir( obj ) )

  # A Port instance
  elif isinstance( obj, ( pymtl.InPort, pymtl.OutPort ) ):
    if isinstance( obj, pymtl.InPort ):
      return Port( 'input', get_rtlir_dtype( obj ) )
    elif isinstance( obj, pymtl.OutPort ):
      return Port( 'output', get_rtlir_dtype( obj ) )
    else: assert False

  # A Wire instance
  elif isinstance( obj, pymtl.Wire ):
    return Wire( get_rtlir_dtype( obj ) )

  # A Constant instance
  elif isinstance( obj, ( int, pymtl.Bits ) ):
    return Const( get_rtlir_dtype( obj ) )

  # An Interface view instance
  elif isinstance( obj, pymtl.Interface ):
    properties = {}
    for _id, _obj in collect_objs( obj, object, True ):
      if not is_rtlir_ifc_convertible( _obj ): continue
      _obj_type = get_rtlir( _obj )
      properties[ _id ] = _obj_type
      if not _is_of_type( _obj_type, Port ):
        assert False,\
          "RTLIR Interface type can only include Port objects!"
      if isinstance( _obj_type, Array ):
        add_packed_instances( _id, _obj_type, properties )
    return InterfaceView( obj.__class__.__name__, properties )

  # A Component instance
  elif isinstance( obj, pymtl.Component ):
    # Collect all attributes of `obj`
    properties = {}
    for _id, _obj in collect_objs( obj, object, True ):
      # Untranslatable attributes will be ignored
      if not is_rtlir_convertible( _obj ): continue
      _obj_type = get_rtlir( _obj )
      properties[ _id ] = _obj_type
      if isinstance( _obj_type, Array ):
        add_packed_instances( _id, _obj_type, properties )
    return Component( obj, properties )

  # Cannot convert `obj` into RTLIR representation
  else:
    assert False, 'cannot convert {} into RTLIR!'.format( obj )
