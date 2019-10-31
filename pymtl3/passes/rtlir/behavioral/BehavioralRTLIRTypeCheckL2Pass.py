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
from .BehavioralRTLIRTypeCheckL1Pass import BehavioralRTLIRTypeCheckVisitorL1


class BehavioralRTLIRTypeCheckL2Pass( BasePass ):
  def __call__( s, m ):
    """Perform type checking on all RTLIR in rtlir_upblks."""
    if not hasattr( m, '_pass_behavioral_rtlir_type_check' ):
      m._pass_behavioral_rtlir_type_check = PassMetadata()
    m._pass_behavioral_rtlir_type_check.rtlir_freevars = OrderedDict()
    m._pass_behavioral_rtlir_type_check.rtlir_tmpvars = OrderedDict()
    m._pass_behavioral_rtlir_type_check.rtlir_accessed = set()

    visitor = BehavioralRTLIRTypeCheckVisitorL2(
      m,
      m._pass_behavioral_rtlir_type_check.rtlir_freevars,
      m._pass_behavioral_rtlir_type_check.rtlir_accessed,
      m._pass_behavioral_rtlir_type_check.rtlir_tmpvars
    )

    for blk in m.get_update_block_order():
      visitor.enter( blk, m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] )

class BehavioralRTLIRTypeCheckVisitorL2( BehavioralRTLIRTypeCheckVisitorL1 ):
  def __init__( s, component, freevars, accessed, tmpvars ):
    super().__init__(component, freevars, accessed)
    s.tmpvars = tmpvars
    s.BinOp_max_nbits = (bir.Add, bir.Sub, bir.Mult, bir.Div, bir.Mod, bir.Pow,
                         bir.BitAnd, bir.BitOr, bir.BitXor)
    s.BinOp_left_nbits = ( bir.ShiftLeft, bir.ShiftRightLogic )
    s.type_expect = {}
    lhs_types = ( rt.Port, rt.Wire, rt.NetWire, rt.NoneType )

    s.type_expect[ 'Assign' ] = {
      'target' : ( lhs_types, 'lhs of assignment must be signal/tmpvar!' ),
      'value' : ( rt.Signal, 'rhs of assignment should be signal/const!' )
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

  def visit_Assign( s, node ):
    # RHS should have the same type as LHS
    rhs_type = node.value.Type
    lhs_type = node.target.Type

    if isinstance( node.target, bir.TmpVar ):
      tmpvar_id = (node.target.name, node.target.upblk_name)
      if lhs_type != rt.NoneType() and lhs_type.get_dtype() != rhs_type.get_dtype():
        raise PyMTLTypeError( s.blk, node.ast,
          f'conflicting type {rhs_type} for temporary variable {node.target.name}({lhs_type})!' )

      # Creating a temporaray variable
      # Reminder that a temporary variable is essentially a wire. So we use
      # rt.Wire here instead of rt.NetWire
      node.target.Type = rt.Wire( rhs_type.get_dtype() )
      s.tmpvars[ tmpvar_id ] = rt.Wire( rhs_type.get_dtype() )
      node.Type = None

    else:
      # non-temporary assignment is an L1 thing
      super().visit_Assign( node )

  def visit_If( s, node ):
    # Can the type of condition be cast into bool?
    dtype = node.cond.Type.get_dtype()
    if not rdt.Bool()( dtype ):
      raise PyMTLTypeError( s.blk, node.ast,
        'the condition of "if" cannot be converted to bool!'
      )
    node.Type = None

  def visit_For( s, node ):
    try:
      step = node.step._value
      if step == 0:
        raise PyMTLTypeError( s.blk, node.ast,
          'the step of for-loop cannot be zero!' )
    except AttributeError:
      raise PyMTLTypeError( s.blk, node.ast,
        'the step of for-loop must be a constant!' )
    node.Type = None

  def visit_LoopVar( s, node ):
    node.Type = rt.Const( rdt.Vector( 32 ), None )

  def visit_TmpVar( s, node ):
    tmpvar_id = (node.name, node.upblk_name)
    if tmpvar_id not in s.tmpvars:
      # This tmpvar is being created. Later when it is used, its type can
      # be read from the tmpvar type environment.
      node.Type = rt.NoneType()

    else:
      node.Type = s.tmpvars[ tmpvar_id ]

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

  def visit_UnaryOp( s, node ):
    if isinstance( node.op, bir.Not ):
      dtype = node.operand.Type.get_dtype()
      if not rdt.Bool()( dtype ):
        raise PyMTLTypeError( s.blk, node.ast,
          'the operand of "Logic-not" cannot be cast to bool!' )
      if dtype.get_length() != 1:
        raise PyMTLTypeError( s.blk, node.ast,
          'the operand of "Logic-not" is not a single bit!' )
      node.Type = rt.NetWire( rdt.Bool() )
    else:
      node.Type = node.operand.Type

  def visit_BoolOp( s, node ):
    for value in node.values:
      if not isinstance(value.Type, rt.Signal) or not rdt.Bool()(value.Type.get_dtype()):
        raise PyMTLTypeError( s.blk, node.ast,
          f"{value} of {value.Type} cannot be cast into bool!")
    node.Type = rt.NetWire( rdt.Bool() )

  def visit_BinOp( s, node ):
    op = node.op
    l_type = node.left.Type.get_dtype()
    r_type = node.right.Type.get_dtype()
    if not( rdt.Vector(1)( l_type ) and rdt.Vector(1)( r_type ) ):
      raise PyMTLTypeError( s.blk, node.ast,
        f"both sides of {op.__class__.__name__} should be of vector type!" )

    if not isinstance( op, s.BinOp_left_nbits ) and l_type != r_type:
      raise PyMTLTypeError( s.blk, node.ast,
        f"LHS and RHS of {op.__class__.__name__} should have the same type ({l_type} vs {r_type})!" )

    l_nbits = l_type.get_length()
    r_nbits = r_type.get_length()

    # Enforcing Verilog bitwidth inference rules
    res_nbits = 0
    if isinstance( op, s.BinOp_max_nbits ):
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
    except AttributeError:
      # Both sides are constant but the value cannot be determined statically
      if isinstance(node.left.Type, rt.Const) and isinstance(node.right.Type, rt.Const):
        node.Type = rt.Const( rdt.Vector( res_nbits ), None )

      # Variable
      else:
        node.Type = rt.NetWire( rdt.Vector( res_nbits ) )

  def visit_Compare( s, node ):
    l_type = node.left.Type.get_dtype()
    r_type = node.right.Type.get_dtype()
    if l_type != r_type:
      raise PyMTLTypeError( s.blk, node.ast,
        f"LHS and RHS of {node.op.__class__.__name__} have different types ({l_type} vs {r_type})!" )
    node.Type = rt.NetWire( rdt.Bool() )
