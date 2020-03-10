#=========================================================================
# BehavioralRTLIRTypeCheckL5Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 30, 2019
"""Provide L5 behavioral RTLIR type check pass."""

from collections import OrderedDict

from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.rtlir.errors import PyMTLTypeError
from pymtl3.passes.rtlir.rtype import RTLIRType as rt
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt

from .BehavioralRTLIRTypeCheckL4Pass import BehavioralRTLIRTypeCheckVisitorL4, \
    BehavioralRTLIRTypeEnforcerL4


class BehavioralRTLIRTypeCheckL5Pass( BasePass ):
  def __call__( s, m ):
    """Perform type checking on all RTLIR in rtlir_upblks."""
    if not hasattr( m, '_pass_behavioral_rtlir_type_check' ):
      m._pass_behavioral_rtlir_type_check = PassMetadata()
    m._pass_behavioral_rtlir_type_check.rtlir_freevars = OrderedDict()
    m._pass_behavioral_rtlir_type_check.rtlir_tmpvars = OrderedDict()
    m._pass_behavioral_rtlir_type_check.rtlir_accessed = set()

    type_checker = BehavioralRTLIRTypeCheckVisitorL5( m,
      m._pass_behavioral_rtlir_type_check.rtlir_freevars,
      m._pass_behavioral_rtlir_type_check.rtlir_accessed,
      m._pass_behavioral_rtlir_type_check.rtlir_tmpvars
    )
    type_enforcer = BehavioralRTLIRTypeEnforcerL5()

    for blk in m.get_update_block_order():
      type_checker.enter( blk, m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] )
      type_enforcer.enter( blk, m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] )

#-------------------------------------------------------------------------
# Type checker
#-------------------------------------------------------------------------

class BehavioralRTLIRTypeCheckVisitorL5( BehavioralRTLIRTypeCheckVisitorL4 ):
  def __init__( s, component, freevars, accessed, tmpvars ):
    super(). \
        __init__( component, freevars, accessed, tmpvars )

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
      if isinstance(node.Type, rt.Port) and isinstance(node.Type.get_dtype(), rdt.Vector):
        node._is_explicit = node.Type.get_dtype().is_explicit()
      else:
        node._is_explicit = True
    else:
      super().visit_Attribute( node )

  def visit_Index( s, node ):
    """Type check the index node."""
    if isinstance( node.value.Type, rt.Array ) and \
       isinstance( node.value.Type.get_sub_type(), rt.Component ):
      node.Type = node.value.Type.get_next_dim_type()
      node._is_explicit = True

    else:
      super().visit_Index( node )

#-------------------------------------------------------------------------
# Enforce types for all terms whose types are inferred (implicit)
#-------------------------------------------------------------------------

class BehavioralRTLIRTypeEnforcerL5( BehavioralRTLIRTypeEnforcerL4 ):

  def visit_Attribute( s, node ):
    if isinstance( node.value.Type, rt.Component ) and \
       node.value.Type.get_name() != s.component.__class__.__name__:
      s.generic_visit( node )
    else:
      super().visit_Attribute( node )

  def visit_Index( s, node ):
    if isinstance( node.value.Type, rt.Array ) and \
       isinstance( node.value.Type.get_sub_type(), rt.Component ):
      s.generic_visit( node )
    else:
      super().visit_Index( node )
