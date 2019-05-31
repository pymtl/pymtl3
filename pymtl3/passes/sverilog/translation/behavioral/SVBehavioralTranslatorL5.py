#=========================================================================
# SVBehavioralTranslatorL5.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 18, 2019
"""Provide the level 5 SystemVerilog translator implementation."""
from __future__ import absolute_import, division, print_function

from pymtl3.passes.rtlir import BehavioralRTLIR as bir
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.sverilog.errors import SVerilogTranslationError
from pymtl3.passes.translator.behavioral.BehavioralTranslatorL5 import (
    BehavioralTranslatorL5,
)

from .SVBehavioralTranslatorL4 import (
    BehavioralRTLIRToSVVisitorL4,
    SVBehavioralTranslatorL4,
)


class SVBehavioralTranslatorL5(
    SVBehavioralTranslatorL4, BehavioralTranslatorL5):

  def _get_rtlir2sv_visitor( s ):
    return BehavioralRTLIRToSVVisitorL5

#-------------------------------------------------------------------------
# BehavioralRTLIRToSVVisitorL5
#-------------------------------------------------------------------------

class BehavioralRTLIRToSVVisitorL5( BehavioralRTLIRToSVVisitorL4 ):
  """Visitor that translates RTLIR to SystemVerilog for a single upblk."""

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):
    """Return the SystemVerilog representation of an attribute.
    
    Add support for subcomponent attributes in L5.
    """
    # Generate subcomponent attribute
    if isinstance( node.value.Type, rt.Component ) and\
       not isinstance( node.value, bir.Base ):

      value = s.visit( node.value )
      attr = node.attr
      return '{value}${attr}'.format( **locals() )

    return super( BehavioralRTLIRToSVVisitorL5, s ).visit_Attribute( node )
