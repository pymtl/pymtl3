#=========================================================================
# BehavioralRTLIRGenL2Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Oct 20, 2018
"""Provide L2 behavioral RTLIR generation pass."""
from __future__ import absolute_import, division, print_function

import ast

from pymtl import *
from pymtl.passes import BasePass
from pymtl.passes.BasePass import PassMetadata
from pymtl.passes.rtlir.errors import PyMTLSyntaxError
from pymtl.passes.rtlir.RTLIRDataType import Bool

from .BehavioralRTLIR import *
from .BehavioralRTLIRGenL1Pass import BehavioralRTLIRGeneratorL1


class BehavioralRTLIRGenL2Pass( BasePass ):
  def __call__( s, m ):
    """ generate RTLIR for all upblks of m"""
    if not hasattr( m, '_pass_behavioral_rtlir_gen' ):
      m._pass_behavioral_rtlir_gen = PassMetadata()

    m._pass_behavioral_rtlir_gen.rtlir_upblks = {}
    visitor = BehavioralRTLIRGeneratorL2( m )
    upblks = {
      'CombUpblk' : m.get_update_blocks() - m.get_update_on_edge(),
      'SeqUpblk'  : m.get_update_on_edge()
    }

    for upblk_type in ( 'CombUpblk', 'SeqUpblk' ):
      for blk in upblks[ upblk_type ]:
        visitor._upblk_type = upblk_type
        m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] = \
          visitor.enter( blk, m.get_update_block_ast( blk ) )

class BehavioralRTLIRGeneratorL2( BehavioralRTLIRGeneratorL1 ):
  def __init__( s, component ):
    super( BehavioralRTLIRGeneratorL2, s ).__init__( component )
    s.loop_var_env = set()
    s.tmp_var_env = set()

    # opmap maps an ast operator to its RTLIR counterpart.
    s.opmap = {
      # Bool operators
      ast.And    : And(),       ast.Or     : Or(),
      # Unary operators
      ast.Invert : Invert(),    ast.Not    : Not(),
      ast.UAdd   : UAdd(),      ast.USub   : USub(),
      # Binary operators
      ast.Add    : Add(),       ast.Sub    : Sub(),
      ast.Mult   : Mult(),      ast.Div    : Div(),
      ast.Mod    : Mod(),       ast.Pow    : Pow(),
      ast.LShift : ShiftLeft(), ast.RShift : ShiftRightLogic(),
      ast.BitOr  : BitOr(),     ast.BitAnd : BitAnd(),
      ast.BitXor : BitXor(),
      # Compare operators
      ast.Eq     : Eq(),        ast.NotEq  : NotEq(),
      ast.Lt     : Lt(),        ast.LtE    : LtE(),
      ast.Gt     : Gt(),        ast.GtE    : GtE()
    }

  def visit_AugAssign( s, node ):
    """Return the behavioral RTLIR of augmented assign.
    
    Preserve the form of augmented assignment instead of transforming it 
    into a normal assignment.
    """
    if not type(node.op) in s.opmap:
      raise PyMTLSyntaxError( s.blk, node,
        'Operator ' + node.op + ' is not supported!' )
    value = s.visit( node.value )
    target = s.visit( node.target )
    op  = s.opmap[ type( node.op ) ]
    op.ast = node.op
    ret = AugAssign( target, op, value )
    ret.ast = node
    return ret

  def visit_Call( s, node ):
    obj = s.get_call_obj( node )
    # At L2 we add bool type but we do not support instantiating a bool
    # value -- that should always be the result of a comparison!
    if obj is Bool:
      raise PyMTLSyntaxError( s.blk, node,
        'bool values cannot be instantiated explicitly!' )
    return super( BehavioralRTLIRGeneratorL2, s ).visit_Call( node )

  def visit_Name( s, node ):
    if (not node.id in s.closure) and (not node.id in s.globals):
      # temporary variable
      # check if is a LoopVar or not
      if node.id in s.loop_var_env:
        ret = LoopVar( node.id )
      elif node.id in s.tmp_var_env:
        ret = TmpVar( node.id, s._upblk_name )
      elif isinstance( node.ctx, ast.Load ):
        # trying to load an unregistered tmpvar
        raise PyMTLSyntaxError( s.blk, node,
          'tmpvar ' + node.id + ' used before assignment!' )
      else:
        # This is the first time we see this tmp var
        s.tmp_var_env.add( node.id )
        ret = TmpVar( node.id, s._upblk_name )
      ret.ast = node
      return ret
    else:
      return super( BehavioralRTLIRGeneratorL2, s ).visit_Name( node )

  def visit_If( s, node ):
    cond = s.visit( node.test )

    body = []
    for body_stmt in node.body:
      body.append( s.visit( body_stmt ) )
    orelse = []
    for orelse_stmt in node.orelse:
      orelse.append( s.visit( orelse_stmt ) )
    ret = If( cond, body, orelse )
    ret.ast = node
    return ret

  def visit_For( s, node ):
    # First fill the loop_var, start, end, step fields
    if node.orelse != []:
      raise PyMTLSyntaxError( s.blk, node,
        "for loops cannot have 'else' branch!" )
    if not isinstance( node.target, ast.Name ):
      raise PyMTLSyntaxError( s.blk, node,
        "The loop index must be a temporary variable!" )
    loop_var_name = node.target.id

    # Check whether loop_var_name has been defined before
    if loop_var_name in s.loop_var_env:
      raise PyMTLSyntaxError( s.blk, node,
        "Redefinition of loop index " + loop_var_name + "!" )

    # Add loop_var to the loop variable environment
    s.loop_var_env.add( loop_var_name )
    var = LoopVarDecl( node.target.id )
    if not isinstance( node.iter, ast.Call ):
      raise PyMTLSyntaxError( s.blk, node,
        "for loops can only use (x)range() after 'in'!" )
    if not node.iter.func.id in [ 'xrange', 'range' ]:
      raise PyMTLSyntaxError( s.blk, node,
        "for loops can only use (x)range() after 'in'!" )
    args = node.iter.args

    if len( args ) == 1:
      # xrange( end )
      start = Number( 0 )
      end = s.visit( args[0] )
      step = Number( 1 )
    elif len( args ) == 2:
      # xrange( start, end )
      start = s.visit( args[0] )
      end = s.visit( args[1] )
      step = Number( 1 )
    elif len( args ) == 3:
      # xrange( start, end, step )
      start = s.visit( args[0] )
      end = s.visit( args[1] )
      step = s.visit( args[2] )
    else:
      raise PyMTLSyntaxError( s.blk, node,
        "1~3 arguments should be given to (x)range!" )

    # Then visit all statements inside the loop
    body = []
    for body_stmt in node.body:
      body.append( s.visit( body_stmt ) )

    # Before we return, clear the loop variable in the loop variable
    # environment
    s.loop_var_env.remove( loop_var_name )
    ret = For( var, start, end, step, body )
    ret.ast = node
    return ret

  def visit_BoolOp( s, node ):
    if not type(node.op) in s.opmap:
      raise PyMTLSyntaxError( s.blk, node,
        'Operator ' + str( node.op ) + ' is not supported!' )
    op  = s.opmap[ type( node.op ) ]
    op.ast = node.op

    values = []
    for value in node.values:
      values.append( s.visit( value ) )

    ret = BoolOp( op, values )
    ret.ast = node
    return ret

  def visit_BinOp( s, node ):
    left  = s.visit( node.left )
    right = s.visit( node.right )
    if not type(node.op) in s.opmap:
      raise PyMTLSyntaxError( s.blk, node,
        'Operator ' + str( node.op ) + ' is not supported!' )
    op  = s.opmap[ type( node.op ) ]
    op.ast = node.op
    ret = BinOp( left, op, right )
    ret.ast = node
    return ret

  def visit_UnaryOp( s, node ):
    if not type(node.op) in s.opmap:
      raise PyMTLSyntaxError( s.blk, node,
        'Operator ' + str( node.op ) + ' is not supported!' )
    op  = s.opmap[ type( node.op ) ]
    op.ast = node.op
    operand = s.visit( node.operand )
    ret = UnaryOp( op, operand )
    ret.ast = node
    return ret

  def visit_IfExp( s, node ):
    cond = s.visit( node.test )
    body = s.visit( node.body )
    orelse = s.visit( node.orelse )
    ret = IfExp( cond, body, orelse )
    ret.ast = node
    return ret

  def visit_Compare( s, node ):
    if not type(node.ops[0]) in s.opmap:
      raise PyMTLSyntaxError( s.blk, node,
        'Operator ' + str( node.ops[0] ) + ' is not supported!' )
    if len( node.ops ) != 1 or len( node.comparators ) != 1:
      raise PyMTLSyntaxError( s.blk, node,
        'Comparison can only have 2 operands!' )

    op  = s.opmap[ type( node.ops[0] ) ]
    op.ast = node.ops[0]
    left = s.visit( node.left )
    right = s.visit( node.comparators[0] )
    ret = Compare( left, op, right )
    ret.ast = node
    return ret
