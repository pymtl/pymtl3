#=========================================================================
# YosysBehavioralTranslatorL1.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Provide the yosys-compatible SystemVerilog L1 behavioral translator."""

from pymtl3.datatypes import Bits, is_bitstruct_inst
from pymtl3.passes.backends.verilog.errors import VerilogTranslationError
from pymtl3.passes.backends.verilog.translation.behavioral.VBehavioralTranslatorL1 import (
    BehavioralRTLIRToVVisitorL1,
    VBehavioralTranslatorL1,
)
from pymtl3.passes.backends.verilog.util.utility import make_indent
from pymtl3.passes.rtlir import BehavioralRTLIR as bir
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt


class YosysBehavioralTranslatorL1( VBehavioralTranslatorL1 ):

  def _get_rtlir2v_visitor( s ):
    return YosysBehavioralRTLIRToVVisitorL1

class YosysBehavioralRTLIRToVVisitorL1( BehavioralRTLIRToVVisitorL1 ):
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
    loopvars = sorted(list( s.loopvars ))
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
    for target in node.targets:
      target._top_expr = 1
    node.value._top_expr = 1
    return super().visit_Assign( node )

  #-----------------------------------------------------------------------
  # visit_Number
  #-----------------------------------------------------------------------

  # def visit_Number( s, node ):
  #   nbits = node.Type.get_dtype().get_length()

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
      node.value._top_expr = 1
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
        nbits = node.Type.get_dtype().get_length()
        node.sexpr['s_attr'] = f"{nbits}'d{obj}"
        node.sexpr['s_index'] = ""
      elif isinstance( obj, Bits ):
        # nbits = obj.nbits
        nbits = node.Type.get_dtype().get_length()
        value = int( obj )
        node.sexpr['s_attr'] = f"{nbits}'d{value}"
        node.sexpr['s_index'] = ""
      elif is_bitstruct_inst( obj ):
        node.sexpr['s_attr'] = s._struct_instance( node.Type.get_dtype(), obj )
        node.sexpr['s_index'] = ""
      else:
        raise VerilogTranslationError( s.blk, node,
          f"{node.attr} {obj} is not an integer!" )

    elif isinstance( node.value, bir.Base ):
      # The base of this attribute node is the component 's'.
      # Example: s.out, s.STATE_IDLE
      # assert node.value.base is s.component
      s.check_res( node, node.attr )
      node.sexpr['s_attr'] = "{}"
      node.sexpr['attr'].append( node.attr )

    else:
      raise VerilogTranslationError( s.blk, node,
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
          raise VerilogTranslationError( s.blk, node,
            f"{value} is not an array of constants!" )
        if isinstance(node.Type, rt.Const):
          nbits = node.Type.get_dtype().get_length()
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
        raise VerilogTranslationError( s.blk, node,
            "internal error: unrecognized index" )

    else:
      raise VerilogTranslationError( s.blk, node,
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
      nbits = node.Type.get_dtype().get_length()
      return f"{nbits}'d{node.obj}"
    elif isinstance( node.obj, Bits ):
      nbits = node.obj.nbits
      value = int( node.obj )
      return f"{nbits}'d{value}"
    else:
      raise VerilogTranslationError( s.blk, node,
      f"{node.name} {node.obj} is not an integer!" )
