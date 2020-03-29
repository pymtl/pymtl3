#=========================================================================
# YosysBehavioralTranslatorL2.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Provide the yosys-compatible SystemVerilog L2 behavioral translator."""

from pymtl3.passes.backends.verilog.translation.behavioral.VBehavioralTranslatorL2 import (
    BehavioralRTLIRToVVisitorL2,
    VBehavioralTranslatorL2,
)
from pymtl3.passes.backends.verilog.util.utility import make_indent

from .YosysBehavioralTranslatorL1 import (
    YosysBehavioralRTLIRToVVisitorL1,
    YosysBehavioralTranslatorL1,
)


class YosysBehavioralTranslatorL2(
    YosysBehavioralTranslatorL1, VBehavioralTranslatorL2 ):

  def _get_rtlir2v_visitor( s ):
    return YosysBehavioralRTLIRToVVisitorL2

  def rtlir_tr_behavioral_tmpvars( s, tmpvars ):
    _tmpvars = []
    for tmpvar in tmpvars:
      _tmpvars += tmpvar
    make_indent( _tmpvars, 1 )
    return '\n'.join( _tmpvars )

class YosysBehavioralRTLIRToVVisitorL2(
    YosysBehavioralRTLIRToVVisitorL1, BehavioralRTLIRToVVisitorL2 ):

  #-----------------------------------------------------------------------
  # visit_If
  #-----------------------------------------------------------------------

  def visit_If( s, node ):
    node.cond._top_expr = 1
    return super().visit_If( node )

  #-----------------------------------------------------------------------
  # visit_For
  #-----------------------------------------------------------------------

  def visit_For( s, node ):
    node.start._top_expr = 1
    node.end._top_expr = 1
    node.step._top_expr = 1

    # Yosys-comptabile Verilog for loop
    src      = []
    body     = []
    loop_var = s.visit( node.var )
    start    = s.visit( node.start )
    end      = s.visit( node.end )

    loop_var = "__loopvar__" + s.blk.__name__ + "_" + loop_var
    if loop_var not in s.loopvars:
      s.loopvars.add( loop_var )

    begin    = ' begin' if len( node.body ) > 1 else ''

    cmp_op   = '<' if node.step.value > 0 else '<'
    inc_op   = '+' if node.step.value > 0 else '-'

    step_abs = s.visit( node.step )
    step_abs = step_abs if node.step.value > 0 else step_abs[ 1 : ]

    for stmt in node.body:
      body.extend( s.visit( stmt ) )
    make_indent( body, 1 )

    for_begin = \
      'for ( {v} = {s}; {v} {comp} {t}; {v} = {v} {inc} {stp} ){begin}'.format(
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
  # visit_IfExp
  #-----------------------------------------------------------------------

  def visit_IfExp( s, node ):
    node.cond._top_expr = 1
    node.body._top_expr = 1
    node.orelse._top_expr = 1
    return super().visit_IfExp( node )

  #-----------------------------------------------------------------------
  # visit_UnaryOp
  #-----------------------------------------------------------------------

  def visit_UnaryOp( s, node ):
    node.operand._top_expr = 1
    return super().visit_UnaryOp( node )

  #-----------------------------------------------------------------------
  # visit_BoolOp
  #-----------------------------------------------------------------------

  # def visit_BoolOp( s, node ):
  #   for child in node.values:
  #     child._top_expr = 1
  #   return super().visit_BoolOp( node )

  #-----------------------------------------------------------------------
  # visit_BinOp
  #-----------------------------------------------------------------------

  def visit_BinOp( s, node ):
    node.left._top_expr = 1
    node.right._top_expr = 1
    return super().visit_BinOp( node )

  #-----------------------------------------------------------------------
  # visit_Compare
  #-----------------------------------------------------------------------

  def visit_Compare( s, node ):
    node.left._top_expr = 1
    node.right._top_expr = 1
    return super().visit_Compare( node )

  #-----------------------------------------------------------------------
  # visit_LoopVar
  #-----------------------------------------------------------------------

  def visit_LoopVar( s, node ):
    s.check_res( node, node.name )
    nbits = node.Type.get_dtype().get_length()
    return f"{nbits}'(__loopvar__{s.blk.__name__}_{node.name})"
