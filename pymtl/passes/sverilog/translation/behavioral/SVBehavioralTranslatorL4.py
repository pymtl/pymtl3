#=========================================================================
# SVBehavioralTranslatorL4.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 18, 2019
"""Provide the level 4 SystemVerilog translator implementation."""

from pymtl.passes.translator.behavioral.BehavioralTranslatorL4 \
    import BehavioralTranslatorL4
from pymtl.passes.sverilog.errors import SVerilogTranslationError
from pymtl.passes.rtlir import RTLIRType as rt

from SVBehavioralTranslatorL3 import BehavioralRTLIRToSVVisitorL3, \
                                     SVBehavioralTranslatorL3

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
      return '{value}_${attr}'.format( **locals() )
    else:
      return super( BehavioralRTLIRToSVVisitorL4, s ).visit_Attribute( node )
