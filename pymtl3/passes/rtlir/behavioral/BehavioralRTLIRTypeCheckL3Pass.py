#=========================================================================
# BehavioralRTLIRTypeCheckL3Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 30, 2019
"""Provide L3 behavioral RTLIR type check pass."""

from pymtl3.passes.rtlir.errors import PyMTLTypeError
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.rtlir.rtype import RTLIRType as rt

from .BehavioralRTLIRTypeCheckL2Pass import (
    BehavioralRTLIRTypeCheckL2Pass,
    BehavioralRTLIRTypeCheckVisitorL2,
    BehavioralRTLIRTypeEnforcerL2,
)


class BehavioralRTLIRTypeCheckL3Pass( BehavioralRTLIRTypeCheckL2Pass ):
  def get_visitor_class( s ):
    return BehavioralRTLIRTypeCheckVisitorL3

class BehavioralRTLIRTypeCheckVisitorL3( BehavioralRTLIRTypeCheckVisitorL2 ):
  def __init__( s, component, freevars, accessed, tmpvars, rtlir_getter ):
    super().__init__( component, freevars, accessed, tmpvars, rtlir_getter )
    s.type_expect[ 'Attribute' ] = (
      ( 'value', (rt.Component, rt.Signal),
                 'the base of an attribute must be one of: component, signal!' ),
    )

  def get_enforce_visitor( s ):
    return BehavioralRTLIRTypeEnforcerL3

  def _visit_Assign_single_target( s, node, target, i ):
    try:
      rhs_type = node.value.Type.get_dtype()
      lhs_type = target.Type.get_dtype()
    except AttributeError:
      rhs_type = None
      lhs_type = None

    l_is_struct = isinstance( lhs_type, rdt.Struct )
    r_is_struct = isinstance( rhs_type, rdt.Struct )

    # At L3 we check if either LHS or RHS is of BitStruct type.
    if l_is_struct or r_is_struct:
      if l_is_struct and r_is_struct:
        # Both sides are of struct type. Type check only if both sides
        # are of the _same_ struct type.
        if lhs_type.get_name() != rhs_type.get_name():
          raise PyMTLTypeError( s.blk, node.ast,
            f'LHS and RHS of assignment should have the same type (LHS target#{i+1} of {lhs_type} vs {rhs_type})!' )
      else:
        # There should be one side of struct type and the other of vector type.
        struct_type, vector_type = lhs_type, rhs_type
        if r_is_struct:
          struct_type, vector_type = rhs_type, lhs_type
        if not isinstance( vector_type, rdt.Vector ):
          raise PyMTLTypeError( s.blk, node.ast,
            f'LHS and RHS of assignment should have agreeable types (LHS target#{i+1} of {lhs_type} vs {rhs_type})!' )

        # Type check only if both sides have the same bitwidth.
        is_rhs_reinterpretable = not node.value._is_explicit
        struct_nbits, vector_nbits = struct_type.get_length(), vector_type.get_length()

        # If RHS is an int literal try to enforce the correct bitwidth.
        if not r_is_struct and is_rhs_reinterpretable and struct_nbits != vector_nbits:
          s.enforcer.enter( s.blk, rt.NetWire(rdt.Vector(struct_nbits)), node.value )

        if l_is_struct:
          vector_nbits = node.value.Type.get_dtype().get_length()

        if struct_nbits != vector_nbits:
          if l_is_struct:
            lnbits, rnbits = struct_nbits, vector_nbits
          else:
            lnbits, rnbits = vector_nbits, struct_nbits

          raise PyMTLTypeError( s.blk, node.ast,
            f'LHS and RHS of assignment should have the same bitwidth (LHS target#{i+1} of {lhs_type} ({lnbits} bits) vs {rhs_type} ({rnbits} bits))!' )

    else:
      super()._visit_Assign_single_target( node, target, i )

  def visit_Attribute( s, node ):
    if isinstance( node.value.Type, rt.Signal ):
      dtype = node.value.Type.get_dtype()
      if not isinstance( dtype, rdt.Struct ):
        raise PyMTLTypeError( s.blk, node.ast,
          'attribute base should be a struct signal!'
        )
      if not dtype.has_property( node.attr ):
        raise PyMTLTypeError( s.blk, node.ast,
          f'{dtype.get_name()} does not have field {node.attr}!' )
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
          f'unrecognized signal type {node.value.Type}!' )
      node.Type = rtype
      dtype = node.Type.get_dtype()
      # Only allow to be re-interpreted if this is a constant vector attribute
      if isinstance( node.Type, rt.Const ) and isinstance( dtype, rdt.Vector ):
        node._is_explicit = dtype.is_explicit()
      else:
        node._is_explicit = True

    else:
      super().visit_Attribute( node )

  def visit_StructInst( s, node ):
    cls = node.struct

    dtype = rdt.get_rtlir_dtype( cls() )
    all_properties = dtype.get_all_properties()

    if len( all_properties ) != len( node.values ):
      raise PyMTLTypeError( s.blk, node.ast,
        f"BitStruct {cls.__name__} has {len(all_properties)} fields but only {len(node.values)} arguments are given!" )

    all_types = zip( node.values, list(all_properties.items()) )

    for idx, ( value, ( name, field ) ) in enumerate( all_types ):
      s.visit( value )
      # Expect each argument to be a signal
      if not isinstance( value.Type, rt.Signal ):
        raise PyMTLTypeError( s.blk, node.ast,
          f"argument #{idx+1} has type {value.Type} but not a signal!" )
      v_dtype = value.Type.get_dtype()
      is_field_reinterpretable = not value._is_explicit
      # Expect each argument to have data type which corresponds to the field
      if v_dtype != field:
        if is_field_reinterpretable:
          target_nbits = field.get_length()
          s.enforcer.enter( s.blk, rt.NetWire(rdt.Vector(target_nbits)), value )
        else:
          raise PyMTLTypeError( s.blk, node.ast,
            f"Expected argument#{idx+1} ( field {name} ) to have type {field}, but got {v_dtype}." )

    node.Type = rt.Const( dtype )
    node._is_explicit = True

#-------------------------------------------------------------------------
# Enforce types for all terms whose types are inferred (implicit)
#-------------------------------------------------------------------------

class BehavioralRTLIRTypeEnforcerL3( BehavioralRTLIRTypeEnforcerL2 ):
  pass
