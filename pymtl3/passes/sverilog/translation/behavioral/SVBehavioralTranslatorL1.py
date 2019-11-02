#=========================================================================
# SVBehavioralTranslatorL1.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 18, 2019
"""Provide the level 1 SystemVerilog translator implementation."""


from pymtl3.datatypes import Bits, Bits32
from pymtl3.passes.rtlir import BehavioralRTLIR as bir
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.sverilog.errors import SVerilogTranslationError
from pymtl3.passes.sverilog.util.utility import make_indent
from pymtl3.passes.translator.behavioral.BehavioralTranslatorL1 import (
    BehavioralTranslatorL1,
)

from .SVBehavioralTranslatorL0 import SVBehavioralTranslatorL0


class SVBehavioralTranslatorL1( SVBehavioralTranslatorL0, BehavioralTranslatorL1 ):

  def rtlir_tr_upblk_decls( s, upblk_decls ):
    ret = ''
    for idx, upblk_decl in enumerate(upblk_decls):
      make_indent( upblk_decl, 1 )
      if idx != 0:
        ret += '\n'
      ret += '\n' + '\n'.join( upblk_decl )
    return ret

  def rtlir_tr_upblk_decl( s, upblk, src, py_src ):
    return py_src + [ "" ] + src

  def _get_rtlir2sv_visitor( s ):
    return BehavioralRTLIRToSVVisitorL1

  def rtlir_tr_upblk_srcs( s, upblk_srcs ):
    ret = ''
    for upblk_src in upblk_srcs:
      make_indent( upblk_src, 1 )
      ret += '\n' + '\n'.join( upblk_src )
    return ret

  def rtlir_tr_upblk_src( s, upblk, rtlir_upblk ):
    visitor = s._get_rtlir2sv_visitor()(s.is_sverilog_reserved)
    return visitor.enter( upblk, rtlir_upblk )

  def rtlir_tr_upblk_py_srcs( s, upblk_py_srcs ):
    ret = ''
    for upblk_py_src in upblk_py_srcs:
      make_indent( upblk_py_src, 1 )
      ret += '\n' + '\n'.join( upblk_py_src )
    return ret

  def rtlir_tr_upblk_py_src( s, upblk, is_lambda, src, lino, filename ):
    def _trim( py_src ):
      indent = 100
      for line in py_src:
        if line:
          n_spaces = len( line ) - len( line.lstrip() )
          if n_spaces < indent:
            indent = n_spaces
      for idx, line in enumerate( py_src ):
        if line:
          py_src[ idx ] = line[indent:]

    upblk_py_src = src.split( '\n' )
    _trim( upblk_py_src )
    while upblk_py_src and not upblk_py_src[-1]:
      upblk_py_src = upblk_py_src[:-1]

    # Add comments to the generated block
    py_src = []

    if is_lambda:
      py_src += [
        "PyMTL Lambda Block Source",
        "{src}",
      ]
    else:
      py_src += [ "PyMTL Update Block Source" ]

    py_src += [ f"At {filename}:{lino}" ]

    py_src += upblk_py_src

    return ["// "+x for x in py_src]

  def rtlir_tr_behavioral_freevars( s, freevars ):
    make_indent( freevars, 1 )
    return '\n'.join( freevars )

  def rtlir_tr_behavioral_freevar( s, id_, rtype, array_type, dtype, obj ):
    assert isinstance( rtype, rt.Const ), \
      f'{id_} freevar should be a constant!'
    assert isinstance( rtype.get_dtype(), rdt.Vector ), \
      f'{id_} freevar should be a (list of) integer/BitStruct!'
    return s.rtlir_tr_const_decl( '__const__'+id_, rtype, array_type, dtype, obj )

#-------------------------------------------------------------------------
# BehavioralRTLIRToSVVisitorL1
#-------------------------------------------------------------------------

class BehavioralRTLIRToSVVisitorL1( bir.BehavioralRTLIRNodeVisitor ):
  """Visitor that translates RTLIR to SystemVerilog for a single upblk."""

  def __init__( s, is_reserved ):
    # Should use enum here, but enum is a python 3 feature...
    s.NONE          = 0
    s.COMBINATIONAL = 1
    s.SEQUENTIAL    = 2
    s.upblk_type    = s.NONE
    s._is_sverilog_reserved = is_reserved

  def is_sverilog_reserved( s, name ):
    return s._is_sverilog_reserved( name )

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

  def check_res( s, node, name ):
    if s.is_sverilog_reserved( name ):
      raise SVerilogTranslationError( s.blk, node,
        f"name {name} is a SystemVerilog reserved keyword!" )

  #-----------------------------------------------------------------------
  # visit_CombUpblk
  #-----------------------------------------------------------------------

  def visit_CombUpblk( s, node ):
    """Return the SV representation of statements inside it."""
    blk_name = node.name
    src      = []
    body     = []
    s.upblk_type = s.COMBINATIONAL

    s.check_res( node, blk_name )

    # Add name of the upblk to this always block
    src.append( f'always_comb begin : {blk_name}' )

    for stmt in node.body:
      body.extend( s.visit( stmt ) )

    make_indent( body, 1 )
    src.extend( body )
    src.append( 'end' )
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

    s.check_res( node, blk_name )

    # Add name of the upblk to this always block
    src.append( f'always_ff @(posedge clk) begin : {blk_name}' )

    for stmt in node.body:
      body.extend( s.visit( stmt ) )

    make_indent( body, 1 )
    src.extend( body )
    src.append( 'end' )
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
    assignment_op = '<=' if not node.blocking else '='
    ret = f'{target} {assignment_op} {value};'
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
    return f'{{ {signals} }}'

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
    return f"{{ {{ {padded_nbits} {{ 1'b0 }} }}, {value} }}"

  #-----------------------------------------------------------------------
  # visit_SignExt
  #-----------------------------------------------------------------------
  # We need to special case the situation where a bit-selection or single-bit
  # part selection needs to be sign-extended ( Verilator throws an error
  # at this ) e.g. in_[31:31][0] should be translated into in_[31:31].

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

    template = "{{ {{ {padded_nbits} {{ {value}[{last_bit}] }} }}, {value} }}"
    one_bit_template = "{{ {{ {padded_nbits} {{ {_value} }} }}, {value} }}"

    # Check if the signal to be extended is a bit selection or one-bit part
    # selection.
    if isinstance( node.value, bir.Slice ):
      try:
        lower = node.value.lower._value
        upper = node.value.upper._value
        if upper - lower == 1:
          _one_bit = True
        else:
          _one_bit = False
      except AttributeError:
        _one_bit = False

      # Manipulate the slicing string to avoid indexing on a sliced signal
      if not _one_bit:
        l, col, r = value.rfind('['), value.rfind(':'), value.rfind(']')
        if -1 < l < col < r:
          _value = value[:col] + ']'
          return one_bit_template.format( **locals() )

    elif isinstance( node.value, bir.Index ):
      _one_bit = True
    else:
      _one_bit = False

    if _one_bit:
      _value = value
      return one_bit_template.format( **locals() )
    else:
      return template.format( **locals() )

  #-----------------------------------------------------------------------
  # visit_Reduce
  #-----------------------------------------------------------------------

  def visit_Reduce( s, node ):
    op_t = type(node.op)
    reduce_ops = { bir.BitAnd : '&', bir.BitOr : '|', bir.BitXor : '^' }
    if op_t not in reduce_ops:
      raise SVerilogTranslationError( s.blk, node,
          f"unrecognized operator {op_t} for reduce method!" )
    value = s.visit( node.value )
    op = reduce_ops[ op_t ]
    return f"( {op} {value} )"

  #-----------------------------------------------------------------------
  # visit_SizeCast
  #-----------------------------------------------------------------------

  def visit_SizeCast( s, node ):
    nbits = node.nbits
    value = s.visit( node.value )
    if hasattr( node, "_value" ):
      if isinstance( node._value, Bits ):
        value = int(node._value)
      else:
        value = node._value
      return f"{nbits}'d{value}"

    return f"{nbits}'( {value} )"

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

    s.check_res( node, attr )

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
      # Unpacked array index must be a static constant integer!
      # if idx is None and not isinstance(subtype, (rt.Port, rt.Wire, rt.Const)):
        # raise SVerilogTranslationError( s.blk, node.ast,
# 'index of unpacked array {} must be a constant integer expression!'. \
            # format(node.value) )

      if isinstance( subtype, ( rt.Port, rt.Wire, rt.Const ) ):
        return f'{value}[{idx}]'
      else:
        return f'{value}__{idx}'

    # Index on a signal
    elif isinstance( Type, rt.Signal ):

      # Packed index
      if Type.is_packed_indexable():
        return f'{value}[{idx}]'
      # Bit selection
      elif isinstance( Type.get_dtype(), rdt.Vector ):
        return f'{value}[{idx}]'
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

    return f'{value}[{upper}:{lower}]'

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
    return f'__const__{node.name}'

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
