#=========================================================================
# VBehavioralTranslatorL5.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 18, 2019
"""Provide the level 5 SystemVerilog translator implementation."""

from pymtl3.passes.backends.generic.behavioral.BehavioralTranslatorL5 import (
    BehavioralTranslatorL5,
)
from pymtl3.passes.rtlir import BehavioralRTLIR as bir
from pymtl3.passes.rtlir import RTLIRType as rt

from ...errors import VerilogTranslationError
from .VBehavioralTranslatorL4 import (
    BehavioralRTLIRToVVisitorL4,
    VBehavioralTranslatorL4,
)


class VBehavioralTranslatorL5(
    VBehavioralTranslatorL4, BehavioralTranslatorL5):

  def _get_rtlir2v_visitor( s ):
    return BehavioralRTLIRToVVisitorL5

#-------------------------------------------------------------------------
# BehavioralRTLIRToVVisitorL5
#-------------------------------------------------------------------------

class BehavioralRTLIRToVVisitorL5( BehavioralRTLIRToVVisitorL4 ):
  """Visitor that translates RTLIR to SystemVerilog for a single upblk."""

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):
    """Return the SystemVerilog representation of an attribute.

    Add support for subcomponent attributes in L5.
    """
    # Generate subcomponent attribute
    if isinstance( node.value.Type, rt.Component ) and \
       not isinstance( node.value, bir.Base ):

      value = s.visit( node.value )
      attr = node.attr
      s.check_res( node, attr )
      return s.process_unpacked_q( node,
                f'{value}__{attr}',
                f'{value}__{attr}{{}}' )

    return super().visit_Attribute( node )

  #-----------------------------------------------------------------------
  # visit_Index
  #-----------------------------------------------------------------------

  def visit_Index( s, node ):
    if isinstance( node.value.Type, rt.Array ) and \
       isinstance( node.value.Type.get_sub_type(), rt.Component ):
      idx = s.visit( node.idx )
      s._unpacked_q.appendleft(idx)
      value = s.visit( node.value )
      return value

    else:
      return super().visit_Index( node )
