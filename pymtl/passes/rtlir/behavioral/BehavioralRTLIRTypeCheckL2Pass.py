#=========================================================================
# BehavioralRTLIRTypeCheckL2Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : March 29, 2019
"""Provide L2 behavioral RTLIR type check pass."""
from __future__ import absolute_import, division, print_function

import pymtl
from pymtl.passes import BasePass
from pymtl.passes.BasePass import PassMetadata
from pymtl.passes.rtlir.RTLIRType import *

from .BehavioralRTLIR import *
from .BehavioralRTLIRTypeCheckL1Pass import BehavioralRTLIRTypeCheckVisitorL1
from .errors import PyMTLTypeError


class BehavioralRTLIRTypeCheckL2Pass( BasePass ):
  def __call__( s, m ):
    """Perform type checking on all RTLIR in rtlir_upblks."""
    if not hasattr( m, '_pass_behavioral_rtlir_type_check' ):
      m._pass_behavioral_rtlir_type_check = PassMetadata()
    m._pass_behavioral_rtlir_type_check.rtlir_freevars = {}
    m._pass_behavioral_rtlir_type_check.rtlir_tmpvars = {}

    visitor = BehavioralRTLIRTypeCheckVisitorL2(
      m,
      m._pass_behavioral_rtlir_type_check.rtlir_freevars,
      m._pass_behavioral_rtlir_type_check.rtlir_tmpvars
    )

    for blk in m.get_update_blocks():
      visitor.enter( blk, m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] )

class BehavioralRTLIRTypeCheckVisitorL2( BehavioralRTLIRTypeCheckVisitorL1 ):
  def __init__( s, component, freevars, tmpvars ):
    super(BehavioralRTLIRTypeCheckVisitorL2, s).__init__(component, freevars)
    s.freevars = freevars
    s.tmpvars = tmpvars
    s.BinOp_max_nbits = (Add, Sub, Mult, Div, Mod, Pow, BitAnd, BitOr, BitXor)
    s.BinOp_left_nbits = ( ShiftLeft, ShiftRightLogic )
    s.type_expect = {}
    lhs_types = ( Port, Wire, NoneType )

    s.type_expect[ 'Assign' ] = {
      'target' : ( lhs_types, 'lhs of assignment must be signal/tmpvar!' ),
      'value' : ( Signal, 'rhs of assignment should be signal/const!' )
    }
    s.type_expect[ 'AugAssign' ] = {
      'target' : ( lhs_types, 'lhs of assignment must be signal/tmpvar!' ),
      'value' : ( Signal, 'rhs of assignment should be signal/const!' )
    }
    s.type_expect[ 'BinOp' ] = {
      'left' : ( Signal, 'lhs of binop should be signal/const!' ),
      'right' : ( Signal, 'rhs of binop should be signal/const!' ),
    }
    s.type_expect[ 'UnaryOp' ] = {
      'operand' : ( Signal, 'op of binop should be signal/const!' )
    }
    s.type_expect[ 'For' ] = {
      'start' : ( Const, 'the start of a for-loop must be a constant expression!' ),
      'end':( Const, 'the end of a for-loop must be a constant expression!' ),
      'step':( Const, 'the step of a for-loop must be a constant expression!' )
    }
    s.type_expect[ 'If' ] = {
      'cond' : ( Signal, 'the condition of if must be a signal!' )
    }
    s.type_expect[ 'IfExp' ] = {
      'cond' : ( Signal, 'the condition of if-exp must be a signal!' ),
      'body' : ( Signal, 'the body of if-exp must be a signal!' ),
      'orelse' : ( Signal, 'the else branch of if-exp must be a signal!' )
    }

  def eval_const_binop( s, l, op, r ):
    """Evaluate ( l op r ) and return the result as an integer."""
    assert type( l ) == int or isinstance( l, pymtl.Bits )
    assert type( r ) == int or isinstance( r, pymtl.Bits )
    op_dict = {
      Add       : '+',  Sub   : '-',  Mult : '*',  Div  : '/',
      Mod       : '%',  Pow   : '**',
      ShiftLeft : '<<', ShiftRightLogic : '>>',
      BitAnd    : '&',  BitOr : '|',  BitXor : '^',
    }
    _op = op_dict[ type( op ) ]
    return eval( 'l{_op}r'.format( **locals() ) )

  def visit_Assign( s, node ):
    # RHS should have the same type as LHS
    rhs_type = node.value.Type
    lhs_type = node.target.Type

    if isinstance( node.target, TmpVar ):
      # Creating a temporaray variable
      node.target.Type = rhs_type
      s.tmpvars[ node.target.name ] = rhs_type
      node.Type = None

    else:
      # non-temporary assignment is an L1 thing
      super( BehavioralRTLIRTypeCheckVisitorL2, s ).visit_Assign( node )

  def visit_AugAssign( s, node ):
    target = node.target
    op = node.op
    value = node.value
    
    # perform type check as if this node corresponds to
    # target = target op value
    l_nbits = target.Type.nbits
    r_nbits = value.Type.nbits
    node.Type = None

  def visit_If( s, node ):
    # Can the type of condition be cast into bool?
    dtype = node.cond.Type.get_dtype()
    if not Bool()( dtype ):
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
    except Exception:
      raise
    node.Type = None

  def visit_LoopVar( s, node ):
    node.Type = Const( Vector( 32 ) )

  def visit_TmpVar( s, node ):
    if not node.name in s.tmpvars:
      # This tmpvar is being created. Later when it is used, its type can
      # be read from the tmpvar type environment.
      node.Type = NoneType()
    else:
      node.Type = s.tmpvars[ node.name ]

  def visit_IfExp( s, node ):
    # Can the type of condition be cast into bool?
    if not Bool()( node.cond.Type.get_dtype() ):
      raise PyMTLTypeError( s.blk, node.ast,
        'the condition of "if-exp" cannot be converted to bool!' )
    # body and orelse must have the same type
    # if node.body.Type != node.orelse.Type:
    if not node.body.Type.get_dtype()( node.orelse.Type.get_dtype() ):
      raise PyMTLTypeError( s.blk, node.ast,
        'the body and orelse of "if-exp" must have the same type!' )
    node.Type = node.body.Type

  def visit_UnaryOp( s, node ):
    if isinstance( node.op, Not ):
      if not Bool()( node.operand.Type.get_dtype() ):
        raise PyMTLTypeError( s.blk, node.ast,
          'the operand of "unary-expr" cannot be cast to bool!' )
      node.Type = Wire( Bool() )
    else:
      node.Type = node.operand.Type

  def visit_BoolOp( s, node ):
    for value in node.values:
      if not isinstance(value.Type, Signal) or not Bool()(value.Type.get_dtype()):
        raise PyMTLTypeError( s.blk, node.ast,
          "{} of {} cannot be cast into bool!".format( value, value.Type ))
    node.Type = Wire( Bool() )

  def visit_BinOp( s, node ):
    op = node.op
    l_type = node.left.Type.get_dtype()
    r_type = node.right.Type.get_dtype()
    if not( Vector(1)( l_type ) and Vector(1)( r_type ) ):
      raise PyMTLTypeError( s.blk, node.ast,
        "both sides of operation should be of vector type!" )

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

    l_val = getattr( node.left, '_value', None )
    r_val = getattr( node.right, '_value', None )
    # Both sides are constant expressions
    # if hasattr( node.left, '_value' ) and hasattr( node.right, '_value' ):
    if l_val is not None and r_val is not None:
      node._value = s.eval_const_binop( l_val, op, r_val )
      node.Type = Const( Vector( res_nbits ) )
    # Both sides are constant but the value cannot be determined at elaboration time
    elif isinstance(node.left.Type, Const) and isinstance(node.right.Type, Const):
      node.Type = Const( Vector( res_nbits ) )
    else:
      node.Type = Wire( Vector( res_nbits ) )

  def visit_Compare( s, node ):
    node.Type = Wire( Bool() )
