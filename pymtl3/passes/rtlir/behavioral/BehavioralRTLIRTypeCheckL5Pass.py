#=========================================================================
# BehavioralRTLIRTypeCheckL5Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 30, 2019
"""Provide L5 behavioral RTLIR type check pass."""

from pymtl3.passes.rtlir.errors import PyMTLTypeError
from pymtl3.passes.rtlir.rtype import RTLIRType as rt

from .BehavioralRTLIRTypeCheckL4Pass import (
    BehavioralRTLIRTypeCheckL4Pass,
    BehavioralRTLIRTypeCheckVisitorL4,
)


class BehavioralRTLIRTypeCheckL5Pass( BehavioralRTLIRTypeCheckL4Pass ):
  def get_visitor_class( s ):
    return BehavioralRTLIRTypeCheckVisitorL5

class BehavioralRTLIRTypeCheckVisitorL5( BehavioralRTLIRTypeCheckVisitorL4 ):

  def visit_Index( s, node ):
    """Type check the index node."""
    if isinstance( node.value.Type, rt.Array ) and \
       isinstance( node.value.Type.get_sub_type(), rt.Component ):
      node.Type = node.value.Type.get_next_dim_type()

    else:
      super().visit_Index( node )

  def visit_Attribute( s, node ):
    """Type check an attribute.

    Since only the ports of a subcomponent can be accessed, no explicit
    cross-hierarchy access detection is needed.
    """
    # Attributes of subcomponent can only access ports
    if isinstance( node.value.Type, rt.Component ) and \
       node.value.Type.get_name() != s.component.__class__.__name__:
      if not node.value.Type.has_property( node.attr ):
        raise PyMTLTypeError( s.blk, node.ast,
          f'rt.Component {node.value.Type.get_name()} does not have attribute {node.attr}!' )
      prop = node.value.Type.get_property( node.attr )
      if not rt._is_of_type( prop, ( rt.Port, rt.InterfaceView ) ):
        raise PyMTLTypeError( s.blk, node.ast,
          f'{node.attr} is not a port of {node.value.Type.get_name()} subcomponent!' )
      node.Type = prop
    else:
      super().visit_Attribute( node )
