#=========================================================================
# SVBehavioralTranslatorL1.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 18, 2019
"""Provide the level 1 SystemVerilog translator implementation."""
from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits32
from pymtl3.passes.rtlir import BehavioralRTLIR as bir
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.sverilog.errors import SVerilogTranslationError
from pymtl3.passes.sverilog.utility import make_indent
from pymtl3.passes.translator.behavioral.BehavioralTranslatorL1 import (
    BehavioralTranslatorL1,
)

from .SVBehavioralTranslatorL0 import SVBehavioralTranslatorL0


class SVBehavioralTranslatorL1( SVBehavioralTranslatorL0, BehavioralTranslatorL1 ):

  def _get_rtlir2sv_visitor( s ):
    return BehavioralRTLIRToSVVisitorL1

  def rtlir_tr_upblk_decls( s, upblk_srcs ):
    ret = ''
    for upblk_src in upblk_srcs:
      make_indent( upblk_src, 1 )
      ret += '\n' + '\n'.join( upblk_src )
    return ret

  def rtlir_tr_upblk_decl( s, upblk, rtlir_upblk ):
    visitor = s._get_rtlir2sv_visitor()()
    return visitor.enter( upblk, rtlir_upblk )

  def rtlir_tr_behavioral_freevars( s, freevars ):
    make_indent( freevars, 1 )
    return '\n'.join( freevars )

  def rtlir_tr_behavioral_freevar( s, id_, rtype, array_type, dtype, obj ):
    assert isinstance( rtype, rt.Const ), \
      '{} freevar should be a constant!'.format( id_ )
    assert isinstance( rtype.get_dtype(), rdt.Vector ), \
      '{} freevar should be a (list of) integer!'.format( id_ )
    return s.rtlir_tr_const_decl( '_fvar_'+id_, rtype, array_type, dtype, obj )

#-------------------------------------------------------------------------
# BehavioralRTLIRToSVVisitorL1
#-------------------------------------------------------------------------

class BehavioralRTLIRToSVVisitorL1( bir.BehavioralRTLIRNodeVisitor ):
  """Visitor that translates RTLIR to SystemVerilog for a single upblk."""

  def __init__( s ):
    # Should use enum here, but enum is a python 3 feature...
    s.NONE          = 0
    s.COMBINATIONAL = 1
    s.SEQUENTIAL    = 2
    s.upblk_type    = s.NONE

  def enter( s, blk, rtlir ):
    """Entry point for RTLIR generation."""
    s.blk     = blk

    # s.globals contains a dict of the global namespace of the module where
    # blk was defined
    s.globals = blk.__globals__

    # s.closure contains the free variables defined in an enclosing scope.
    # Basically this is the model instance s.
    s.closure = {}

    for i, var in enumerate( blk.__code__.co_freevars ):
      try: 
        s.closure[ var ] = blk.__closure__[ i ].cell_contents
      except ValueError: 
        pass

    return s.visit( rtlir )

  #-----------------------------------------------------------------------
  # visit_CombUpblk
  #-----------------------------------------------------------------------

  def visit_CombUpblk( s, node ):
    """Return the SV representation of statements inside it."""
    blk_name = node.name
    src      = []
    body     = []
    s.upblk_type = s.COMBINATIONAL

    # Add name of the upblk to this always block
    src.extend( [ 'always_comb begin : {blk_name}'.format( **locals() ) ] )
    
    for stmt in node.body:
      body.extend( s.visit( stmt ) )

    make_indent( body, 1 )
    src.extend( body )
    src.extend( [ 'end' ] )
    s.upblk_type = s.NONE
    return src

  #-----------------------------------------------------------------------
  # visit_SeqUpblk
  #-----------------------------------------------------------------------

  def visit_SeqUpblk( s, node ):
    """Return the SV representation of statements inside it."""
    blk_name = node.name
    src      = []
    body     = []

    s.upblk_type = s.SEQUENTIAL

    # Add name of the upblk to this always block
    src.extend( [
      'always_ff @(posedge clk) begin : {blk_name}'.format( **locals() )
    ] )
    
    for stmt in node.body:
      body.extend( s.visit( stmt ) )

    make_indent( body, 1 )
    src.extend( body )
    src.extend( [ 'end' ] )
    s.upblk_type = s.NONE
    return src

  #-----------------------------------------------------------------------
  # Statements
  #-----------------------------------------------------------------------
  # All statement nodes return a list of strings.

  #-----------------------------------------------------------------------
  # visit_Assign
  #-----------------------------------------------------------------------

  def visit_Assign( s, node ):
    target        = s.visit( node.target )
    value         = s.visit( node.value )
    assignment_op = '<=' if s.upblk_type == s.SEQUENTIAL else '='
    ret = '{target} {assignment_op} {value};'.format( **locals() )
    return [ ret ]

  #-----------------------------------------------------------------------
  # visit_If
  #-----------------------------------------------------------------------

  def visit_If( s, node ):
    raise SVerilogTranslationError( s.blk, node, "If not supported at L1" )

  #-----------------------------------------------------------------------
  # visit_For
  #-----------------------------------------------------------------------

  def visit_For( s, node ):
    raise SVerilogTranslationError( s.blk, node, "For not supported at L1" )

  #-----------------------------------------------------------------------
  # Expressions
  #-----------------------------------------------------------------------
  # All expression nodes return a single string.  

  #-----------------------------------------------------------------------
  # visit_Number
  #-----------------------------------------------------------------------

  def visit_Number( s, node ):
    """Return a number in string without width specifier."""
    return str( node.value )

  #-----------------------------------------------------------------------
  # visit_Concat
  #-----------------------------------------------------------------------

  def visit_Concat( s, node ):
    values = [ s.visit(v) for v in node.values ]
    signals = ', '.join( values )
    return '{{ {signals} }}'.format( **locals() )

  #-----------------------------------------------------------------------
  # visit_ZeroExt
  #-----------------------------------------------------------------------

  def visit_ZeroExt( s, node ):
    value = s.visit( node.value )
    try:
      target_nbits = int(node.nbits._value)
    except AttributeError:
      raise SVerilogTranslationError( s.blk, node, 
        "new bitwidth of zero extension must be known at elaboration time!" )
    current_nbits = int(node.value.Type.get_dtype().get_length())
    padded_nbits = target_nbits - current_nbits
    return "{{ {{ {padded_nbits} {{ 1'b0 }} }}, {value} }}".format( **locals() )

  #-----------------------------------------------------------------------
  # visit_SignExt
  #-----------------------------------------------------------------------

  def visit_SignExt( s, node ):
    value = s.visit( node.value )
    try:
      target_nbits = int(node.nbits._value)
    except AttributeError:
      raise SVerilogTranslationError( s.blk, node, 
        "new bitwidth of sign extension must be known at elaboration time!" )
    current_nbits = int(node.value.Type.get_dtype().get_length())
    last_bit = current_nbits - 1
    padded_nbits = target_nbits - current_nbits
    return "{{ {{ {padded_nbits} {{ {value}[{last_bit}] }} }}, {value} }}". \
        format( **locals() )

  #-----------------------------------------------------------------------
  # visit_Reduce
  #-----------------------------------------------------------------------

  def visit_Reduce( s, node ):
    op_t = type(node.op)
    reduce_ops = { bir.BitAnd : '&', bir.BitOr : '|', bir.BitXor : '^' }
    if op_t not in reduce_ops:
      raise SVerilogTranslationError( s.blk, node,
          "unrecognized operator {} for reduce method!".format(op_t) )
    value = s.visit( node.value )
    op = reduce_ops[ op_t ]
    return "({op}{value})".format( **locals() )

  #-----------------------------------------------------------------------
  # visit_SizeCast
  #-----------------------------------------------------------------------

  def visit_SizeCast( s, node ):
    nbits = node.nbits
    value = s.visit( node.value )
    return "{nbits}'( {value} )".format( **locals() )

  #-----------------------------------------------------------------------
  # visit_StructInst
  #-----------------------------------------------------------------------

  def visit_StructInst( s, node ):
    raise SVerilogTranslationError( s.blk, node, "StructInst not supported at L1" )

  #-----------------------------------------------------------------------
  # visit_IfExp
  #-----------------------------------------------------------------------

  def visit_IfExp( s, node ):
    raise SVerilogTranslationError( s.blk, node, "IfExp not supported at L1" )

  #-----------------------------------------------------------------------
  # visit_UnaryOp
  #-----------------------------------------------------------------------

  def visit_UnaryOp( s, node ):
    raise SVerilogTranslationError( s.blk, node, "UnaryOp not supported at L1" )

  #-----------------------------------------------------------------------
  # visit_BoolOp
  #-----------------------------------------------------------------------

  def visit_BoolOp( s, node ):
    raise SVerilogTranslationError( s.blk, node, "BoolOp not supported at L1" )

  #-----------------------------------------------------------------------
  # visit_BinOp
  #-----------------------------------------------------------------------

  def visit_BinOp( s, node ):
    raise SVerilogTranslationError( s.blk, node, "BinOp not supported at L1" )

  #-----------------------------------------------------------------------
  # visit_Compare
  #-----------------------------------------------------------------------

  def visit_Compare( s, node ):
    raise SVerilogTranslationError( s.blk, node, "Compare not supported at L1" )

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):

    attr  = node.attr
    value = s.visit( node.value )

    if isinstance( node.value, bir.Base ):
      # The base of this attribute node is the component 's'.
      # Example: s.out, s.STATE_IDLE
      # assert node.value.base is s.component
      ret = attr
    else:
      raise SVerilogTranslationError( s.blk, node, 
          "sub-components are not supported at L1" )

    return ret

  #-----------------------------------------------------------------------
  # visit_Index
  #-----------------------------------------------------------------------

  def visit_Index( s, node ):
    idx   = s.visit( node.idx )
    value = s.visit( node.value )
    Type = node.value.Type

    # Unpacked index
    if isinstance( Type, rt.Array ):

      subtype = Type.get_sub_type()
      if isinstance( subtype, ( rt.Port, rt.Wire, rt.Const ) ):
        return '{value}[{idx}]'.format( **locals() )
      else:
        return '{value}_${idx}'.format( **locals() )

    # Index on a signal
    elif isinstance( Type, rt.Signal ):

      # Packed index
      if Type.is_packed_indexable():
        return '{value}[{idx}]'.format( **locals() )
      # Bit selection
      elif isinstance( Type.get_dtype(), rdt.Vector ):
        return '{value}[{idx}]'.format( **locals() )
      else:
        raise SVerilogTranslationError( s.blk, node, 
            "internal error: unrecognized index" )

    else:
      raise SVerilogTranslationError( s.blk, node, 
          "internal error: unrecognized index" )

  #-----------------------------------------------------------------------
  # visit_Slice
  #-----------------------------------------------------------------------

  def visit_Slice( s, node ):

    lower = s.visit( node.lower )
    value = s.visit( node.value )

    if hasattr( node.upper, '_value' ):
      upper = str( int( node.upper._value - Bits32(1) ) )
    else:
      upper = s.visit( node.upper ) + '-1'

    return '{value}[{upper}:{lower}]'.format( **locals() )

  #-----------------------------------------------------------------------
  # visit_Base
  #-----------------------------------------------------------------------

  def visit_Base( s, node ):
    return str( node.base )

  #-----------------------------------------------------------------------
  # visit_LoopVar
  #-----------------------------------------------------------------------

  def visit_LoopVar( s, node ):
    raise SVerilogTranslationError( s.blk, node, "LoopVar not supported at L1" )

  #-----------------------------------------------------------------------
  # visit_FreeVar
  #-----------------------------------------------------------------------

  def visit_FreeVar( s, node ):
    return '_fvar_'+node.name

  #-----------------------------------------------------------------------
  # visit_TmpVar
  #-----------------------------------------------------------------------

  def visit_TmpVar( s, node ):
    raise SVerilogTranslationError( s.blk, node, "TmpVar not supported at L1" )

  #-----------------------------------------------------------------------
  # visit_LoopVarDecl
  #-----------------------------------------------------------------------

  def visit_LoopVarDecl( s, node ):
    raise SVerilogTranslationError( s.blk, node, "LoopVarDecl not supported at L1" )
