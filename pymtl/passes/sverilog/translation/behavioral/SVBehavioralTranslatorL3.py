#=========================================================================
# SVBehavioralTranslatorL3.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 18, 2019
"""Provide the level 3 SystemVerilog translator implementation."""

from pymtl.passes.translator.behavioral.BehavioralTranslatorL3 \
    import BehavioralTranslatorL3
from pymtl.passes.sverilog.errors import SVerilogTranslationError
from pymtl.passes.rtlir import RTLIRType as rt
from pymtl.passes.rtlir import RTLIRDataType as rdt

from SVBehavioralTranslatorL2 import BehavioralRTLIRToSVVisitorL2, \
                                     SVBehavioralTranslatorL2

class SVBehavioralTranslatorL3(
    SVBehavioralTranslatorL2, BehavioralTranslatorL3 ):

  def _get_rtlir2sv_visitor( s ):
    return BehavioralRTLIRToSVVisitorL3

#-------------------------------------------------------------------------
# BehavioralRTLIRToSVVisitorL3
#-------------------------------------------------------------------------

class BehavioralRTLIRToSVVisitorL3( BehavioralRTLIRToSVVisitorL2 ):
  """Visitor that translates RTLIR to SystemVerilog for a single upblk."""

  #-----------------------------------------------------------------------
  # visit_StructInst
  #-----------------------------------------------------------------------

  def visit_StructInst( s, node ):
    raise SVerilogTranslationError( s.blk, node, "StrutctInst not supported yet" )

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):
    """Return the SystemVerilog representation of an attribute.
    
    Add support for accessing struct attribute in L3.
    """
    if isinstance( node.value.Type, rt.Signal ):
      if isinstance( node.value.Type, rt.Const ):
        raise SVerilogTranslationError( s.blk, node,
          "attribute ({}) of constant struct instance ({}) is not supported!". \
            format( node.attr, node.value ))

      if isinstance( node.value.Type.get_dtype(), rdt.Struct ):
        value = s.visit( node.value )
        attr = node.attr
        return '{value}.{attr}'.format( **locals() )

    return super( BehavioralRTLIRToSVVisitorL3, s ).visit_Attribute( node )
