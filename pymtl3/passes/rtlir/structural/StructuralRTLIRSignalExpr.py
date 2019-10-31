#=========================================================================
# StructuralRTLIRSignalExpr.py
#=========================================================================
"""RTLIR signal expression class definitions and generation method."""


import pymtl3.dsl as dsl
from pymtl3.datatypes import Bits, is_bitstruct_inst
from pymtl3.passes.rtlir.errors import RTLIRConversionError
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.rtlir.rtype import RTLIRType as rt


class BaseSignalExpr:
  """Base abstract class of RTLIR signal expressions."""
  def __init__( s, rtype ):
    assert isinstance( rtype, rt.BaseRTLIRType ), f"non-RTLIR type {rtype} encountered!"
    s.rtype = rtype

  def get_rtype( s ):
    return s.rtype

  def __eq__( s, other ):
    return type(s) is type(other) and s.rtype == other.rtype

  def __ne__( s, other ):
    return not s.__eq__( other )

  def __hash__( s ):
    return hash((type(s), s.rtype))

#-------------------------------------------------------------------------
# Internal signal expression classes
#-------------------------------------------------------------------------

class _Index( BaseSignalExpr ):
  """Base IR class for all index signal operations.

  This class implements a series of static methods that is called to tell
  if the current index signal operation is indexing on a signal of packed
  data type array or a bit selection.
  """
  def __init__( s, index_base, index, rtype ):
    super().__init__( rtype )
    s.index = index
    s.base = index_base

  def __eq__( s, other ):
    return type(s) is type(other) and s.rtype == other.rtype and\
           s.index == other.index and \
           s.base == other.base

  def __hash__( s ):
    return hash((type(s), s.rtype, s.index, s.base))

  def get_index( s ):
    return s.index

  def get_base( s ):
    return s.base

  @staticmethod
  def is_packed_index( index_base, index ):
    """Return PackedIndex constructor if the given index base is a signal of packed data type."""
    base_rtype = index_base.get_rtype()
    if isinstance(base_rtype, (rt.Port, rt.Wire)) and \
       isinstance(base_rtype.get_dtype(), rdt.PackedArray):
      return PackedIndex
    else:
      return None

  @staticmethod
  def is_bit_selection( index_base, index ):
    """Return BitSelection constructor if the given index base is a vector signal."""
    base_rtype = index_base.get_rtype()
    if isinstance(base_rtype, (rt.Port, rt.Wire)) and \
       isinstance(base_rtype.get_dtype(), rdt.Vector):
      return BitSelection
    else:
      return None

class _UnpackedIndex( _Index ):
  """Base IR class for all index signal operations on unpacked arrays.

  Unpacked indexing operations include indexing on a port array, a wire
  array, a const array, an interface array, and a component array. This class
  implements a series of static methods to check if the given signal operation
  is one of them.
  """
  def __init__( s, index_base, index ):
    base_rtype = index_base.get_rtype()
    rtype = base_rtype.get_next_dim_type()
    super().__init__( index_base, index, rtype )

  @staticmethod
  def is_port_index( index_base, index ):
    """Return PortIndex constructor if the given index base is a port array."""
    base_rtype = index_base.get_rtype()
    if isinstance(base_rtype, rt.Array) and \
       isinstance(base_rtype.get_sub_type(), rt.Port):
      return PortIndex
    else:
      return None

  @staticmethod
  def is_wire_index( index_base, index ):
    """Return WireIndex constructor if the given index base is a wire array."""
    base_rtype = index_base.get_rtype()
    if isinstance(base_rtype, rt.Array) and \
       isinstance(base_rtype.get_sub_type(), rt.Wire):
      return WireIndex
    else:
      return None

  @staticmethod
  def is_const_index( index_base, index ):
    """Return ConstIndex constructor if the given index base is a const array."""
    base_rtype = index_base.get_rtype()
    if isinstance(base_rtype, rt.Array) and \
       isinstance(base_rtype.get_sub_type(), rt.Const):
      return ConstIndex
    else:
      return None

  @staticmethod
  def is_ifc_view_index( index_base, index ):
    """Return InterfaceViewIndex constructor if the given index base is an interface array."""
    base_rtype = index_base.get_rtype()
    if isinstance(base_rtype, rt.Array) and \
       isinstance(base_rtype.get_sub_type(), rt.InterfaceView):
      return InterfaceViewIndex
    else:
      return None

  @staticmethod
  def is_component_index( index_base, index ):
    """Return ComponentIndex constructor if the given index base is component array."""
    base_rtype = index_base.get_rtype()
    if isinstance(base_rtype, rt.Array) and \
       isinstance(base_rtype.get_sub_type(), rt.Component):
      return ComponentIndex
    else:
      return None

class _Slice( BaseSignalExpr ):
  """Base IR class for all slicing signal operations.

  This class implements a single static method which checks if the given
  signal operation is slicing a vector signal (a.k.a. a part selection).
  """
  def __init__( s, slice_base, start, stop ):
    base_rtype = slice_base.get_rtype()
    dtype = base_rtype.get_dtype()
    if isinstance( base_rtype, rt.Port ):
      rtype = rt.Port( base_rtype.get_direction(), rdt.Vector( stop-start ) )
    elif isinstance( base_rtype, rt.Wire ):
      rtype = rt.Wire( rdt.Vector( stop-start ) )
    else:
      assert False, f"unrecognized signal type {base_rtype} for slicing"
    super().__init__( rtype )
    s.base = slice_base
    s.slice = ( start, stop )

  def __eq__( s, other ):
    return type(s) is type(other) and s.rtype == other.rtype and \
           s.slice == other.slice and s.base == other.base

  def __hash__( s ):
    return hash((type(s), s.rtype, s.slice, s.base))

  def get_slice( s ):
    return s.slice

  def get_base( s ):
    return s.base

  @staticmethod
  def is_part_selection( slice_base, start, stop ):
    """Return PartSelection constructor if the given index base is a vector signal."""
    base_rtype = slice_base.get_rtype()
    if isinstance(base_rtype, (rt.Port, rt.Wire)) and \
       isinstance(base_rtype.get_dtype(), rdt.Vector) and \
       isinstance(start, int) and isinstance(stop, int):
      return PartSelection
    else:
      return None

class _Attribute( BaseSignalExpr ):
  """Base IR class for all attribute accessing signal operations.

  This class implements a series of static methods to check if the given signal
  operation is accessing attribute of the current component, a subcompoennt,
  an interface, or a field in a struct signal.
  """
  def __init__( s, attr_base, attr, rtype ):
    super().__init__( rtype )
    s.attr = attr
    s.base = attr_base

  def __eq__( s, other ):
    return type(s) is type(other) and s.rtype == other.rtype and \
           s.attr == other.attr and \
           s.base == other.base

  def __hash__( s ):
    return hash((type(s), s.rtype, s.attr, s.base))

  def get_base( s ):
    return s.base

  def get_attr( s ):
    return s.attr

  @staticmethod
  def is_cur_comp_attr( attr_base, attr ):
    """Return CurCompAttr constructor if the given attribute belongs to the current component."""
    base_rtype = attr_base.get_rtype()
    if isinstance(attr_base, CurComp) and base_rtype.has_property(attr):
      return CurCompAttr
    else:
      return None

  @staticmethod
  def is_subcomp_attr( attr_base, attr ):
    """Return CurCompAttr constructor if the given attribute belongs to a sub-component."""
    base_rtype = attr_base.get_rtype()
    if not isinstance(attr_base, CurComp) and \
       isinstance(base_rtype, rt.Component) and base_rtype.has_property(attr):
      return SubCompAttr
    else:
      return None

  @staticmethod
  def is_interface_attr( attr_base, attr ):
    """Return CurCompAttr constructor if the given attribute belongs to an interface."""
    base_rtype = attr_base.get_rtype()
    if isinstance(base_rtype, rt.InterfaceView) and base_rtype.has_property(attr):
      return InterfaceAttr
    else:
      return None

  @staticmethod
  def is_struct_attr( attr_base, attr ):
    """Return CurCompAttr constructor if the given attribute belongs to struct signal."""
    base_rtype = attr_base.get_rtype()
    if isinstance(base_rtype, rt.Signal):
      dtype = base_rtype.get_dtype()
      if isinstance(dtype, rdt.Struct) and dtype.has_property(attr):
        return StructAttr
      else:
        return None
    else:
      return None

#-------------------------------------------------------------------------
# Actual IR signal operation classes
#-------------------------------------------------------------------------

class ConstInstance( BaseSignalExpr ):
  """IR class for a constant instance.

  This class is for constants that appear in signal operations and is not
  an attribute of a component.
  """
  def __init__( s, obj, value ):
    super().__init__(rt.Const(rdt.get_rtlir_dtype( obj )))
    s.value = value

  def __eq__( s, other ):
    return isinstance(other, ConstInstance) and s.rtype == other.rtype and \
           s.value == other.value

  def __hash__( s ):
    return hash((type(s), s.rtype, s.value))

  def get_value( s ):
    return s.value

class CurComp( BaseSignalExpr ):
  """IR class for the current component.

  This class is the base of most signal expressions because most signal
  expressions begin by accessing an attribute of the current component.
  This class implements a static method which checks if the given name
  is the same as the current component's name.
  """
  def __init__( s, comp, comp_id ):
    super().__init__(comp._pass_structural_rtlir_gen.rtlir_type)
    s.comp_id = comp_id

  def __eq__( s, other ):
    return isinstance(other, CurComp) and s.rtype == other.rtype and \
           s.comp_id == other.comp_id

  def __hash__( s ):
    return hash((type(s), s.rtype, s.comp_id))

  def get_component_id( s ):
    return s.comp_id

  @staticmethod
  def is_cur_comp( comp, comp_id ):
    """Return CurComp constructor if comp_id matches the current component's name."""
    if comp_id == comp._dsl.my_name:
      return CurComp
    else:
      return None

class PortIndex( _UnpackedIndex ):
  """IR class for indexing on a port array ."""

class WireIndex( _UnpackedIndex ):
  """IR class for indexing on a wire array ."""

class ConstIndex( _UnpackedIndex ):
  """IR class for indexing on a const array ."""

class InterfaceViewIndex( _UnpackedIndex ):
  """IR class for indexing on an interface array ."""

class ComponentIndex( _UnpackedIndex ):
  """IR class for indexing on a component array ."""

class PackedIndex( _Index ):
  """IR class for indexing on a signal of packed data type."""
  def __init__( s, index_base, index ):
    base_rtype = index_base.get_rtype()
    dtype = base_rtype.get_dtype()
    if isinstance( base_rtype, rt.Port ):
      rtype = rt.Port( base_rtype.get_direction(),
                    dtype.get_next_dim_type() )
    elif isinstance( base_rtype, rt.Wire ):
      rtype = rt.Wire( dtype.get_next_dim_type() )
    else:
      assert False, f"unrecognized signal type {base_rtype} for indexing"
    super().__init__( index_base, index, rtype )

class BitSelection( _Index ):
  """IR class for selecting a bit of a vector signal."""
  def __init__( s, index_base, index ):
    base_rtype = index_base.get_rtype()
    dtype = base_rtype.get_dtype()
    if isinstance( base_rtype, rt.Port ):
      rtype = rt.Port( base_rtype.get_direction(), rdt.Vector( 1 ) )
    elif isinstance( base_rtype, rt.Wire ):
      rtype = rt.Wire( rdt.Vector( 1 ) )
    else:
      assert False, f"unrecognized signal type {base_rtype} for indexing"
    super().__init__( index_base, index, rtype )

class PartSelection( _Slice ):
  """IR class for selecting one or more bits of a vector signal."""

class CurCompAttr( _Attribute ):
  """IR class for accessing the attribute of the current component."""
  def __init__( s, attr_base, attr ):
    rtype = attr_base.get_rtype().get_property( attr )
    super().__init__( attr_base, attr, rtype )

class SubCompAttr( _Attribute ):
  """IR class for accessing the attribute of a sub-component."""
  def __init__( s, attr_base, attr ):
    rtype = attr_base.get_rtype().get_property( attr )
    super().__init__( attr_base, attr, rtype )

class InterfaceAttr( _Attribute ):
  """IR class for accessing the attribute of an interface."""
  def __init__( s, attr_base, attr ):
    rtype = attr_base.get_rtype().get_property( attr )
    super().__init__( attr_base, attr, rtype )

class StructAttr( _Attribute ):
  """IR class for accessing the attribute of a struct signal."""
  def __init__( s, attr_base, attr ):
    base_rtype = attr_base.get_rtype()
    dtype = base_rtype.get_dtype()
    if isinstance( base_rtype, rt.Port ):
      rtype = rt.Port( base_rtype.get_direction(), dtype.get_property( attr ) )
    elif isinstance( base_rtype, rt.Wire ):
      rtype = rt.Wire( dtype.get_property( attr ) )
    else:
      assert False, f"unrecognized signal type {base_rtype} for field selection"
    super().__init__( attr_base, attr, rtype )

#-------------------------------------------------------------------------
# Map string signal expression to IR object generation methods
#-------------------------------------------------------------------------

signal_expr_classes = {
    'Attr' :  [ _Attribute.is_cur_comp_attr,   _Attribute.is_subcomp_attr,
                _Attribute.is_interface_attr,  _Attribute.is_struct_attr ],
    'Index' : [ _Index.is_packed_index,        _Index.is_bit_selection,
                _UnpackedIndex.is_port_index,  _UnpackedIndex.is_wire_index,
                _UnpackedIndex.is_const_index, _UnpackedIndex.is_ifc_view_index,
                _UnpackedIndex.is_component_index ],
    'Slice' : [ _Slice.is_part_selection ],
    'Base'  : [ CurComp.is_cur_comp ]
}

#-------------------------------------------------------------------------
# gen_signal_expr
#-------------------------------------------------------------------------

def gen_signal_expr( cur_component, signal ):
  """Return an RTLIR signal expression for the given signal."""

  def get_next_op( expr, cur_pos, my_name, full_name ):
    """Return the next signal operation in string `expr`.

    Return value: ( op, *data )
    op is one of [ 'Attr', 'Slice', 'Index', 'Base', 'Done' ].
    *data is one to two variables that describes the next signal operation.
    """
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
      assert rb_pos != -1 and pos == rb_pos+1, \
        f"unrecognized expression {expr}"

      if cur_pos < colon_pos < rb_pos:
        start = int( expr[cur_pos+1:colon_pos] )
        stop  = int( expr[colon_pos+1:rb_pos] )
        return ( 'Slice', start, stop ), pos
      else:
        return ( 'Index', int(expr[cur_pos+1:rb_pos]) ), pos

    # The current component ( base of attribute )
    else:
      base_pos = expr.find( full_name )
      assert base_pos >= 0, \
        f"cannot find the base of attribute {full_name} in {expr}"
      return ( 'Base', my_name ), base_pos + len( full_name )

  def get_cls_inst( func_list, cur_node, ops ):
    """Return an IR instance of the given signal operation."""
    classes = [ c for c in ( f( cur_node, *ops ) for f in func_list ) if c ]
    assert len(classes) <= 1, f"internal error: not unique class {classes}!"
    assert classes, f"internal error: no available expression nodes for {cur_node}!"
    return classes[0]( cur_node, *ops )

  try:

    try:
      expr = signal._dsl.full_name
      base_comp = signal
    except AttributeError:
      # Special case for a ConstInstance because it has no name
      assert hasattr( signal._dsl, 'const' ), f'{signal} is not supported!'
      c = signal._dsl.const
      assert isinstance( c, ( int, Bits )) or is_bitstruct_inst( c ), \
          f'{signal._dsl.const} is not an integer/Bits/BitStruct const!'
      return ConstInstance( signal, c )

    # Get the base component
    base_comp = cur_component
    full_name = base_comp._dsl.full_name
    my_name = base_comp._dsl.my_name
    assert expr.find( full_name ) >= 0, \
      f"cannot find the base of attribute {full_name} in {expr}"

    # Start from the base component and process one operation per iteration
    cur_pos, cur_node = 0, base_comp
    while cur_pos < len( expr ):
      op, next_pos = get_next_op( expr, cur_pos, my_name, full_name )
      if op[0] == 'Done': break
      cur_node = get_cls_inst( signal_expr_classes[ op[0] ], cur_node, op[1:] )
      cur_pos = next_pos
    return cur_node

  except AssertionError as e:
    msg = '' if e.args[0] is None else e.args[0]
    raise RTLIRConversionError( signal, msg )
