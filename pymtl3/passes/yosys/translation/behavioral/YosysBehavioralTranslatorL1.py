#=========================================================================
# YosysBehavioralTranslatorL1.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Provide the yosys-compatible SystemVerilog L1 behavioral translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits
from pymtl3.passes.rtlir import BehavioralRTLIR as bir
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.sverilog.errors import SVerilogTranslationError
from pymtl3.passes.sverilog.translation.behavioral.SVBehavioralTranslatorL1 import (
    BehavioralRTLIRToSVVisitorL1,
    SVBehavioralTranslatorL1,
)


class YosysBehavioralTranslatorL1( SVBehavioralTranslatorL1 ):

  def _get_rtlir2sv_visitor( s ):
    return YosysBehavioralRTLIRToSVVisitorL1

class YosysBehavioralRTLIRToSVVisitorL1( BehavioralRTLIRToSVVisitorL1 ):
  """IR visitor that generates yosys-compatible SystemVerilog code.
  
  This visitor differs from the canonical SystemVerilog visitor in that
  1) it does not use the explicity bitwidth casting syntax in
  SystemVerilog ( e.g. 32'( in_[0:16] ) ) because it is not yet supported
  by yosys;
  2) it does not use array of ports syntax because yosys does not support
  array of ports;
  3) it does not use declaration of constant attributes and all constant
  attributes will be translated into literal numbers;
  4) it does not support free variables unless the variable is a single python
  int or a Bits object;
  """

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

  #-----------------------------------------------------------------------
  # visit_Assign
  #-----------------------------------------------------------------------

  def visit_Assign( s, node ):
    node.target._top_expr = 1
    node.value._top_expr = 1
    return super( YosysBehavioralRTLIRToSVVisitorL1, s ).visit_Assign( node )

  #-----------------------------------------------------------------------
  # visit_Concat
  #-----------------------------------------------------------------------

  def visit_Concat( s, node ):
    for child in node.values:
      child._top_expr = 1
    return super( YosysBehavioralRTLIRToSVVisitorL1, s ).visit_Concat( node )

  #-----------------------------------------------------------------------
  # visit_ZeroExt
  #-----------------------------------------------------------------------

  def visit_ZeroExt( s, node ):
    node.value._top_expr = 1
    return super( YosysBehavioralRTLIRToSVVisitorL1, s ).visit_ZeroExt( node )

  #-----------------------------------------------------------------------
  # visit_SignExt
  #-----------------------------------------------------------------------

  def visit_SignExt( s, node ):
    node.value._top_expr = 1
    return super( YosysBehavioralRTLIRToSVVisitorL1, s ).visit_SignExt( node )

  #-----------------------------------------------------------------------
  # visit_Reduce
  #-----------------------------------------------------------------------

  def visit_Reduce( s, node ):
    node.value._top_expr = 1
    return super( YosysBehavioralRTLIRToSVVisitorL1, s ).visit_Reduce( node )

  #-----------------------------------------------------------------------
  # visit_SizeCast
  #-----------------------------------------------------------------------

  def visit_SizeCast( s, node ):
    nbits = node.nbits
    value = getattr( node.value, "_value", None )

    if value is None:
      raise SVerilogTranslationError( s.blk, node, 
"""\
Operand {} of bitwidth casting is not an integer! If you are trying to cast \
a signal to a different bitwdith, you probably want to use sext or zext to \
extend the signal to the desired bitwidth or slicing to extract desired \
amount of bits.
NOTE: this error is yosys-specific because it does not support SystemVerilog \
      bitwidth casting syntax. You can still use this syntax in the canonical \
      SystemVerilog translation ( passes.sverilog.TranslationPass ).
""".format( node.value ) )

    if isinstance( value, Bits ):
      value = value.uint()
    return "{nbits}'d{value}".format( **locals() )

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):

    s.signal_expr_prologue( node )

    Type = node.Type

    if isinstance(Type, rt.Array) and isinstance(Type.get_sub_type(), rt.Const):
      raise SVerilogTranslationError( s.blk, node,
          "array of constants {} is not allowed!".format(node.attr) )

    if isinstance(Type, rt.Const):
      obj = Type.get_object()
      if isinstance( obj, int ):
        node.sexpr['s_attr'] = "32'd{}".format( obj )
      elif isinstance( obj, Bits ):
        nbits = obj.nbits
        value = int( obj.value )
        node.sexpr['s_attr'] = "{nbits}'d{value}".format( **locals() )
      else:
        raise SVerilogTranslationError( s.blk, node,
          "{} {} is not an integer!".format( node.attr, obj ) )

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
        raise SVerilogTranslationError( s.blk, node,
          "array of consts {} is not supported by the yosys backend!". \
              format( value ) )
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

    return s.signal_expr_epilogue( node, value+'[{}]'.format( idx ) )

  #-----------------------------------------------------------------------
  # visit_Slice
  #-----------------------------------------------------------------------

  def visit_Slice( s, node ):
    node.value._top_expr = 1
    node.lower._top_expr = 1
    node.upper._top_expr = 1
    return super( YosysBehavioralRTLIRToSVVisitorL1, s ).visit_Slice( node )

  #-----------------------------------------------------------------------
  # visit_FreeVar
  #-----------------------------------------------------------------------

  def visit_FreeVar( s, node ):
    if isinstance( node.obj, int ):
      return "32'd{}".format( node.obj )
    elif isinstance( node.obj, Bits ):
      nbits = node.obj.nbits
      value = int( node.obj.value )
      return "{nbits}'d{value}".format( **locals() )
    else:
      raise SVerilogTranslationError( s.blk, node,
        "{} {} is not an integer!".format( node.name, node.obj ) )
