#=========================================================================
# YosysBehavioralTranslatorL4.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Provide the yosys-compatible SystemVerilog L4 behavioral translator."""

from pymtl3.passes.backends.verilog.translation.behavioral.VBehavioralTranslatorL4 import (
    BehavioralRTLIRToVVisitorL4,
    VBehavioralTranslatorL4,
)
from pymtl3.passes.rtlir import RTLIRType as rt

from .YosysBehavioralTranslatorL3 import (
    YosysBehavioralRTLIRToVVisitorL3,
    YosysBehavioralTranslatorL3,
)


class YosysBehavioralTranslatorL4(
    YosysBehavioralTranslatorL3, VBehavioralTranslatorL4 ):

  def _get_rtlir2v_visitor( s ):
    return YosysBehavioralRTLIRToVVisitorL4

class YosysBehavioralRTLIRToVVisitorL4(
    YosysBehavioralRTLIRToVVisitorL3, BehavioralRTLIRToVVisitorL4 ):

  def visit_Attribute( s, node ):
    """Return the SystemVerilog representation of an attribute.

    Add support for accessing interface attribute in L4.
    """
    if isinstance( node.value.Type, rt.InterfaceView ):
      value = s.visit( node.value )
      s.signal_expr_prologue( node )
      attr = node.attr
      s.check_res( node, attr )
      node.sexpr['s_attr'] += "__{}"
      node.sexpr['attr'].append( attr )
      return s.signal_expr_epilogue(node, f"{value}.{attr}")

    else:
      return super().visit_Attribute( node )
