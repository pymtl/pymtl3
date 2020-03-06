#=========================================================================
# YosysBehavioralTranslatorL5.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Provide the yosys-compatible SystemVerilog L5 behavioral translator."""

from pymtl3.passes.backends.verilog.translation.behavioral.VBehavioralTranslatorL5 import (
    BehavioralRTLIRToVVisitorL5,
    VBehavioralTranslatorL5,
)
from pymtl3.passes.rtlir import BehavioralRTLIR as bir
from pymtl3.passes.rtlir import RTLIRType as rt

from .YosysBehavioralTranslatorL4 import (
    YosysBehavioralRTLIRToVVisitorL4,
    YosysBehavioralTranslatorL4,
)


class YosysBehavioralTranslatorL5(
    YosysBehavioralTranslatorL4, VBehavioralTranslatorL5 ):

  def _get_rtlir2v_visitor( s ):
    return YosysBehavioralRTLIRToVVisitorL5

class YosysBehavioralRTLIRToVVisitorL5(
    YosysBehavioralRTLIRToVVisitorL4, BehavioralRTLIRToVVisitorL5 ):

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
