#=========================================================================
# BehavioralRTLIRTypeCheckL1Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 20, 2019
"""Provide L1 behavioral RTLIR type check pass."""
from __future__ import absolute_import, division, print_function

import pymtl
from pymtl.passes import BasePass
from pymtl.passes.BasePass import PassMetadata
from pymtl.passes.rtlir.RTLIRType import *

from .BehavioralRTLIR import *
from .errors import PyMTLTypeError


class BehavioralRTLIRTypeCheckL1Pass( BasePass ):

  def __call__( s, m ):
    """perform type checking on all RTLIR in rtlir_upblks"""

    if not hasattr( m, '_pass_behavioral_rtlir_type_check' ):
      m._pass_behavioral_rtlir_type_check = PassMetadata()

    m._pass_behavioral_rtlir_type_check.rtlir_freevars = {}

    visitor = BehavioralRTLIRTypeCheckVisitorL1( m,
      m._pass_behavioral_rtlir_type_check.rtlir_freevars
    )

    for blk in m.get_update_blocks():
      visitor.enter( blk, m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] )

class BehavioralRTLIRTypeCheckVisitorL1( BehavioralRTLIRNodeVisitor ):

  def __init__( s, component, freevars ):

    s.component = component

    s.freevars = freevars

    s.type_expect = {}

    lhs_types = ( Port, Wire )
    index_types = ( Port, Wire, Array )

    s.type_expect[ 'Assign' ] = {
      'target' : ( lhs_types, 'lhs of assignment must be a signal!' ),
      'value' : ( Signal, 'rhs of assignment should be signal or const!' )
    }
    s.type_expect[ 'BitsCast' ] = {
      'value':( Signal, 'only signals/consts can be cast into bits!' )
    }
    s.type_expect[ 'Attribute' ] = {
      'value':( Component, 'the base of an attribute must be a module!' )
    }
    s.type_expect[ 'Index' ] = {
      'idx':(Signal, 'index must be a signal or constant expression!'),
      'value':(index_types, 'the base of an index must be an array or signal!')
    }
    s.type_expect[ 'Slice' ] = {
      'value':( lhs_types, 'the base of a slice must be a signal!' ),
      'lower':( Signal, 'upper of slice must be a constant expression!' ),
      'upper':( Signal, 'lower of slice must be a constant expression!' )
    }

  def enter( s, blk, rtlir ):
    """ entry point for RTLIR type checking """
    s.blk     = blk

    # s.globals contains a dict of the global namespace of the module where
    # blk was defined
    s.globals = blk.__globals__

    # s.closure contains the free variables defined in an enclosing scope.
    # Basically this is the model instance s.
    s.closure = {}

    for i, var in enumerate( blk.__code__.co_freevars ):
      try: 
        s.closure[ var ] = blk.__closure__[ i ].cell_contents
      except ValueError: 
        pass

    s.visit( rtlir )

  # Override the default visit()
  def visit( s, node ):
    node_name = node.__class__.__name__
    method = 'visit_' + node_name
    func = getattr( s, method, s.generic_visit )

    # First visit (type check) all child nodes
    for field in node.__dict__.keys():
      value = node.__dict__[ field ]
      if isinstance( value, list ):
        for item in value:
          if isinstance( item, BaseBehavioralRTLIR ):
            s.visit( item )
      elif isinstance( value, BaseBehavioralRTLIR ):
        s.visit( value )

    # Then verify that all child nodes have desired types
    try:
      # Check the expected types of child nodes
      for field, type_rule in s.type_expect[node_name].iteritems():
        value = node.__dict__[ field ]
        target_type = type_rule[ 0 ]
        exception_msg = type_rule[ 1 ]

        if eval( 'not isinstance( value.Type, target_type )' ):
          raise PyMTLTypeError( s.blk, node.ast, exception_msg )

    except PyMTLTypeError:
      raise
    except:
      # This node does not require type checking on child nodes
      pass

    # Finally call the type check function
    func( node )

  # Override the default generic_visit()
  def generic_visit( s, node ):
    node.Type = None

  def visit_Assign( s, node ):

    # RHS should have the same type as LHS

    rhs_type = node.value.Type.get_dtype()
    lhs_type = node.target.Type.get_dtype()

    if not lhs_type( rhs_type ):
      raise PyMTLTypeError(
        s.blk, node.ast, 'Unagreeable types {} and {}!'.format(
          lhs_type, rhs_type
        )
      )

    node.Type = None

  def visit_FreeVar( s, node ):

    if not node.name in s.freevars.keys():
      s.freevars[ node.name ] = node.obj

    t = get_rtlir( node.obj )

    if isinstance( t, Const ) and isinstance( t.get_dtype(), Vector ):

      node._value = pymtl.mk_bits( t.get_dtype().get_length() )( node.obj )

    node.Type = t

  def visit_Base( s, node ):

    # Mark this node as having type Component
    # In L1 the `s` top component is the only possible base

    node.Type = get_rtlir( node.base )

    assert isinstance( node.Type, Component )

  def visit_Number( s, node ):

    # By default, number literals have bitwidth of 32

    node.Type = get_rtlir( node.value )
    node._value = pymtl.Bits32( node.value )

  def visit_BitsCast( s, node ):

    nbits = node.nbits
    Type = node.value.Type

    # We do not check for bitwidth mismatch here because the user should
    # be able to explicitly convert signals/constatns to different bitwidth.

    node.Type = Wire( Vector( nbits ) )

    if hasattr( node, '_value' ):
      node._value = mk_Bits( nbits, node._value )

  def visit_Attribute( s, node ):

    # Attribute supported at L1: CurCompAttr

    if isinstance( node.value, Base ):
      if not node.value.Type.has_property( node.attr ):
        raise PyMTLTypeError(
          s.blk, node.ast, 'type {} does not have attribute {}!'.format(
            node.value.Type, node.attr
        ) )

    else:
      raise PyMTLTypeError(
        s.blk, node.ast, '{} of type {} is not supported at L1!'.format(
          node.attr, node.value.Type
      ) )


    # value.attr has the type that is specified by the base

    node.Type = node.value.Type.get_property( node.attr )

  def visit_Index( s, node ):

    idx = getattr( node.idx, '_value', None )

    if isinstance( node.value.Type, Array ):

      if ( not idx is None ) and not(
          0<=idx<=node.value.Type.get_dim_sizes()[0] ):

        raise PyMTLTypeError(
          s.blk, node.ast, 'array index out of range!' )

      # Unpacked array index must be a static constant integer!
      subtype = node.value.Type.get_sub_type()
      if not isinstance( subtype, ( Port, Wire, Const ) ):
        if not hasattr( node.value, '_value' ):
          raise PyMTLTypeError(
            s.blk, node.ast,\
'index of unpacked array {} must be a constant integer expression!'.format(
            node.value ) )

      node.Type = node.value.Type.get_next_dim_type()

    elif isinstance( node.value.Type, Signal ):

      dtype = node.value.Type.get_dtype()

      if node.value.Type.is_packed_indexable():

        if ( not idx is None ) and not( 0<=idx<=dtype.get_length() ):

          raise PyMTLTypeError(
            s.blk, node.ast, 'bit selection index out of range!' )

        node.Type = node.value.Type.get_next_dim_type()

      elif isinstance( dtype, Vector ):

        if ( not idx is None ) and not( 0<=idx<=dtype.get_length() ):

          raise PyMTLTypeError(
            s.blk, node.ast, 'bit selection index out of range!' )

        node.Type = Wire( Vector( 1 ) )

      else:

        raise PyMTLTypeError(
          s.blk, node.ast, 'cannot perform index on {}!'.format(dtype) )

    else:

      raise PyMTLTypeError(
        s.blk, node.ast, 'cannot perform index on {}!'.format(
          node.value.Type ) )

  def visit_Slice( s, node ):

    lower_val = getattr( node.lower, '_value', None )
    upper_val  = getattr( node.upper, '_value', None )

    dtype = node.value.Type.get_dtype()

    if not isinstance( dtype, Vector ):

      raise PyMTLTypeError(
        s.blk, node.ast, 'cannot perform slicing on type {}!'.format(
          node.value.Type ) )

    if not lower_val is None and not upper_val is None:

      signal_nbits = dtype.get_length()

      # upper bound must be strictly larger than the lower bound

      if ( lower_val >= upper_val ):
        raise PyMTLTypeError(
          s.blk, node.ast,
          'the upper bound of a slice must be larger than the lower bound!' )

      # upper & lower bound should be less than the bit width of the signal

      if not ( 0 <= lower_val < upper_val <= signal_nbits ):
        raise PyMTLTypeError(
          s.blk, node.ast, 'upper/lower bound of slice out of width of signal!' )

      node.Type = Wire( Vector( upper_val - lower_val ) )

    else:

      raise PyMTLTypeError(
        s.blk, node.ast, 'slice bounds must be constant!' )
