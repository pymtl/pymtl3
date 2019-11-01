#=========================================================================
# YosysBehavioralTranslatorL1.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Provide the yosys-compatible SystemVerilog L1 behavioral translator."""

from pymtl3.datatypes import Bits, is_bitstruct_inst
from pymtl3.passes.rtlir import BehavioralRTLIR as bir
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.sverilog.errors import SVerilogTranslationError
from pymtl3.passes.sverilog.translation.behavioral.SVBehavioralTranslatorL1 import (
    BehavioralRTLIRToSVVisitorL1,
    SVBehavioralTranslatorL1,
)
from pymtl3.passes.sverilog.util.utility import make_indent


class YosysBehavioralTranslatorL1( SVBehavioralTranslatorL1 ):

  def _get_rtlir2sv_visitor( s ):
    return YosysBehavioralRTLIRToSVVisitorL1

class YosysBehavioralRTLIRToSVVisitorL1( BehavioralRTLIRToSVVisitorL1 ):
  """IR visitor that generates yosys-compatible SystemVerilog code."""

  def __init__( s, is_reserved ):
    super().__init__( is_reserved )
    s.loopvars = set()

  def signal_expr_prologue( s, node ):
    # Setup the signal expression attributes
    # attr: an array of all attributes that will be filled into the attribute
    # template string `s_attr`
    # index: an array of all indices that will be filled into the index
    # template string `s_index`
    try:
      node.sexpr = node.value.sexpr
    except AttributeError:
      node.sexpr = { 'attr' : [], 'index' : [], 's_attr' : "", 's_index' : "" }

  def signal_expr_epilogue( s, node, ret ):
    try:
      # If the current node is a top level signal expression, assemble the
      # complete signal expression by filling attributes and indices into
      # their template strings
      if node._top_expr:
        all_terms = node.sexpr['attr'] + node.sexpr['index']
        template = node.sexpr['s_attr'] + node.sexpr['s_index']
        return template.format( *all_terms )
    except AttributeError:
      # If the current node is not a top level signal expression then we
      # are done. Return the given return value for debugging purposes.
      return ret

  def get_loopvars( s ):
    loopvars = list( s.loopvars )
    for i, loopvar in enumerate( loopvars ):
      loopvars[i] = "integer " + loopvar + ";"
    if loopvars:
      loopvars.append( "" )
    return loopvars

  #-----------------------------------------------------------------------
  # visit_CombUpblk
  #-----------------------------------------------------------------------

  def visit_CombUpblk( s, node ):
    upblk = super().visit_CombUpblk( node )
    return s.get_loopvars() + upblk

  #-----------------------------------------------------------------------
  # visit_SeqUpblk
  #-----------------------------------------------------------------------

  def visit_SeqUpblk( s, node ):
    upblk = super().visit_SeqUpblk( node )
    return s.get_loopvars() + upblk

  #-----------------------------------------------------------------------
  # visit_Assign
  #-----------------------------------------------------------------------

  def visit_Assign( s, node ):
    node.target._top_expr = 1
    node.value._top_expr = 1
    return super().visit_Assign( node )

  #-----------------------------------------------------------------------
  # visit_Concat
  #-----------------------------------------------------------------------

  def visit_Concat( s, node ):
    for child in node.values:
      child._top_expr = 1
    return super().visit_Concat( node )

  #-----------------------------------------------------------------------
  # visit_ZeroExt
  #-----------------------------------------------------------------------

  def visit_ZeroExt( s, node ):
    node.value._top_expr = 1
    return super().visit_ZeroExt( node )

  #-----------------------------------------------------------------------
  # visit_SignExt
  #-----------------------------------------------------------------------

  def visit_SignExt( s, node ):
    node.value._top_expr = 1
    return super().visit_SignExt( node )

  #-----------------------------------------------------------------------
  # visit_Reduce
  #-----------------------------------------------------------------------

  def visit_Reduce( s, node ):
    node.value._top_expr = 1
    return super().visit_Reduce( node )

  #-----------------------------------------------------------------------
  # visit_SizeCast
  #-----------------------------------------------------------------------

  def visit_SizeCast( s, node ):
    nbits = node.nbits
    value = None if not hasattr(node.value, "_value") else node.value._value

    if value is None:
      value_str = s.visit( node.value )
      cur_nbits = node.value.Type.get_dtype().get_length()
      if cur_nbits == nbits:
        return value_str
      elif cur_nbits > nbits:
        msb = nbits-1
        return f"{value_str}[{msb}:0]"
      else:
        # Zero-extend the value
        n_zero = nbits - cur_nbits
        return f"{{ {{ {n_zero} {{ 1'b0 }} }}, {value_str} }}"

    if isinstance( value, Bits ):
      value = int(value)
    return f"{nbits}'d{value}"

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):

    s.signal_expr_prologue( node )

    Type = node.Type

    if isinstance(Type, rt.Const):
      obj = Type.get_object()
      if isinstance( obj, int ):
        node.sexpr['s_attr'] = f"32'd{obj}"
        node.sexpr['s_index'] = ""
      elif isinstance( obj, Bits ):
        nbits = obj.nbits
        value = int( obj )
        node.sexpr['s_attr'] = f"{nbits}'d{value}"
        node.sexpr['s_index'] = ""
      elif is_bitstruct_inst( obj ):
        node.sexpr['s_attr'] = s._struct_instance( node.Type.get_dtype(), obj )
        node.sexpr['s_index'] = ""
      else:
        raise SVerilogTranslationError( s.blk, node,
          f"{node.attr} {obj} is not an integer!" )

    elif isinstance( node.value, bir.Base ):
      # The base of this attribute node is the component 's'.
      # Example: s.out, s.STATE_IDLE
      # assert node.value.base is s.component
      s.check_res( node, node.attr )
      node.sexpr['s_attr'] = "{}"
      node.sexpr['attr'].append( node.attr )

    else:
      raise SVerilogTranslationError( s.blk, node,
          "sub-components are not supported at L1" )

    return s.signal_expr_epilogue( node, node.attr )

  #-----------------------------------------------------------------------
  # visit_Index
  #-----------------------------------------------------------------------

  def visit_Index( s, node ):

    node.idx._top_expr = 1
    idx   = s.visit( node.idx )
    value = s.visit( node.value )
    Type = node.value.Type

    s.signal_expr_prologue( node )

    # Unpacked index
    if isinstance( Type, rt.Array ):

      subtype = Type.get_sub_type()
      if isinstance( subtype, rt.Const ):
        nbits = subtype.get_dtype().get_length()
        try:
          const_value = node._value
        except AttributeError:
          raise SVerilogTranslationError( s.blk, node,
            f"{value} is not an array of constants!" )
        node.sexpr['s_index'] = f"{nbits}'d{const_value}"
        node.sexpr['index'] = []
        node.sexpr['s_attr'] = ""
        node.sexpr['attr'] = []
      else:
        node.sexpr['s_index'] += '[{}]'
        node.sexpr['index'].append( idx )

    # Index on a signal
    elif isinstance( Type, rt.Signal ):

      # Packed index or bit selection
      if Type.is_packed_indexable() or isinstance(Type.get_dtype(), rdt.Vector):
        node.sexpr['s_index'] += '[{}]'
        node.sexpr['index'].append( idx )
      else:
        raise SVerilogTranslationError( s.blk, node,
            "internal error: unrecognized index" )

    else:
      raise SVerilogTranslationError( s.blk, node,
          "internal error: unrecognized index" )

    return s.signal_expr_epilogue( node, f'{value}[{idx}]' )

  #-----------------------------------------------------------------------
  # visit_Slice
  #-----------------------------------------------------------------------

  def visit_Slice( s, node ):
    node.value._top_expr = 1
    node.lower._top_expr = 1
    node.upper._top_expr = 1
    return super().visit_Slice( node )

  #-----------------------------------------------------------------------
  # visit_FreeVar
  #-----------------------------------------------------------------------

  def visit_FreeVar( s, node ):
    if isinstance( node.obj, int ):
      return f"32'd{node.obj}"
    elif isinstance( node.obj, Bits ):
      nbits = node.obj.nbits
      value = int( node.obj )
      return f"{nbits}'d{value}"
    else:
      raise SVerilogTranslationError( s.blk, node,
      f"{node.name} {node.obj} is not an integer!" )
