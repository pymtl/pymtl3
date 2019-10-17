#=========================================================================
# SVBehavioralTranslatorL2.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 18, 2019
"""Provide the level 2 SystemVerilog translator implementation."""

from pymtl3.passes.rtlir import BehavioralRTLIR as bir
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.sverilog.util.utility import make_indent
from pymtl3.passes.translator.behavioral.BehavioralTranslatorL2 import (
    BehavioralTranslatorL2,
)

from .SVBehavioralTranslatorL1 import (
    BehavioralRTLIRToSVVisitorL1,
    SVBehavioralTranslatorL1,
)


class SVBehavioralTranslatorL2( SVBehavioralTranslatorL1, BehavioralTranslatorL2 ):

  def _get_rtlir2sv_visitor( s ):
    return BehavioralRTLIRToSVVisitorL2

  def rtlir_tr_behavioral_tmpvars( s, tmpvars ):
    make_indent( tmpvars, 1 )
    return '\n'.join( tmpvars )

  def rtlir_tr_behavioral_tmpvar( s, id_, upblk_id, dtype ):
    return s.rtlir_tr_wire_decl(
        "__tmpvar__"+upblk_id+'_'+id_, rt.Wire(dtype['raw_dtype']),
        s.rtlir_tr_unpacked_array_type(None), dtype )

#-------------------------------------------------------------------------
# BehavioralRTLIRToSVVisitorL2
#-------------------------------------------------------------------------

class BehavioralRTLIRToSVVisitorL2( BehavioralRTLIRToSVVisitorL1 ):
  """Visitor that translates RTLIR to SystemVerilog for a single upblk."""

  def __init__( s, is_reserved ):
    super().__init__( is_reserved )

    # The dictionary of operator-character pairs
    s.ops = {
      # Unary operators
      bir.Invert : '~', bir.Not : '!', bir.UAdd : '+', bir.USub : '-',
      # Boolean operators
      bir.And : '&&', bir.Or : '||',
      # Binary operators
      bir.Add : '+', bir.Sub : '-', bir.Mult : '*', bir.Div : '/',
      bir.Mod : '%', bir.Pow : '**',
      bir.ShiftLeft : '<<', bir.ShiftRightLogic : '>>',
      bir.BitAnd : '&', bir.BitOr : '|', bir.BitXor : '^',
      # Comparison operators
      bir.Eq : '==', bir.NotEq : '!=', bir.Lt : '<', bir.LtE : '<=',
      bir.Gt : '>', bir.GtE : '>='
    }

  def visit_expr_wrap( s, node ):
    """Return expressions selectively wrapped with brackets."""
    if isinstance( node,
        ( bir.IfExp, bir.UnaryOp, bir.BoolOp, bir.BinOp, bir.Compare ) ):
      return f"( {s.visit(node)} )"
    else:
      return s.visit( node )

  #-----------------------------------------------------------------------
  # Statements
  #-----------------------------------------------------------------------
  # All statement nodes return a list of strings.

  #-----------------------------------------------------------------------
  # visit_If
  #-----------------------------------------------------------------------

  def visit_If( s, node ):
    src    = []
    body   = []
    orelse = []

    # Grab condition, if-body, and orelse-body
    cond = s.visit( node.cond )
    for stmt in node.body:
      body.extend( s.visit( stmt ) )
    make_indent( body, 1 )
    for stmt in node.orelse:
      orelse.extend( s.visit( stmt ) )

    # Assemble the statement, starting with if-body
    if_begin   = f'if ( {cond} ) begin'
    src.extend( [ if_begin ] )
    src.extend( body )

    # if len( node.body ) > 1:
    src.extend( [ 'end' ] )

    # If orelse-body is not empty, add it to the list of strings
    if node.orelse != []:

      # If an if statement is the only statement in the orelse-body
      if len( node.orelse ) == 1 and isinstance( node.orelse[ 0 ], bir.If ):
        # No indent will be added, also append if-begin to else-begin
        else_begin = f'else {orelse[0]}'
        orelse = orelse[ 1 : ]

      # Else indent orelse-body
      else:
        else_begin = 'else' + ( ' begin' if len( node.orelse ) > 1 else '' )
        make_indent( orelse, 1 )

      src.extend( [ else_begin ] )
      src.extend( orelse )
      if len( node.orelse ) > 1:
        src.extend( [ 'end' ] )

    return src

  #-----------------------------------------------------------------------
  # visit_For
  #-----------------------------------------------------------------------

  def visit_For( s, node ):
    src      = []
    body     = []
    loop_var = s.visit( node.var )
    start    = s.visit( node.start )
    end      = s.visit( node.end )

    begin    = ' begin' if len( node.body ) > 1 else ''

    cmp_op   = '<' if node.step.value > 0 else '<'
    inc_op   = '+' if node.step.value > 0 else '-'

    step_abs = s.visit( node.step )
    step_abs = step_abs if node.step.value > 0 else step_abs[ 1 : ]

    for stmt in node.body:
      body.extend( s.visit( stmt ) )
    make_indent( body, 1 )

    for_begin = \
      'for ( int {v} = {s}; {v} {comp} {t}; {v} {inc}= {stp} ){begin}'.format(
      v = loop_var, s = start, t = end, stp = step_abs,
      comp = cmp_op, inc = inc_op, begin = begin
    )

    # Assemble for statement
    src.extend( [ for_begin ] )
    src.extend( body )

    if len( node.body ) > 1:
      src.extend( [ 'end' ] )

    return src

  #-----------------------------------------------------------------------
  # Expressions
  #-----------------------------------------------------------------------
  # All expression nodes return a single string.

  #-----------------------------------------------------------------------
  # visit_IfExp
  #-----------------------------------------------------------------------

  def visit_IfExp( s, node ):
    cond  = s.visit_expr_wrap( node.cond )
    true  = s.visit( node.body )
    false = s.visit( node.orelse )

    return f'{cond} ? {true} : {false}'

  #-----------------------------------------------------------------------
  # visit_UnaryOp
  #-----------------------------------------------------------------------

  def visit_UnaryOp( s, node ):
    op      = s.ops[ type( node.op ) ]
    operand = s.visit_expr_wrap( node.operand )

    return f'{op}{operand}'

  #-----------------------------------------------------------------------
  # visit_BoolOp
  #-----------------------------------------------------------------------

  def visit_BoolOp( s, node ):
    op     = s.ops[ type( node.op ) ]
    values = []

    for value in node.values:
      values.append( s.visit_expr_wrap( value ) )
    src = f' {op} '.join( values )

    return src

  #-----------------------------------------------------------------------
  # visit_BinOp
  #-----------------------------------------------------------------------

  def visit_BinOp( s, node ):
    op  = s.ops[ type( node.op ) ]
    lhs = s.visit_expr_wrap( node.left )
    rhs = s.visit_expr_wrap( node.right )

    return f'{lhs} {op} {rhs}'

  #-----------------------------------------------------------------------
  # visit_Compare
  #-----------------------------------------------------------------------

  def visit_Compare( s, node ):
    op  = s.ops[ type( node.op ) ]
    lhs = s.visit_expr_wrap( node.left )
    rhs = s.visit_expr_wrap( node.right )

    return f'{lhs} {op} {rhs}'

  #-----------------------------------------------------------------------
  # visit_LoopVar
  #-----------------------------------------------------------------------

  def visit_LoopVar( s, node ):
    s.check_res( node, node.name )
    return node.name

  #-----------------------------------------------------------------------
  # visit_TmpVar
  #-----------------------------------------------------------------------

  def visit_TmpVar( s, node ):
    return f"__tmpvar__{node.upblk_name}_{node.name}"

  #-----------------------------------------------------------------------
  # visit_LoopVarDecl
  #-----------------------------------------------------------------------

  def visit_LoopVarDecl( s, node ):
    s.check_res( node, node.name )
    return node.name
