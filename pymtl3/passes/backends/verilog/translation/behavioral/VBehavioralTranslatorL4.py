#=========================================================================
# VBehavioralTranslatorL4.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 18, 2019
"""Provide the level 4 SystemVerilog translator implementation."""

from pymtl3.passes.backends.generic.behavioral.BehavioralTranslatorL4 import (
    BehavioralTranslatorL4,
)
from pymtl3.passes.rtlir import RTLIRType as rt

from ...errors import VerilogTranslationError
from .VBehavioralTranslatorL3 import (
    BehavioralRTLIRToVVisitorL3,
    VBehavioralTranslatorL3,
)


class VBehavioralTranslatorL4(
    VBehavioralTranslatorL3, BehavioralTranslatorL4):

  def _get_rtlir2v_visitor( s ):
    return BehavioralRTLIRToVVisitorL4

#-------------------------------------------------------------------------
# BehavioralRTLIRToVVisitorL4
#-------------------------------------------------------------------------

class BehavioralRTLIRToVVisitorL4( BehavioralRTLIRToVVisitorL3 ):
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
      return s.process_unpacked_q( node,
                f'{value}__{attr}',
                f'{value}__{attr}{{}}' )
    else:
      return super().visit_Attribute( node )

  #-----------------------------------------------------------------------
  # visit_Index
  #-----------------------------------------------------------------------

  def visit_Index( s, node ):
    if isinstance( node.value.Type, rt.Array ) and \
        isinstance( node.value.Type.get_sub_type(), rt.InterfaceView ):
      idx = s.visit( node.idx )
      s._unpacked_q.appendleft(idx)
      value = s.visit( node.value )
      return value

    else:
      return super().visit_Index( node )
