#=========================================================================
# StructuralRTLIRSignalExpr.py
#=========================================================================
"""RTLIR signal expression class definitions and generation method."""

from __future__ import absolute_import, division, print_function

from functools import reduce

import pymtl

from ..RTLIRType import *


class BaseSignalExpr( object ):
  """Base abstract class of RTLIR signal expressions."""

  def __init__( s, rtype ):

    assert isinstance( rtype, BaseRTLIRType )
    s.rtype = rtype

  def get_rtype( s ):

    return s.rtype

  def __eq__( s, other ):
    
    return type(s) == type(other) and s.rtype == other.rtype

  def __ne__( s, other ): return not s.__eq__( other )

class _Index( BaseSignalExpr ):

  def __init__( s, index_base, index, rtype ):

    super( _Index, s ).__init__( rtype )
    s.index = index
    s.base = index_base

  def __eq__( s, other ):

    return super( _Index, s ).__eq__( other ) and\
           s.index == other.index and\
           s.base == other.base

  def get_index( s ): return s.index

  def get_base( s ): return s.base

  @staticmethod
  def is_port_index( index_base, index ):

    try:

      base_rtype = index_base.get_rtype()
      assert isinstance( base_rtype, Array )
      assert isinstance( base_rtype.get_sub_type(), Port )

    except: return None

    return PortIndex

  @staticmethod
  def is_wire_index( index_base, index ):

    try:

      base_rtype = index_base.get_rtype()
      assert isinstance( base_rtype, Array )
      assert isinstance( base_rtype.get_sub_type(), Wire )

    except: return None

    return WireIndex

  @staticmethod
  def is_const_index( index_base, index ):

    try:

      base_rtype = index_base.get_rtype()
      assert isinstance( base_rtype, Array )
      assert isinstance( base_rtype.get_sub_type(), Const )

    except: return None

    return ConstIndex

  @staticmethod
  def is_ifc_view_index( index_base, index ):

    try:

      base_rtype = index_base.get_rtype()
      assert isinstance( base_rtype, Array )
      assert isinstance( base_rtype.get_sub_type(), InterfaceView )

    except: return None

    return InterfaceViewIndex

  @staticmethod
  def is_component_index( index_base, index ):

    try:

      base_rtype = index_base.get_rtype()
      assert isinstance( base_rtype, Array )
      assert isinstance( base_rtype.get_sub_type(), Component )

    except: return None

    return ComponentIndex

  @staticmethod
  def is_packed_index( index_base, index ):

    try:

      base_rtype = index_base.get_rtype()
      assert isinstance( base_rtype, ( Port, Wire ) )
      dtype = base_rtype.get_dtype()
      assert isinstance( dtype, PackedArray )

    except: return None

    return PackedIndex

  @staticmethod
  def is_bit_selection( index_base, index ):

    try:

      base_rtype = index_base.get_rtype()
      assert isinstance( base_rtype, ( Port, Wire ) )
      dtype = base_rtype.get_dtype()
      assert isinstance( dtype, Vector )

    except: return None

    return BitSelection

class UnpackedIndex( _Index ):

  def __init__( s, index_base, index ):

    base_rtype = index_base.get_rtype()
    rtype = base_rtype.get_next_dim_type()
    super( UnpackedIndex, s ).__init__( index_base, index, rtype )


class _Slice( BaseSignalExpr ):

  def __init__( s, slice_base, start, stop ):

    base_rtype = slice_base.get_rtype()
    dtype = base_rtype.get_dtype()

    if isinstance( base_rtype, Port ):

      rtype = Port( base_rtype.get_direction(), Vector( stop-start ) )

    elif isinstance( base_rtype, Wire ): rtype = Wire( Vector( stop-start ) )

    else: assert False

    super( _Slice, s ).__init__( rtype )
    s.base = slice_base
    s.slice = ( start, stop )

  def __eq__( s, other ):

    return super( _Slice, s ).__eq__( other ) and\
           s.start == other.start and s.stop == other.stop and\
           s.slice_base == other.slice_base

  def get_slice( s ): return s.slice

  def get_base( s ): return s.base

  @staticmethod
  def is_part_selection( slice_base, start, stop ):

    try:

      base_rtype = slice_base.get_rtype()
      assert isinstance( base_rtype, ( Port, Wire ) )
      dtype = base_rtype.get_dtype()
      assert isinstance( dtype, Vector )
      assert isinstance( start, int ) and isinstance( stop, int )

    except: return None

    return PartSelection

class _Attribute( BaseSignalExpr ):

  def __init__( s, attr_base, attr, rtype ):

    super( _Attribute, s ).__init__( rtype )
    s.attr = attr
    s.base = attr_base

  def __eq__( s, other ):

    return super( _Attribute, s ).__eq__( other ) and\
           s.attr == other.attr and\
           s.attr_base == other.attr_base

  def get_base( s ): return s.base

  def get_attr( s ): return s.attr

  @staticmethod
  def is_cur_comp_attr( attr_base, attr ):

    try:

      assert isinstance( attr_base, CurComp )
      assert attr_base.get_rtype().has_property( attr )

    except: return None

    return CurCompAttr

  @staticmethod
  def is_subcomp_attr( attr_base, attr ):

    try:

      assert not isinstance( attr_base, CurComp )
      assert isinstance( attr_base.get_rtype(), Component )
      assert attr_base.get_rtype().has_property( attr )

    except: return None

    return SubCompAttr

  @staticmethod
  def is_interface_attr( attr_base, attr ):

    try:

      assert isinstance( attr_base.get_rtype(), InterfaceView )
      assert attr_base.get_rtype().has_property( attr )

    except: return None

    return InterfaceAttr

  @staticmethod
  def is_struct_attr( attr_base, attr ):

    try:

      rtype = attr_base.get_rtype()
      assert isinstance( rtype, Signal )
      dtype = rtype.get_dtype()
      assert isinstance( dtype, Struct ) and dtype.has_property( attr )

    except: return None

    return StructAttr

class ConstInstance( BaseSignalExpr ):

  def __init__( s, obj, value ):

    super( ConstInstance, s ).__init__(Const(get_rtlir_dtype( obj )))
    s.value = value

  def __eq__( s, other ):

    return super( ConstInstance, s ).__eq__( other ) and s.value == other.value

  def get_value( s ): return s.value

class CurComp( BaseSignalExpr ):
  """ Can only be the root of a signal expression  """

  def __init__( s, comp, comp_id ):
    
    super( CurComp, s ).__init__(comp._pass_structural_rtlir_gen.rtlir_type)
    s.comp_id = comp_id

  def __eq__( s, other ):

    return super( CurComp, s ).__eq__( other ) and\
           s.comp_id == other.comp_id

  def get_component_id( s ): return s.comp_id

  @staticmethod
  def is_cur_comp( comp, comp_id ):

    try:

      assert comp_id == comp._dsl.my_name

    except: return None

    return CurComp

class PortIndex( UnpackedIndex ): pass

class WireIndex( UnpackedIndex ): pass

class ConstIndex( UnpackedIndex ): pass

class InterfaceViewIndex( UnpackedIndex ): pass

class ComponentIndex( UnpackedIndex ): pass

class PackedIndex( _Index ):

  def __init__( s, index_base, index ):

    base_rtype = index_base.get_rtype()
    dtype = base_rtype.get_dtype()

    if isinstance( base_rtype, Port ):

      rtype = Port( base_rtype.get_direction(),
                    dtype.get_next_dim_type() )

    elif isinstance( base_rtype, Wire ):

      rtype = Wire( dtype.get_next_dim_type() )

    else: assert False

    super( PackedIndex, s ).__init__( index_base, index, rtype )

class BitSelection( _Index ):

  def __init__( s, index_base, index ):

    base_rtype = index_base.get_rtype()
    dtype = base_rtype.get_dtype()

    if isinstance( base_rtype, Port ):

      rtype = Port( base_rtype.get_direction(), Vector( 1 ) )

    elif isinstance( base_rtype, Wire ):

      rtype = Wire( Vector( 1 ) )

    else: assert False

    super( BitSelection, s ).__init__( index_base, index, rtype )

class PartSelection( _Slice ): pass

class CurCompAttr( _Attribute ):

  def __init__( s, attr_base, attr ):

    rtype = attr_base.get_rtype().get_property( attr )
    super( CurCompAttr, s ).__init__( attr_base, attr, rtype )

class SubCompAttr( _Attribute ):

  def __init__( s, attr_base, attr ):

    rtype = attr_base.get_rtype().get_property( attr )
    super( SubCompAttr, s ).__init__( attr_base, attr, rtype )

class InterfaceAttr( _Attribute ):

  def __init__( s, attr_base, attr ):

    rtype = attr_base.get_rtype().get_property( attr )
    super( InterfaceAttr, s ).__init__( attr_base, attr, rtype )

class StructAttr( _Attribute ):
  
  def __init__( s, attr_base, attr ):

    base_rtype = attr_base.get_rtype()
    dtype = base_rtype.get_dtype()

    if isinstance( base_rtype, Port ):

      rtype = Port( base_rtype.get_direction(), dtype.get_property( attr ) )

    elif isinstance( base_rtype, Wire ):
      
      rtype = Wire( dtype.get_property( attr ) )

    else: assert False

    super( StructAttr, s ).__init__( attr_base, attr, rtype )

signal_expr_classes = {
    'Attr' :  [ _Attribute.is_cur_comp_attr, _Attribute.is_subcomp_attr,
                _Attribute.is_interface_attr, _Attribute.is_struct_attr ],
    'Index' : [ _Index.is_packed_index, _Index.is_bit_selection,
                _Index.is_port_index,   _Index.is_wire_index,
                _Index.is_const_index,  _Index.is_ifc_view_index,
                _Index.is_component_index ],
    'Slice' : [ _Slice.is_part_selection ],
    'Base'  : [ CurComp.is_cur_comp ]
}

def gen_signal_expr( cur_component, signal ):
  """Return an RTLIR signal expression for the given signal."""

  def get_next_op( expr, cur_pos, my_name, full_name ):

    if not expr[cur_pos:]: return ( 'Done', '' ), 0

    pos = len( expr )
    dot_pos = expr.find( '.', cur_pos+1 )
    lb_pos  = expr.find( '[', cur_pos+1 )
    pos = dot_pos if dot_pos != -1 and dot_pos < pos else pos
    pos =  lb_pos if  lb_pos != -1 and  lb_pos < pos else pos

    # Attribute operation

    if expr[cur_pos] == '.': return ( 'Attr', expr[cur_pos+1:pos] ), pos

    # Index or slice operation

    elif expr[cur_pos] == '[':

      rb_pos = expr.find( ']', cur_pos )
      colon_pos = expr.find( ':', cur_pos )
      assert rb_pos != -1 and pos == rb_pos+1

      if cur_pos < colon_pos < rb_pos:

        start = int( expr[cur_pos+1:colon_pos] )
        stop  = int( expr[colon_pos+1:rb_pos] )
        return ( 'Slice', start, stop ), pos

      else: return ( 'Index', int(expr[cur_pos+1:rb_pos]) ), pos

    # The current component ( base of attribute )

    else:

      base_pos = expr.find( full_name )
      assert base_pos >= 0
      return ( 'Base', my_name ), base_pos + len( full_name )

    # else: return ( 'Base', expr[cur_pos:pos] ), pos

  def get_cls_inst( func_list, cur_node, ops ):

    classes = map( lambda f: f( cur_node, *ops ), func_list )
    assert reduce( lambda r, c: r + (1 if c else 0), classes, 0 ) == 1,\
      'internal error: not unique class {}!'.format( classes )
    for cls in classes:
      if cls:
        return cls( cur_node, *ops )
    assert False

  try:

    expr = signal._dsl.full_name
    base_comp = signal

  except AttributeError:

    assert hasattr( signal._dsl, 'const' ), '{} is not supported!'.format(signal)
    assert isinstance( signal._dsl.const, int ),\
        '{} is not an integer const!'.format( signal._dsl.const )
    return ConstInstance( signal, signal._dsl.const )

  while hasattr( base_comp._dsl, 'parent_obj' ) and base_comp._dsl.parent_obj:

    base_comp = base_comp._dsl.parent_obj
    if base_comp == cur_component: break

  assert isinstance( base_comp, pymtl.Component ) and base_comp == cur_component
  full_name = base_comp._dsl.full_name
  my_name = base_comp._dsl.my_name
  assert expr.find( full_name ) >= 0

  # Start from the base component and process one operation per iteration

  cur_pos, cur_node = 0, base_comp

  while cur_pos < len( expr ):

    op, next_pos = get_next_op( expr, cur_pos, my_name, full_name )
    if op[0] == 'Done': break

    cur_node = get_cls_inst( signal_expr_classes[ op[0] ], cur_node, op[1:] )
    cur_pos = next_pos

  return cur_node
