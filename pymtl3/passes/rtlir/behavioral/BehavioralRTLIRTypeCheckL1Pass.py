#=========================================================================
# BehavioralRTLIRTypeCheckL1Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 20, 2019
"""Provide L1 behavioral RTLIR type check pass."""

import copy
import math
from collections import OrderedDict, deque
from contextlib import contextmanager

from pymtl3.datatypes import Bits32, mk_bits
from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.rtlir.errors import PyMTLTypeError, RTLIRConversionError
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.rtlir.rtype import RTLIRType as rt

from . import BehavioralRTLIR as bir


class BehavioralRTLIRTypeCheckL1Pass( BasePass ):
  def __call__( s, m ):
    """Perform type checking on all RTLIR in rtlir_upblks."""
    if not hasattr( m, '_pass_behavioral_rtlir_type_check' ):
      m._pass_behavioral_rtlir_type_check = PassMetadata()
    m._pass_behavioral_rtlir_type_check.rtlir_freevars = OrderedDict()
    m._pass_behavioral_rtlir_type_check.rtlir_accessed = set()
    type_checker = BehavioralRTLIRTypeCheckVisitorL1(
      m, m._pass_behavioral_rtlir_type_check.rtlir_freevars,
      m._pass_behavioral_rtlir_type_check.rtlir_accessed )
    for blk in m.get_update_block_order():
      type_checker.enter( blk, m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] )

#-------------------------------------------------------------------------
# Type checker
#-------------------------------------------------------------------------

class BehavioralRTLIRTypeCheckVisitorL1( bir.BehavioralRTLIRNodeVisitor ):
  def __init__( s, component, freevars, accessed ):
    s.component = component
    s.freevars = freevars
    s.accessed = accessed
    s.type_expect = {}

    # The enforcer is called with a context and an AST node so that it can
    # enforce every implicitly typed node in the subtree to have the type
    # of the given context. Note that after one enforcement, the _is_explicit
    # flag would be set to True.
    try:
      s.enforcer = s.get_enforce_visitor()( component )
    except TypeError:
      pass

    lhs_types = ( rt.Port, rt.Wire, rt.NetWire )
    index_types = ( rt.Port, rt.Wire, rt.Array )
    slice_types = ( rt.Port, rt.Wire )
    s.type_expect[ 'Assign' ] = {
      'targets' : ( lhs_types, 'lhs of assignment must be a signal!' ),
      'value'   : ( rt.Signal, 'rhs of assignment should be signal or const!' )
    }
    s.type_expect[ 'ZeroExt' ] = {
      'value':( rt.Signal, 'extension only applies to signals!' )
    }
    s.type_expect[ 'SignExt' ] = {
      'value':( rt.Signal, 'extension only applies to signals!' )
    }
    s.type_expect[ 'Reduce' ] = {
      'value':( rt.Signal, 'reduce only applies on a signal!' )
    }
    s.type_expect[ 'SizeCast' ] = {
      'value':( rt.Signal, 'size casting only applies to signals/consts!' )
    }
    s.type_expect[ 'Attribute' ] = {
      'value':( rt.Component, 'the base of an attribute must be a component!' )
    }
    s.type_expect[ 'Index' ] = {
      'idx':( rt.Signal, 'index must be a signal or constant expression!' ),
      'value':( index_types, 'the base of an index must be an array or signal!' )
    }
    s.type_expect[ 'Slice' ] = {
      'value':( slice_types, 'the base of a slice must be a signal!' ),
      'lower':( rt.Signal, 'upper of slice must be a constant expression!' ),
      'upper':( rt.Signal, 'lower of slice must be a constant expression!' )
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

  def get_enforce_visitor( s ):
    return BehavioralRTLIRTypeEnforcerL1

  # Override the default visit()
  def visit( s, node ):
    # not node._is_explicit: is the parent node allowed to re-interpret this
    # node's bitwidth without truncation?
    node_name = node.__class__.__name__
    method = 'visit_' + node_name
    func = getattr( s, method, s.generic_visit )

    # First visit (type check) all child nodes
    for field, value in vars(node).items():
      # Special case For because we use context depedent types
      # for the loop index
      if node_name == 'For' and field == 'body': continue
      if isinstance( value, list ):
        for item in value:
          if isinstance( item, bir.BaseBehavioralRTLIR ):
            s.visit( item )
      elif isinstance( value, bir.BaseBehavioralRTLIR ):
        s.visit( value )

    # Then verify that all child nodes have desired types
    try:
      # Check the expected types of child nodes
      for field, type_rule in s.type_expect[node_name].items():
        value = vars(node)[field]
        target_type = type_rule[ 0 ]
        exception_msg = type_rule[ 1 ]
        if isinstance( value, list ):
          for v in value:
            if eval( 'not isinstance( v.Type, target_type )' ):
              raise PyMTLTypeError( s.blk, node.ast, exception_msg )
        else:
          if eval( 'not isinstance( value.Type, target_type )' ):
            raise PyMTLTypeError( s.blk, node.ast, exception_msg )
    except PyMTLTypeError:
      raise
    except Exception:
      # This node does not require type checking on child nodes
      pass

    # Finally call the type check function
    func( node )

  # Override the default generic_visit()
  def generic_visit( s, node ):
    node.Type = None
    # Is the parent node allowed to re-interpret the type of this node?
    node._is_explicit = True
    # Has this node re-interpreted the type of its child node?
    node._has_reinterpreted = False

  def is_same( s, u, v ):
    """Return if the sub-AST at u and v are the same."""
    if type(u) is not type(v):
      return False
    return u == v

  def _visit_Assign_single_target( s, node, target, i ):
    lhs_type = target.Type.get_dtype()
    rhs_type = node.value.Type.get_dtype()

    # At L1 it's always signal assignment
    is_rhs_reinterpretable = not node.value._is_explicit
    if is_rhs_reinterpretable and ((not lhs_type(rhs_type)) or (rhs_type != lhs_type)):
      s.enforcer.enter( s.blk, target.Type, node.value )

    rhs_type = node.value.Type.get_dtype()

    # Weak type checking (agreeable types)
    if not lhs_type( rhs_type ):
      raise PyMTLTypeError( s.blk, node.ast,
        f'Unagreeable types between LHS and RHS (LHS target#{i+1} of {lhs_type} vs {rhs_type})!' )

    # Strong type checking (same type)
    if rhs_type != lhs_type:
      raise PyMTLTypeError( s.blk, node.ast,
        f'LHS and RHS of assignment should have the same type (LHS target#{i+1} of {lhs_type} vs {rhs_type})!' )

  def visit_Assign( s, node ):
    # RHS should have the same type as any of LHS
    for i, target in enumerate( node.targets ):
      s._visit_Assign_single_target( node, target, i )

    node.Type = None
    node._is_explicit = True

  def visit_FreeVar( s, node ):
    if node.name not in s.freevars:
      s.freevars[ node.name ] = node.obj

    try:
      t = rt.get_rtlir( node.obj )
    except RTLIRConversionError as e:
      raise PyMTLTypeError(s.blk, node.ast,
        f'{node.name} cannot be converted into a valid RTLIR object!' )

    if isinstance( t, rt.Const ) and isinstance( t.get_dtype(), rdt.Vector ):
      node._value = int(node.obj)
    node.Type = t
    node._is_explicit = False if isinstance(node.obj, int) else True

  def visit_Base( s, node ):
    # Mark this node as having type rt.Component
    # In L1 the `s` top component is the only possible base
    node.Type = rt.get_rtlir( node.base )
    node._is_explicit = True
    if not isinstance( node.Type, rt.Component ):
      raise PyMTLTypeError( s.blk, node.ast,
        f'{node} is not a rt.Component!' )

  def visit_Number( s, node ):
    # By default, number literals have the minimal bitwidth that can
    # hold its value without truncation.
    node.Type = rt.get_rtlir( node.value )
    node._value = int(node.value)
    node._is_explicit = False

  def visit_Concat( s, node ):
    nbits = 0
    for child in node.values:
      if not isinstance(child.Type, rt.Signal):
        raise PyMTLTypeError( s.blk, node.ast,
          f'{child} is not a signal!' )
      nbits += child.Type.get_dtype().get_length()
    node.Type = rt.NetWire( rdt.Vector( nbits ) )
    node._is_explicit = True

  def visit_ZeroExt( s, node ):
    new_nbits = node.nbits
    child_type = node.value.Type
    old_nbits = child_type.get_dtype().get_length()
    if new_nbits < old_nbits:
      raise PyMTLTypeError( s.blk, node.ast,
        f'the target bitwidth {new_nbits} is less than the bitwidth of the operand ({old_nbits})!' )
    node.Type = copy.copy( child_type )
    node.Type.dtype = rdt.Vector( new_nbits )
    node._is_explicit = True

  def visit_SignExt( s, node ):
    new_nbits = node.nbits
    child_type = node.value.Type
    old_nbits = child_type.get_dtype().get_length()
    if new_nbits < old_nbits:
      raise PyMTLTypeError( s.blk, node.ast,
        f'the target bitwidth {new_nbits} is less than the bitwidth of the operand ({old_nbits})!' )
    node.Type = copy.copy( child_type )
    node.Type.dtype = rdt.Vector( new_nbits )
    node._is_explicit = True

  def visit_Truncate( s, node ):
    new_nbits = node.nbits
    child_type = node.value.Type
    old_nbits = child_type.get_dtype().get_length()
    if new_nbits > old_nbits:
      raise PyMTLTypeError( s.blk, node.ast,
        f'the target bitwidth {new_nbits} is larger than the bitwidth of the operand ({old_nbits})!' )
    node.Type = copy.copy( child_type )
    node.Type.dtype = rdt.Vector( new_nbits )
    node._is_explicit = True

  def visit_Reduce( s, node ):
    child_type = node.value.Type
    node.Type = copy.copy( child_type )
    node.Type.dtype = rdt.Vector( 1 )
    node._is_explicit = True

  def visit_SizeCast( s, node ):
    nbits = node.nbits
    Type = node.value.Type

    # We do not check for bitwidth mismatch here because the user should
    # be able to explicitly convert signals/constatns to different bitwidth.
    node.Type = copy.copy( Type )
    node.Type.dtype = rdt.Vector( nbits )
    node._is_explicit = True

    try:
      node._value = node.value._value
    except AttributeError:
      pass

  def visit_Attribute( s, node ):
    # Attribute supported at L1: CurCompAttr
    if isinstance( node.value, bir.Base ):
      if not node.value.Type.has_property( node.attr ):
        raise PyMTLTypeError( s.blk, node.ast,
          f'type {node.value.Type} does not have attribute {node.attr}!' )
      s.accessed.add( node.attr )

    else:
      raise PyMTLTypeError( s.blk, node.ast,
        f'non-component attribute {node.attr} of type {node.value.Type} is not supported at L1!' )
    # value.attr has the type that is specified by the base
    node.Type = node.value.Type.get_property( node.attr )
    if isinstance( node.Type, rt.Const ):
      dtype = node.Type.get_dtype()
      if isinstance( dtype, rdt.Vector ):
        node._is_explicit = dtype.is_explicit()
      else:
        node._is_explicit = True
    else:
      node._is_explicit = True

  def _handle_index_extension( s, node, value, idx, dscp, inclusive=True ):
    expected_nbits = value.Type.get_index_width()
    idx_nbits = idx.Type.get_dtype().get_length()
    is_idx_reinterpretable = not idx._is_explicit

    if not inclusive and hasattr( idx, '_value' ):
      idx_nbits = s._get_nbits_from_value( idx._value-1 )

    if idx_nbits > expected_nbits:
      # Either bitwidth do not match or requires implicit truncation
      raise PyMTLTypeError( s.blk, node.ast,
        f'expects a {expected_nbits}-bit index but the given {dscp} has more ({idx_nbits}) bits!' )
    elif idx_nbits < expected_nbits:
      if is_idx_reinterpretable:
        # Implicit zero-extension
        s.enforcer.enter( s.blk, rt.NetWire(rdt.Vector(expected_nbits)), idx )
      else:
        # Bitwidth mismatch
        raise PyMTLTypeError( s.blk, node.ast,
          f'expects a {expected_nbits}-bit index but the given {dscp} has {idx_nbits} bits!' )
    else:
      if idx_nbits != idx.Type.get_dtype().get_length():
        # If we used a different bitwidth then enforce it
        s.enforcer.enter( s.blk, rt.NetWire(rdt.Vector(idx_nbits)), idx )

  def visit_Index( s, node ):
    idx = None if not hasattr(node.idx, "_value") else int(node.idx._value)
    if isinstance( node.value.Type, rt.Array ):
      if idx is not None and not (0 <= idx < node.value.Type.get_dim_sizes()[0]):
        raise PyMTLTypeError( s.blk, node.ast, 'array index out of range!' )
      node.Type = node.value.Type.get_next_dim_type()
      obj = node.value.Type.get_obj()
      s._handle_index_extension( node, node.value, node.idx, 'index' )

      # If the given index yields an integer, mark this node as implicit
      if idx is not None and obj is not None:
        if isinstance( node.Type, rt.Array ):
          node.Type.obj = obj[ int( idx ) ]
          node._is_explicit = True
        else:
          node._value = int( obj[ int( idx ) ] )
          node._is_explicit = False if isinstance(node._value, int) else True
      else:
        node._is_explicit = True

    elif isinstance( node.value.Type, rt.Signal ):
      dtype = node.value.Type.get_dtype()
      s._handle_index_extension( node, node.value, node.idx, 'index' )

      if node.value.Type.is_packed_indexable():
        if idx is not None and not (0 <= idx < dtype.get_length()):
          raise PyMTLTypeError( s.blk, node.ast,
            'bit selection index out of range!' )
        node.Type = node.value.Type.get_next_dim_type()
        node._is_explicit = True
      elif isinstance( dtype, rdt.Vector ):
        if idx is not None and not(0 <= idx < dtype.get_length()):
          raise PyMTLTypeError( s.blk, node.ast,
            'bit selection index out of range!' )
        node.Type = rt.NetWire( rdt.Vector( 1 ) )
        node._is_explicit = True
      else:
        raise PyMTLTypeError( s.blk, node.ast,
          f'cannot perform index on {dtype}!')

    else:
      # Should be unreachable
      raise PyMTLTypeError( s.blk, node.ast,
        f'cannot perform index on {node.value.Type}!')

  def visit_Slice( s, node ):
    lower_val = None if not hasattr(node.lower, "_value") else node.lower._value
    upper_val = None if not hasattr(node.upper, "_value") else node.upper._value
    dtype = node.value.Type.get_dtype()

    if hasattr(node.value, "_value"):
      raise PyMTLTypeError( s.blk, node.ast,
          f'cannot perform slicing on constant {node.value._value}!')

    if not isinstance( dtype, rdt.Vector ):
      raise PyMTLTypeError( s.blk, node.ast, f'cannot perform slicing on type {dtype}!')

    s._handle_index_extension( node, node.value, node.lower, 'slice lower bound' )
    s._handle_index_extension( node, node.value, node.upper, 'slice upper bound', False )

    if not lower_val is None and not upper_val is None:
      signal_nbits = dtype.get_length()
      # upper bound must be strictly larger than the lower bound
      if ( lower_val >= upper_val ):
        raise PyMTLTypeError( s.blk, node.ast,
          'the upper bound of a slice must be larger than the lower bound!' )
      # upper & lower bound should be less than the bit width of the signal
      if not ( 0 <= lower_val < upper_val <= signal_nbits ):
        raise PyMTLTypeError( s.blk, node.ast,
          'upper/lower bound of slice out of width of signal!' )
      node.Type = rt.NetWire( rdt.Vector( int( upper_val - lower_val ) ) )
      node._is_explicit = True

    else:
      # Try to special case the constant-stride part selection
      try:
        assert isinstance( node.upper, bir.BinOp )
        assert isinstance( node.upper.op, bir.Add )
        nbits = node.upper.right
        slice_size = nbits._value
        assert s.is_same( node.lower, node.upper.left )
        node.Type = rt.NetWire( rdt.Vector( slice_size ) )
        node._is_explicit = True
        # Add new fields that might help translation
        node.size = slice_size
        node.base = node.lower
      except Exception:
        raise PyMTLTypeError( s.blk, node.ast, 'slice bounds must be constant!' )

  def _get_nbits_from_value( s, value ):
    if -1 <= value <= 1:
      return 1
    if value < 0:
      return math.ceil(math.log2(abs(value)))
    else:
      return math.ceil(math.log2(value+1))

#-------------------------------------------------------------------------
# Enforce types for all terms whose types are inferred (implicit)
#-------------------------------------------------------------------------

class BehavioralRTLIRTypeEnforcerL1( bir.BehavioralRTLIRNodeVisitor ):

  def __init__( s, component ):
    s.component = component

  def enter( s, blk, context, node ):
    s.blk = blk
    s.stack = deque([])
    with s.register_context( context ):
      s.visit( node )

  @contextmanager
  def register_context( s, context_type ):
    s.stack.append( context_type )
    yield
    s.stack.pop()

  def get_context( s, node, obj ):
    if not s.stack:
      raise PyMTLTypeError( s.blk, node.ast,
          f'no context was provided to validate the inferred bitwidth of {obj}!' )
    return s.stack[-1]

  def mutate_datatype( s, node, descp ):
    if not node._is_explicit:
      # assert isinstance(node.Type, rt.Const), f'internal error: {node} is not constant!'
      target_nbits = s.get_context(node, descp).get_dtype().nbits
      # All RTLIR datatypes are cached -- we don't want to invalidate the cache
      # and therefore a deepcopy is needed here
      node.Type = copy.deepcopy(node.Type)
      node.Type.dtype.nbits = target_nbits
      # node._is_explicit = True

  def visit_FreeVar( s, node ):
    s.mutate_datatype( node, node.obj )

  def visit_Number( s, node ):
    s.mutate_datatype( node, node.value )

  def visit_Attribute( s, node ):
    s.mutate_datatype( node, node.attr )

  def visit_Index( s, node ):
    s.mutate_datatype( node, 'indexing' )
