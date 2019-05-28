#=========================================================================
# BehavioralRTLIRTypeCheckL3Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 30, 2019
"""Provide L3 behavioral RTLIR type check pass."""
from __future__ import absolute_import, division, print_function

from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.rtlir.errors import PyMTLTypeError
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.rtlir.rtype import RTLIRType as rt

from .BehavioralRTLIRTypeCheckL2Pass import BehavioralRTLIRTypeCheckVisitorL2


class BehavioralRTLIRTypeCheckL3Pass( BasePass ):
  def __call__( s, m ):
    """Perform type checking on all RTLIR in rtlir_upblks."""
    if not hasattr( m, '_pass_behavioral_rtlir_type_check' ):
      m._pass_behavioral_rtlir_type_check = PassMetadata()
    m._pass_behavioral_rtlir_type_check.rtlir_freevars = {}
    m._pass_behavioral_rtlir_type_check.rtlir_tmpvars = {}

    visitor = BehavioralRTLIRTypeCheckVisitorL3(
      m,
      m._pass_behavioral_rtlir_type_check.rtlir_freevars,
      m._pass_behavioral_rtlir_type_check.rtlir_tmpvars
    )

    for blk in m.get_update_blocks():
      visitor.enter( blk, m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] )

class BehavioralRTLIRTypeCheckVisitorL3( BehavioralRTLIRTypeCheckVisitorL2 ):
  def __init__( s, component, freevars, tmpvars ):
    super( BehavioralRTLIRTypeCheckVisitorL3, s ). \
        __init__( component, freevars, tmpvars )
    s.type_expect[ 'Attribute' ] = {
      'value':( (rt.Component, rt.Signal),
        'the base of an attribute must be one of: component, signal!' )
    }

  def visit_Attribute( s, node ):
    if isinstance( node.value.Type, rt.Signal ):
      dtype = node.value.Type.get_dtype()
      if not isinstance( dtype, rdt.Struct ):
        raise PyMTLTypeError( s.blk, node.ast,
          'attribute base should be a struct signal!'
        )
      if not dtype.has_property( node.attr ):
        raise PyMTLTypeError( s.blk, node.ast,
          '{} does not have field {}!'.format(
            dtype.get_name(), node.attr ))
      dtype = dtype.get_property( node.attr )
      if isinstance( node.value.Type, rt.Port ):
        rtype = rt.Port( node.value.Type.get_direction(), dtype )
      elif isinstance( node.value.Type, rt.Wire ):
        rtype = rt.Wire( dtype )
      else:
        raise PyMTLTypeError( s.blk, node.ast,
          'constant struct is not supported!' )
      node.Type = rtype

    else:
      super( BehavioralRTLIRTypeCheckVisitorL3, s ).visit_Attribute( node )

  def visit_StructInst( s, node ):
    """Type check the struct instantiation node.

    TODO
    To instantiate a struct inside an upblk the instantiator needs to:
    1. guarantee to return an instance of the desired struct ( static
    analysis on a very limited subset of python syntax may be able to do
    this )
    2. say how it composes the parameters into a struct instance (
    translate the instantiator to its backend representation like a
    function in SV )
    """
    raise NotImplementedError()
