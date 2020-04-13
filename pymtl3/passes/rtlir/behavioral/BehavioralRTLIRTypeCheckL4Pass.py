#=========================================================================
# BehavioralRTLIRTypeCheckL4Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 30, 2019
"""Provide L4 behavioral RTLIR type check pass."""

from pymtl3.passes.rtlir.errors import PyMTLTypeError
from pymtl3.passes.rtlir.rtype import RTLIRType as rt

from .BehavioralRTLIRTypeCheckL3Pass import (
    BehavioralRTLIRTypeCheckL3Pass,
    BehavioralRTLIRTypeCheckVisitorL3,
)


class BehavioralRTLIRTypeCheckL4Pass( BehavioralRTLIRTypeCheckL3Pass ):
  def get_visitor_class( s ):
    return BehavioralRTLIRTypeCheckVisitorL4

class BehavioralRTLIRTypeCheckVisitorL4( BehavioralRTLIRTypeCheckVisitorL3 ):

  def __init__( s, component, freevars, accessed, tmpvars, rtlir_getter ):
    super().__init__( component, freevars, accessed, tmpvars, rtlir_getter )
    s.type_expect[ 'Attribute' ] = (
      ( 'value', (rt.Component, rt.Signal, rt.InterfaceView),
                 'the base of an attribute must be one of: module, struct, interface!' ),
    )

  def visit_Attribute( s, node ):
    if isinstance( node.value.Type, rt.InterfaceView ):
      if not node.value.Type.has_property( node.attr ):
        raise PyMTLTypeError( s.blk, node.ast,
          f'{dtype.get_name()} does not have field {node.attr}!' )
      node.Type = node.value.Type.get_property( node.attr )
    else:
      super().visit_Attribute( node )

  def visit_Index( s, node ):
    if isinstance( node.value.Type, rt.Array ) and \
       isinstance( node.value.Type.get_sub_type(), rt.InterfaceView ):
      node.Type = node.value.Type.get_next_dim_type()

    else:
      super().visit_Index( node )
