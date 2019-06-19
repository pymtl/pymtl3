#=========================================================================
# BehavioralRTLIRTypeCheckL3Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 30, 2019
"""Provide L3 behavioral RTLIR type check pass."""
from __future__ import absolute_import, division, print_function

from collections import OrderedDict

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
    m._pass_behavioral_rtlir_type_check.rtlir_freevars = OrderedDict()
    m._pass_behavioral_rtlir_type_check.rtlir_tmpvars = OrderedDict()
    m._pass_behavioral_rtlir_type_check.rtlir_accessed = set()

    visitor = BehavioralRTLIRTypeCheckVisitorL3(
      m,
      m._pass_behavioral_rtlir_type_check.rtlir_freevars,
      m._pass_behavioral_rtlir_type_check.rtlir_accessed,
      m._pass_behavioral_rtlir_type_check.rtlir_tmpvars
    )

    for blk in m.get_update_blocks():
      visitor.enter( blk, m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] )

class BehavioralRTLIRTypeCheckVisitorL3( BehavioralRTLIRTypeCheckVisitorL2 ):
  def __init__( s, component, freevars, accessed, tmpvars ):
    super( BehavioralRTLIRTypeCheckVisitorL3, s ). \
        __init__( component, freevars, accessed, tmpvars )
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
            dtype.get_name(), node.attr ) )
      dtype = dtype.get_property( node.attr )
      if isinstance( node.value.Type, rt.Port ):
        rtype = rt.Port( node.value.Type.get_direction(), dtype )
      elif isinstance( node.value.Type, rt.Wire ):
        rtype = rt.Wire( dtype )
      elif isinstance( node.value.Type, rt.Const ):
        obj = node.value.Type.get_object()
        if obj is None:
          rtype = rt.Const( dtype )
        else:
          try:
            rtype = rt.Const( dtype, getattr( obj, node.attr ) )
          except AttributeError:
            rtype = rt.Const( dtype )
      else:
        raise PyMTLTypeError( s.blk, node.ast,
          'unrecognized signal type {}!'.format( node.value.Type ) )
      node.Type = rtype

    else:
      super( BehavioralRTLIRTypeCheckVisitorL3, s ).visit_Attribute( node )

  def visit_StructInst( s, node ):
    cls = node.struct

    try:
      type_instance = cls()
    except TypeError:
      raise PyMTLTypeError( s.blk, node.ast,
""""\
__init__ of BitStruct {} should take 0 arguments! You can achieve this by
adding default values to the arguments.
""".format( cls.__name__ ) )

    dtype = rdt.get_rtlir_dtype( cls() )
    all_properties = dtype.get_all_properties()

    if len( all_properties ) != len( node.values ):
      raise PyMTLTypeError( s.blk, node.ast,
        "BitStruct {} has {} fields but only {} arguments are given!". \
            format(cls.__name__, len(all_properties), len(node.values)) )

    all_types = zip( node.values, all_properties )
    for idx, ( value, ( name, field ) ) in enumerate( all_types ):
      s.visit( value )
      # Expect each argument to be a signal
      if not isinstance( value.Type, rt.Signal ):
        raise PyMTLTypeError( s.blk, node.ast,
          "argument #{} has type {} but not a signal!". \
              format( idx, value.Type ) )
      v_dtype = value.Type.get_dtype()
      # Expect each argument to have data type which corresponds to the field
      if v_dtype != field:
        raise PyMTLTypeError( s.blk, node.ast,
          "Expected argument#{} ( field {} ) to have type {}, but got {}.". \
              format( idx, name, field, v_dtype ) )

    node.Type = rt.Const( dtype )
