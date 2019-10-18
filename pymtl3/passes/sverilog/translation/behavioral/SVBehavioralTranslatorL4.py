#=========================================================================
# SVBehavioralTranslatorL4.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 18, 2019
"""Provide the level 4 SystemVerilog translator implementation."""

from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.sverilog.errors import SVerilogTranslationError
from pymtl3.passes.translator.behavioral.BehavioralTranslatorL4 import (
    BehavioralTranslatorL4,
)

from .SVBehavioralTranslatorL3 import (
    BehavioralRTLIRToSVVisitorL3,
    SVBehavioralTranslatorL3,
)


class SVBehavioralTranslatorL4(
    SVBehavioralTranslatorL3, BehavioralTranslatorL4):

  def _get_rtlir2sv_visitor( s ):
    return BehavioralRTLIRToSVVisitorL4

#-------------------------------------------------------------------------
# BehavioralRTLIRToSVVisitorL4
#-------------------------------------------------------------------------

class BehavioralRTLIRToSVVisitorL4( BehavioralRTLIRToSVVisitorL3 ):
  """Visitor that translates RTLIR to SystemVerilog for a single upblk."""

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):
    """Return the SystemVerilog representation of an attribute.

    Add support for interface attributes in L4. We just name mangle every
    signal in an interface instead of constructing a SystemVerilog interface
    and instantiating new interfaces from it.
    """
    if isinstance( node.value.Type, rt.InterfaceView ):
      value = s.visit( node.value )
      attr = node.attr
      s.check_res( node, attr )
      return f'{value}__{attr}'
    else:
      return super().visit_Attribute( node )

  #-----------------------------------------------------------------------
  # visit_Index
  #-----------------------------------------------------------------------

  def visit_Index( s, node ):
    if isinstance( node.value.Type, rt.Array ) and \
        isinstance( node.value.Type.get_sub_type(), rt.InterfaceView ):
      try:
        nbits = node.idx._value
      except AttributeError:
        raise SVerilogTranslationError( s.blk, node,
          f'index of interface array {node.idx} must be a static constant expression!' )
      idx = int( nbits )
      value = s.visit( node.value )
      return f'{value}__{idx}'

    else:
      return super().visit_Index( node )
