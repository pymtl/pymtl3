#=========================================================================
# BehavioralRTLIRTypeCheckL3Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 30, 2019
"""Provide L3 behavioral RTLIR type check pass."""
from __future__ import absolute_import, division, print_function

from pymtl import *
from pymtl.passes import BasePass
from pymtl.passes.BasePass import PassMetadata
from pymtl.passes.rtlir.RTLIRType import *
from pymtl.passes.rtlir.utility import freeze

from .BehavioralRTLIR import *
from .BehavioralRTLIRTypeCheckL2Pass import BehavioralRTLIRTypeCheckVisitorL2
from .errors import PyMTLTypeError


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
    super( BehavioralRTLIRTypeCheckVisitorL3, s ).\
        __init__( component, freevars, tmpvars )
    s.type_expect[ 'Attribute' ] = {
      'value':( (Component, Signal),
        'the base of an attribute must be one of: component, signal!' )
    }

  def visit_Attribute( s, node ):
    if isinstance( node.value.Type, Signal ):
      dtype = node.value.Type.get_dtype()
      if not isinstance( dtype, Struct ):
        raise PyMTLTypeError(
          s.blk, node.ast, 'attribute base should be a struct signal!'
        )
      if not dtype.has_property( node.attr ):
        raise PyMTLTypeError(
          s.blk, node.ast, '{} does not have field {}!'.format(
            dtype.get_name(), node.attr ))
      dtype = dtype.get_property( node.attr )
      if isinstance( node.value.Type, Port ):
        rtype = Port( node.value.Type.get_direction(), dtype )
      elif isinstance( node.value.Type, Wire ):
        rtype = Wire( dtype )
      else:
        raise PyMTLTypeError(
          s.blk, node.ast, 'constant struct is not supported!' )
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
    assert Type is not bool and not issubclass( Type, Bits ),\
        "internal error: StructInst did not get struct Type!"
    raise NotImplementedError()
