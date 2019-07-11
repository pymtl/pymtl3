#=========================================================================
# SVBehavioralTranslatorL3.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 18, 2019
"""Provide the level 3 SystemVerilog translator implementation."""
from __future__ import absolute_import, division, print_function

from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.sverilog.errors import SVerilogTranslationError
from pymtl3.passes.translator.behavioral.BehavioralTranslatorL3 import (
    BehavioralTranslatorL3,
)

from .SVBehavioralTranslatorL2 import (
    BehavioralRTLIRToSVVisitorL2,
    SVBehavioralTranslatorL2,
)


class SVBehavioralTranslatorL3(
    SVBehavioralTranslatorL2, BehavioralTranslatorL3 ):

  def _get_rtlir2sv_visitor( s ):
    return BehavioralRTLIRToSVVisitorL3

  def rtlir_tr_behavioral_freevar( s, id_, rtype, array_type, dtype, obj ):
    assert isinstance( rtype, rt.Const ), \
      '{} freevar should be a constant!'.format( id_ )
    if isinstance( rtype.get_dtype(), rdt.Struct ):
      return s.rtlir_tr_const_decl( '__const$'+id_, rtype, array_type, dtype, obj )
    else:
      return super( SVBehavioralTranslatorL3, s ).rtlir_tr_behavioral_freevar(
          id_, rtype, array_type, dtype, obj )

#-------------------------------------------------------------------------
# BehavioralRTLIRToSVVisitorL3
#-------------------------------------------------------------------------

class BehavioralRTLIRToSVVisitorL3( BehavioralRTLIRToSVVisitorL2 ):
  """Visitor that translates RTLIR to SystemVerilog for a single upblk."""

  #-----------------------------------------------------------------------
  # visit_StructInst
  #-----------------------------------------------------------------------

  def visit_StructInst( s, node ):
    values = list( map( s.visit, node.values ) )
    if len( values ) == 1:
      return values[0]
    else:
      cat_value = ", ".join( values )
      return "{{ {cat_value} }}".format( **locals() )

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):
    """Return the SystemVerilog representation of an attribute.
    
    Add support for accessing struct attribute in L3.
    """
    if isinstance( node.value.Type, rt.Signal ):
      # if isinstance( node.value.Type, rt.Const ):
        # raise SVerilogTranslationError( s.blk, node,
          # "attribute ({}) of constant struct instance ({}) is not supported!". \
            # format( node.attr, node.value ))

      if isinstance( node.value.Type.get_dtype(), rdt.Struct ):
        value = s.visit( node.value )
        attr = node.attr
        s.check_res( node, attr )
        return '{value}.{attr}'.format( **locals() )

    return super( BehavioralRTLIRToSVVisitorL3, s ).visit_Attribute( node )
