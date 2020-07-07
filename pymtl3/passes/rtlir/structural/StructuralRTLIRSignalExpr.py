#=========================================================================
# StructuralRTLIRSignalExpr.py
#=========================================================================
"""RTLIR signal expression class definitions and generation method."""
from pymtl3 import dsl
from pymtl3.datatypes import Bits, is_bitstruct_inst
from pymtl3.passes.rtlir.errors import RTLIRConversionError
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.rtlir.rtype import RTLIRType as rt

from .StructuralRTLIRGenL0Pass import StructuralRTLIRGenL0Pass


class BaseSignalExpr:
  """Base abstract class of RTLIR signal expressions."""
  def __init__( s, rtype ):
    assert isinstance( rtype, rt.BaseRTLIRType ), f"non-RTLIR type {rtype} encountered!"
    s.rtype = rtype

  def get_rtype( s ):
    return s.rtype

  def __eq__( s, other ):
    return type(s) is type(other) and s.rtype == other.rtype

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
           s.index == other.index and s.base == other.base

  def __hash__( s ):
    return hash((type(s), s.rtype, s.index, s.base))

  def get_index( s ):
    return s.index

  def get_base( s ):
    return s.base

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
    super().__init__(comp.get_metadata(StructuralRTLIRGenL0Pass.rtlir_type))
    s.comp_id = comp_id

  def __eq__( s, other ):
    return isinstance(other, CurComp) and s.rtype == other.rtype and \
           s.comp_id == other.comp_id

  def __hash__( s ):
    return hash((type(s), s.rtype, s.comp_id))

  def get_component_id( s ):
    return s.comp_id

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
# IR object generation methods for different types
#-------------------------------------------------------------------------

def construct_attr( attr_base, attr ):
  """Return CurCompAttr/SubCompAttr/InterfaceAttr/StructAttr constructor
     if the given attribute belongs to the current component."""
  base_rtype = attr_base.get_rtype()

  if isinstance(attr_base, CurComp):
    if base_rtype.has_property(attr):
      return CurCompAttr( attr_base, attr )
  if isinstance(base_rtype, rt.Component):
    if base_rtype.has_property(attr):
      return SubCompAttr( attr_base, attr )
  if isinstance(base_rtype, rt.InterfaceView):
    if base_rtype.has_property(attr):
      return InterfaceAttr( attr_base, attr )
  if isinstance(base_rtype, rt.Signal):
    dtype = base_rtype.get_dtype()
    if isinstance(dtype, rdt.Struct) and dtype.has_property(attr):
      return StructAttr( attr_base, attr )
  raise AssertionError(f"internal error: no available expression nodes for {attr_base}!")

def construct_index( index_base, index ):
  """Return PackedIndex/BitSelection constructor if the given index base
     is a signal of packed data type."""
  base_rtype = index_base.get_rtype()
  if isinstance(base_rtype, (rt.Port, rt.Wire)):
    dtype = base_rtype.get_dtype()
    if isinstance( dtype, rdt.Vector ):
      return BitSelection( index_base, index )
    elif isinstance( dtype, rdt.PackedArray ):
      return PackedIndex( index_base, index )
  elif isinstance( base_rtype, rt.Array ):
    subtype = base_rtype.get_sub_type()
    if isinstance( subtype, rt.Port ):
      return PortIndex( index_base, index )
    elif isinstance( subtype, rt.Wire ):
      return WireIndex( index_base, index )
    elif isinstance( subtype, rt.Const ):
      return ConstIndex( index_base, index )
    elif isinstance( subtype, rt.InterfaceView ):
      return InterfaceViewIndex( index_base, index )
    elif isinstance( subtype, rt.Component ):
      return ComponentIndex( index_base, index )
  raise AssertionError(f"internal error: no available expression nodes for {index_base}!")

def construct_slice( slice_base, sl ):
  """Return PartSelection constructor if the given index base is a vector signal."""
  base_rtype = slice_base.get_rtype()
  if isinstance(base_rtype, (rt.Port, rt.Wire)) and \
     isinstance(base_rtype.get_dtype(), rdt.Vector):
    return PartSelection( slice_base, sl.start, sl.stop )
  raise AssertionError(f"internal error: no available expression nodes for {slice_base}!")

def construct_base( comp, comp_id ):
  """Return CurComp constructor if comp_id matches the current component's name."""
  return CurComp( comp, comp_id )

#-------------------------------------------------------------------------
# gen_signal_expr
#-------------------------------------------------------------------------

def gen_signal_expr( cur_component, signal ):
  """Return an RTLIR signal expression for the given signal."""

  try:
    if isinstance( signal, dsl.Const ):
      c = signal._dsl.const
      assert isinstance( c, ( int, Bits )) or is_bitstruct_inst( c ), \
                        f'{c} is not an integer/Bits/BitStruct const!'
      return ConstInstance( signal, c )

    assert isinstance( signal, dsl.Signal ), f'{signal} is not supported!'

    # Strip off all the tokens from the signal to the component

    tmp = signal
    stack = []

    if tmp.is_sliced_signal():
      stack.append( (construct_slice, tmp._dsl.slice) )
      tmp = tmp.get_parent_object()

    while tmp is not cur_component:
      if tmp._dsl._my_indices:
        for x in reversed(tmp._dsl._my_indices):
          stack.append( (construct_index, x) )
      stack.append( (construct_attr, tmp._dsl._my_name) )
      tmp = tmp.get_parent_object()

    cur_node = construct_base( tmp, tmp._dsl.my_name )

    for f, token in reversed(stack):
      cur_node = f( cur_node, token )

    return cur_node

  except AssertionError as e:
    msg = '' if e.args[0] is None else e.args[0]
    raise RTLIRConversionError( signal, msg )
