#=========================================================================
# BehavioralRTLIRTypeCheckL2Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 29, 2019
"""Provide L2 behavioral RTLIR type check pass."""

from collections import OrderedDict

from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.rtlir.errors import PyMTLTypeError
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.rtlir.rtype import RTLIRType as rt

from . import BehavioralRTLIR as bir
from .BehavioralRTLIRTypeCheckL1Pass import BehavioralRTLIRTypeCheckVisitorL1, \
    BehavioralRTLIRTypeEnforcerL1


class BehavioralRTLIRTypeCheckL2Pass( BasePass ):
  def __call__( s, m ):
    """Perform type checking on all RTLIR in rtlir_upblks."""
    if not hasattr( m, '_pass_behavioral_rtlir_type_check' ):
      m._pass_behavioral_rtlir_type_check = PassMetadata()
    m._pass_behavioral_rtlir_type_check.rtlir_freevars = OrderedDict()
    m._pass_behavioral_rtlir_type_check.rtlir_tmpvars = OrderedDict()
    m._pass_behavioral_rtlir_type_check.rtlir_accessed = set()

    type_checker = BehavioralRTLIRTypeCheckVisitorL2(
      m,
      m._pass_behavioral_rtlir_type_check.rtlir_freevars,
      m._pass_behavioral_rtlir_type_check.rtlir_accessed,
      m._pass_behavioral_rtlir_type_check.rtlir_tmpvars
    )
    type_enforcer = BehavioralRTLIRTypeEnforcerL2()

    for blk in m.get_update_block_order():
      type_checker.enter( blk, m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] )
      type_enforcer.enter( blk, m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] )

#-------------------------------------------------------------------------
# Type checker
#-------------------------------------------------------------------------

class BehavioralRTLIRTypeCheckVisitorL2( BehavioralRTLIRTypeCheckVisitorL1 ):
  def __init__( s, component, freevars, accessed, tmpvars ):
    super().__init__(component, freevars, accessed)
    s.tmpvars = tmpvars
    s.loopvar_nbits = {}
    s.BinOp_max_nbits = (bir.Add, bir.Sub, bir.Mult, bir.Div, bir.Mod, bir.Pow,
                         bir.BitAnd, bir.BitOr, bir.BitXor)
    s.BinOp_left_nbits = ( bir.ShiftLeft, bir.ShiftRightLogic )
    s.type_expect = {}
    lhs_types = ( rt.Port, rt.Wire, rt.NetWire, rt.NoneType )

    s.type_expect[ 'Assign' ] = {
      'targets' : ( lhs_types, 'lhs of assignment must be signal/tmpvar!' ),
      'value'   : ( rt.Signal, 'rhs of assignment should be signal/const!' )
    }
    s.type_expect[ 'BinOp' ] = {
      'left' : ( rt.Signal, 'lhs of binop should be signal/const!' ),
      'right' : ( rt.Signal, 'rhs of binop should be signal/const!' ),
    }
    s.type_expect[ 'UnaryOp' ] = {
      'operand' : ( rt.Signal, 'unary op only applies to signals and consts!' )
    }
    s.type_expect[ 'For' ] = {
      'start' : ( rt.Const, 'the start of a for-loop must be a constant expression!' ),
      'end':( rt.Const, 'the end of a for-loop must be a constant expression!' ),
      'step':( rt.Const, 'the step of a for-loop must be a constant expression!' )
    }
    s.type_expect[ 'If' ] = {
      'cond' : ( rt.Signal, 'the condition of if must be a signal!' )
    }
    s.type_expect[ 'IfExp' ] = {
      'cond' : ( rt.Signal, 'the condition of if-exp must be a signal!' ),
      'body' : ( rt.Signal, 'the body of if-exp must be a signal!' ),
      'orelse' : ( rt.Signal, 'the else branch of if-exp must be a signal!' )
    }

  def eval_const_binop( s, l, op, r ):
    """Evaluate ( l op r ) and return the result as an integer."""
    assert type( l ) == int or isinstance( l, pymtl3_datatype.Bits )
    assert type( r ) == int or isinstance( r, pymtl3_datatype.Bits )
    op_dict = {
      bir.And       : 'and', bir.Or    : 'or',
      bir.Add       : '+',   bir.Sub   : '-',  bir.Mult : '*',  bir.Div  : '/',
      bir.Mod       : '%',   bir.Pow   : '**',
      bir.ShiftLeft : '<<',  bir.ShiftRightLogic : '>>',
      bir.BitAnd    : '&',   bir.BitOr : '|',  bir.BitXor : '^',
    }
    _op = op_dict[ type( op ) ]
    return eval( f'l{_op}r' )

  def _visit_Assign_single_target( s, node, target, i ):
    rhs_type = node.value.Type
    lhs_type = target.Type

    if isinstance( target, bir.TmpVar ):
      tmpvar_id = (target.name, target.upblk_name)
      if lhs_type != rt.NoneType() and lhs_type.get_dtype() != rhs_type.get_dtype():
        raise PyMTLTypeError( s.blk, node.ast,
          f'conflicting type {rhs_type} for temporary variable {node.targets[i].name}(LHS target#{i+1} of {lhs_type})!' )

      # Creating a temporaray variable
      # Reminder that a temporary variable is essentially a wire. So we use
      # rt.Wire here instead of rt.NetWire
      target.Type = rt.Wire( rhs_type.get_dtype() )
      s.tmpvars[ tmpvar_id ] = rt.Wire( rhs_type.get_dtype() )

    else:
      # non-temporary assignment is an L1 thing
      super()._visit_Assign_single_target( node, target, i )

  def visit_Assign( s, node ):
    # RHS should have the same type as LHS
    for i, target in enumerate( node.targets ):
      s._visit_Assign_single_target( node, target, i )

    node.Type = None
    node._is_explicit = True

  def visit_If( s, node ):
    # Can the type of condition be cast into bool?
    dtype = node.cond.Type.get_dtype()
    if not rdt.Bool()( dtype ):
      raise PyMTLTypeError( s.blk, node.ast,
        'the condition of "if" cannot be converted to bool!' )
    node.Type = None
    node._is_explicit = True

  def visit_For( s, node ):
    try:
      step = node.step._value
      if step == 0:
        raise PyMTLTypeError( s.blk, node.ast,
          'the step of for-loop cannot be zero!' )
    except AttributeError:
      raise PyMTLTypeError( s.blk, node.ast,
        'the step of for-loop must be a constant!' )

    start_nbits = node.start.Type.get_dtype().get_length()
    end_nbits = node.end.Type.get_dtype().get_length()
    step_nbits = node.step.Type.get_dtype().get_length()
    nbits = max(start_nbits, end_nbits, step_nbits)
    s.loopvar_nbits[node.var.name] = nbits

    for stmt in node.body:
      s.visit( stmt )

    del s.loopvar_nbits[node.var.name]

    node.Type = None
    node._is_explicit = True

  def visit_LoopVar( s, node ):
    node.Type = rt.Const( rdt.Vector( s.loopvar_nbits[node.name] ), None )
    node._is_explicit = True

  def visit_TmpVar( s, node ):
    tmpvar_id = (node.name, node.upblk_name)
    if tmpvar_id not in s.tmpvars:
      # This tmpvar is being created. Later when it is used, its type can
      # be read from the tmpvar type environment.
      node.Type = rt.NoneType()
      node._is_explicit = True

    else:
      node.Type = s.tmpvars[ tmpvar_id ]
      node._is_explicit = True

  def visit_IfExp( s, node ):
    # Can the type of condition be cast into bool?
    if not rdt.Bool()( node.cond.Type.get_dtype() ):
      raise PyMTLTypeError( s.blk, node.ast,
        'the condition of "if-exp" cannot be converted to bool!' )

    # body and orelse must have the same type
    # if node.body.Type != node.orelse.Type:
    if not node.body.Type.get_dtype()( node.orelse.Type.get_dtype() ):
      raise PyMTLTypeError( s.blk, node.ast,
        'the body and orelse of "if-exp" must have the same type!' )
    node.Type = node.body.Type
    node._is_explicit = True

  def visit_UnaryOp( s, node ):
    # if isinstance( node.op, bir.Not ):
    #   dtype = node.operand.Type.get_dtype()
    #   if not rdt.Bool()( dtype ):
    #     raise PyMTLTypeError( s.blk, node.ast,
    #       'the operand of "Logic-not" cannot be cast to bool!' )
    #   # if dtype.get_length() != 1:
    #   #   raise PyMTLTypeError( s.blk, node.ast,
    #   #     'the operand of "Logic-not" is not a single bit!' )
    #   node.Type = rt.NetWire( rdt.Vector( node.operand.Type.get_dtype().get_lenght() ) )
    #   node._is_explicit = True
    # else:
    node.Type = node.operand.Type
    node._is_explicit = True

  # def visit_BoolOp( s, node ):
  #   max_nbits = -1
  #   for value in node.values:
  #     dtype = value.Type.get_dtype()
  #     if not isinstance(value.Type, rt.Signal) or not rdt.Bool()(dtype):
  #       raise PyMTLTypeError( s.blk, node.ast,
  #         f"{value} of {value.Type} cannot be cast into bool!")
  #     if dtype.get_length() > max_nbits:
  #       max_nbits = dtype.get_length()
  #   node.Type = rt.NetWire( rdt.Bool(max_nbits) )
  #   node._is_explicit = True

  def visit_BinOp( s, node ):
    op = node.op
    l_type = node.left.Type.get_dtype()
    r_type = node.right.Type.get_dtype()
    l_explicit, r_explicit = node.left._is_explicit, node.right._is_explicit
    if not( rdt.Vector(1)( l_type ) and rdt.Vector(1)( r_type ) ):
      raise PyMTLTypeError( s.blk, node.ast,
        f"both sides of {op.__class__.__name__} should be of vector type!" )

    l_nbits = l_type.get_length()
    r_nbits = r_type.get_length()

    if l_explicit and r_explicit:
      if not isinstance( op, s.BinOp_left_nbits ) and l_type != r_type:
        raise PyMTLTypeError( s.blk, node.ast,
          f"LHS and RHS of {op.__class__.__name__} should have the same type ({l_type} vs {r_type})!" )
    elif not l_explicit and not r_explicit:
      raise PyMTLTypeError( s.blk, node.ast,
        f"at least one side of {op.__class__.__name__} should have explicit bitwidth ({l_type} vs {r_type})!" )

    # Enforcing Verilog bitwidth inference rules
    res_nbits = 0
    if isinstance( op, s.BinOp_max_nbits ):
      if (not l_explicit and r_explicit) or (l_explicit and not r_explicit):
        explicit, implicit = l_nbits, r_nbits
        if not l_explicit:
          explicit, implicit = r_nbits, l_nbits
        # Check if any implicit truncation happens
        if explicit < implicit:
          raise PyMTLTypeError( s.blk, node.ast,
              f"The explicitly sized side of operation has {explicit} bits but "
              f"the integer literal requires more ({implicit}) bits to hold!" )
      res_nbits = max( l_nbits, r_nbits )
    elif isinstance( op, s.BinOp_left_nbits ):
      res_nbits = l_nbits
    else:
      raise Exception( 'RTLIRTypeCheck internal error: unrecognized op!' )

    try:
      # Both sides are constant expressions
      l_val = node.left._value
      r_val = node.rigth._value
      node._value = s.eval_const_binop( l_val, op, r_val )
      node.Type = rt.Const( rdt.Vector( res_nbits ) )
      node._is_explicit = True
    except AttributeError:
      # Both sides are constant but the value cannot be determined statically
      if isinstance(node.left.Type, rt.Const) and isinstance(node.right.Type, rt.Const):
        node.Type = rt.Const( rdt.Vector( res_nbits ), None )
      # Variable
      else:
        node.Type = rt.NetWire( rdt.Vector( res_nbits ) )

      node._is_explicit = True

  def visit_Compare( s, node ):
    l_type = node.left.Type.get_dtype()
    r_type = node.right.Type.get_dtype()
    l_explicit, r_explicit = node.left._is_explicit, node.right._is_explicit
    l_nbits, r_nbits = l_type.get_length(), r_type.get_length()
    if l_explicit and r_explicit:
      if l_type != r_type:
        raise PyMTLTypeError( s.blk, node.ast,
          f"LHS and RHS of {node.op.__class__.__name__} have different types ({l_type} vs {r_type})!" )
    elif not l_explicit and not r_explicit:
      raise PyMTLTypeError( s.blk, node.ast,
        f"at least one side of {node.op.__class__.__name__} should have explicit bitwidth ({l_type} vs {r_type})!" )
    else:
      explicit, implicit = l_nbits, r_nbits
      if not l_explicit:
        explicit, implicit = r_nbits, l_nbits
      # Check if any implicit truncation happens
      if explicit < implicit:
        raise PyMTLTypeError( s.blk, node.ast,
            f"The explicitly sized side of comparison has {explicit} bits but "
            f"the integer literal requires more ({implicit}) bits to hold!" )
    node.Type = rt.NetWire( rdt.Bool() )
    node._is_explicit = True

#-------------------------------------------------------------------------
# Enforce types for all terms whose types are inferred (implicit)
#-------------------------------------------------------------------------
# Terms that are able to introduce a context at L2:
#   - IfExp ( type of this node )
#   - UnaryOp ( the same type as the operand )
#   - BinOp ( the type of the explicitly sized side if the result is max(n,m),
#             or the type of each side )
#   - Compare ( the type of the explicitly sized side )

class BehavioralRTLIRTypeEnforcerL2( BehavioralRTLIRTypeEnforcerL1 ):

  def visit_IfExp( s, node ):
    with s.register_context( node.cond.Type ):
      s.visit( node.cond )
    with s.register_context( node.Type ):
      s.visit( node.body )
      s.visit( node.orelse )

  def visit_UnaryOp( s, node ):
    with s.register_context( node.Type ):
      s.visit( node.operand )

  def visit_BinOp( s, node ):
    op = node.op
    if isinstance( op, s.BinOp_max_nbits ):
      with s.register_context( node.Type ):
        s.visit( node.left )
        s.visit( node.right )
    elif isinstance( op, s.BinOp_left_nbits ):
      with s.register_context( node.Type ):
        s.visit( node.left )
      with s.register_context( node.right.Type ):
        s.visit( node.right )
    else:
      raise Exception( 'RTLIRTypeCheck internal error: unrecognized op!' )

  def visit_Compare( s, node ):
    l_type = node.left.Type.get_dtype()
    r_type = node.right.Type.get_dtype()
    l_explicit, r_explicit = node.left._is_explicit, node.right._is_explicit
    l_nbits, r_nbits = l_type.get_length(), r_type.get_length()
    if l_explicit and r_explicit:
      with s.register_context( node.left.Type ):
        s.visit( node.left )
      with s.register_context( node.right.Type ):
        s.visit( node.right )
    else:
      explicit = node.left.Type
      if not l_explicit:
        explicit = node.right.Type
      with s.register_context( explicit ):
        s.visit( node.left )
        s.visit( node.right )
