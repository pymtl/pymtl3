#=========================================================================
# YosysBehavioralTranslatorL2.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Provide the yosys-compatible SystemVerilog L2 behavioral translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.passes.sverilog.translation.behavioral.SVBehavioralTranslatorL2 import (
    BehavioralRTLIRToSVVisitorL2,
    SVBehavioralTranslatorL2,
)
from pymtl3.passes.sverilog.util.utility import make_indent

from .YosysBehavioralTranslatorL1 import (
    YosysBehavioralRTLIRToSVVisitorL1,
    YosysBehavioralTranslatorL1,
)


class YosysBehavioralTranslatorL2(
    YosysBehavioralTranslatorL1, SVBehavioralTranslatorL2 ):

  def _get_rtlir2sv_visitor( s ):
    return YosysBehavioralRTLIRToSVVisitorL2

  def rtlir_tr_behavioral_tmpvars( s, tmpvars ):
    _tmpvars = []
    for tmpvar in tmpvars:
      _tmpvars += tmpvar
    make_indent( _tmpvars, 1 )
    return '\n'.join( _tmpvars )

class YosysBehavioralRTLIRToSVVisitorL2(
    YosysBehavioralRTLIRToSVVisitorL1, BehavioralRTLIRToSVVisitorL2 ):

  #-----------------------------------------------------------------------
  # visit_If
  #-----------------------------------------------------------------------

  def visit_If( s, node ):
    node.cond._top_expr = 1
    return super( YosysBehavioralRTLIRToSVVisitorL2, s ).visit_If( node )

  #-----------------------------------------------------------------------
  # visit_For
  #-----------------------------------------------------------------------

  def visit_For( s, node ):
    node.start._top_expr = 1
    node.end._top_expr = 1
    node.step._top_expr = 1
    return super( YosysBehavioralRTLIRToSVVisitorL2, s ).visit_For( node )

  #-----------------------------------------------------------------------
  # visit_IfExp
  #-----------------------------------------------------------------------

  def visit_IfExp( s, node ):
    node.cond._top_expr = 1
    node.body._top_expr = 1
    node.orelse._top_expr = 1
    return super( YosysBehavioralRTLIRToSVVisitorL2, s ).visit_IfExp( node )

  #-----------------------------------------------------------------------
  # visit_UnaryOp
  #-----------------------------------------------------------------------

  def visit_UnaryOp( s, node ):
    node.operand._top_expr = 1
    return super( YosysBehavioralRTLIRToSVVisitorL2, s ).visit_UnaryOp( node )

  #-----------------------------------------------------------------------
  # visit_BoolOp
  #-----------------------------------------------------------------------

  def visit_BoolOp( s, node ):
    for child in node.values:
      child._top_expr = 1
    return super( YosysBehavioralRTLIRToSVVisitorL2, s ).visit_BoolOp( node )

  #-----------------------------------------------------------------------
  # visit_BinOp
  #-----------------------------------------------------------------------

  def visit_BinOp( s, node ):
    node.left._top_expr = 1
    node.right._top_expr = 1
    return super( YosysBehavioralRTLIRToSVVisitorL2, s ).visit_BinOp( node )

  #-----------------------------------------------------------------------
  # visit_Compare
  #-----------------------------------------------------------------------

  def visit_Compare( s, node ):
    node.left._top_expr = 1
    node.right._top_expr = 1
    return super( YosysBehavioralRTLIRToSVVisitorL2, s ).visit_Compare( node )
