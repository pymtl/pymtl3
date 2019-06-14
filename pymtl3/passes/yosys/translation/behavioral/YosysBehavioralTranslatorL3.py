#=========================================================================
# YosysBehavioralTranslatorL3.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Provide the yosys-compatible SystemVerilog L3 behavioral translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.sverilog.errors import SVerilogTranslationError
from pymtl3.passes.sverilog.translation.behavioral.SVBehavioralTranslatorL3 import (
    BehavioralRTLIRToSVVisitorL3,
    SVBehavioralTranslatorL3,
)

from .YosysBehavioralTranslatorL2 import (
    YosysBehavioralRTLIRToSVVisitorL2,
    YosysBehavioralTranslatorL2,
)


class YosysBehavioralTranslatorL3(
    YosysBehavioralTranslatorL2, SVBehavioralTranslatorL3 ):

  def _get_rtlir2sv_visitor( s ):
    return YosysBehavioralRTLIRToSVVisitorL3

class YosysBehavioralRTLIRToSVVisitorL3(
    YosysBehavioralRTLIRToSVVisitorL2, BehavioralRTLIRToSVVisitorL3 ):
  """IR visitor that generates yosys-compatible SystemVerilog code.
  
  This visitor differs from the canonical SystemVerilog visitor in that
  it name-mangles each struct signal into multiple signals for all fields
  in the struct. We don't use SystemVerilog struct here because yosys
  does not support that yet.
  """

  def visit_Attribute( s, node ):
    """Return the SystemVerilog representation of an attribute.
    
    Add support for accessing struct attribute in L3.
    """
    if isinstance( node.value.Type, rt.Signal ):
      if isinstance( node.value.Type, rt.Const ):
        raise SVerilogTranslationError( s.blk, node,
          "attribute ({}) of constant struct instance ({}) is not supported!". \
            format( node.attr, node.value ) )

      if isinstance( node.value.Type.get_dtype(), rdt.Struct ):
        value = s.visit( node.value )
        s.signal_expr_prologue( node )
        attr = node.attr
        s.check_res( node, attr )
        node.sexpr['s_attr'] += "${}"
        node.sexpr['attr'].append( attr )
        return s.signal_expr_epilogue(node, "{value}.{attr}".format(**locals()))

    return super( YosysBehavioralRTLIRToSVVisitorL3, s ).visit_Attribute( node )
