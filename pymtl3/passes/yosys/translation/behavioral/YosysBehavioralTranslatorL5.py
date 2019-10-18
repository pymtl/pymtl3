#=========================================================================
# YosysBehavioralTranslatorL5.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Provide the yosys-compatible SystemVerilog L5 behavioral translator."""

from pymtl3.passes.rtlir import BehavioralRTLIR as bir
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.sverilog.translation.behavioral.SVBehavioralTranslatorL5 import (
    BehavioralRTLIRToSVVisitorL5,
    SVBehavioralTranslatorL5,
)

from .YosysBehavioralTranslatorL4 import (
    YosysBehavioralRTLIRToSVVisitorL4,
    YosysBehavioralTranslatorL4,
)


class YosysBehavioralTranslatorL5(
    YosysBehavioralTranslatorL4, SVBehavioralTranslatorL5 ):

  def _get_rtlir2sv_visitor( s ):
    return YosysBehavioralRTLIRToSVVisitorL5

class YosysBehavioralRTLIRToSVVisitorL5(
    YosysBehavioralRTLIRToSVVisitorL4, BehavioralRTLIRToSVVisitorL5 ):

  def visit_Attribute( s, node ):
    """Return the SystemVerilog representation of an attribute.

    Add support for subcomponent attributes in L5.
    """
    # Generate subcomponent attribute
    if isinstance( node.value.Type, rt.Component ) and\
       not isinstance( node.value, bir.Base ):

      value = s.visit( node.value )
      s.signal_expr_prologue( node )
      attr = node.attr
      s.check_res( node, attr )
      node.sexpr['s_attr'] += "__{}"
      node.sexpr['attr'].append( attr )
      return s.signal_expr_epilogue(node, f"{value}.{attr}")

    return super().visit_Attribute( node )
