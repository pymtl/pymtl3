#=========================================================================
# BehavioralRTLIRGenL2Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Oct 20, 2018
"""Provide L2 behavioral RTLIR generation pass."""

import ast

from pymtl3.passes.BasePass import BasePass, PassMetadata
from pymtl3.passes.rtlir.errors import PyMTLSyntaxError
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.rtlir.util.utility import get_ordered_upblks, get_ordered_update_ff

from . import BehavioralRTLIR as bir
from .BehavioralRTLIRGenL1Pass import BehavioralRTLIRGeneratorL1


class BehavioralRTLIRGenL2Pass( BasePass ):
  def __call__( s, m ):
    """ generate RTLIR for all upblks of m"""
    if not hasattr( m, '_pass_behavioral_rtlir_gen' ):
      m._pass_behavioral_rtlir_gen = PassMetadata()

    m._pass_behavioral_rtlir_gen.rtlir_upblks = {}
    visitor = BehavioralRTLIRGeneratorL2( m )
    upblks = {
      'CombUpblk' : get_ordered_upblks(m),
      'SeqUpblk'  : get_ordered_update_ff(m),
    }
    # Sort the upblks by their name
    upblks['CombUpblk'].sort( key = lambda x: x.__name__ )
    upblks['SeqUpblk'].sort( key = lambda x: x.__name__ )

    for upblk_type in ( 'CombUpblk', 'SeqUpblk' ):
      for blk in upblks[ upblk_type ]:
        visitor._upblk_type = upblk_type
        upblk_info = m.get_update_block_info( blk )
        upblk = visitor.enter( blk, upblk_info[-1] )
        upblk.is_lambda = upblk_info[0]
        upblk.src       = upblk_info[1]
        upblk.lino      = upblk_info[2]
        upblk.filename  = upblk_info[3]
        m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] = upblk

class BehavioralRTLIRGeneratorL2( BehavioralRTLIRGeneratorL1 ):
  def __init__( s, component ):
    super().__init__( component )
    s.loop_var_env = set()
    s.tmp_var_env = set()

    # opmap maps an ast operator to its RTLIR counterpart.
    s.opmap = {
      # Bool operators
      ast.And    : bir.And(),       ast.Or     : bir.Or(),
      # Unary operators
      ast.Invert : bir.Invert(),    ast.Not    : bir.Not(),
      ast.UAdd   : bir.UAdd(),      ast.USub   : bir.USub(),
      # Binary operators
      ast.Add    : bir.Add(),       ast.Sub    : bir.Sub(),
      ast.Mult   : bir.Mult(),      ast.Div    : bir.Div(),
      ast.Mod    : bir.Mod(),       ast.Pow    : bir.Pow(),
      ast.LShift : bir.ShiftLeft(), ast.RShift : bir.ShiftRightLogic(),
      ast.BitOr  : bir.BitOr(),     ast.BitAnd : bir.BitAnd(),
      ast.BitXor : bir.BitXor(),
      # Compare bir.bir.operators
      ast.Eq     : bir.Eq(),        ast.NotEq  : bir.NotEq(),
      ast.Lt     : bir.Lt(),        ast.LtE    : bir.LtE(),
      ast.Gt     : bir.Gt(),        ast.GtE    : bir.GtE()
    }

  def visit_Call( s, node ):
    obj = s.get_call_obj( node )
    # At L2 we add bool type but we do not support instantiating a bool
    # value -- that should always be the result of a comparison!
    if obj is rdt.Bool:
      raise PyMTLSyntaxError( s.blk, node,
        'bool values cannot be instantiated explicitly!' )
    return super().visit_Call( node )

  def visit_Name( s, node ):
    # temporary variable
    if (not node.id in s.closure) and (not node.id in s.globals):
      # check if is a LoopVar or not
      if node.id in s.loop_var_env:
        ret = bir.LoopVar( node.id )
      elif node.id in s.tmp_var_env:
        ret = bir.TmpVar( node.id, s._upblk_name )
      elif isinstance( node.ctx, ast.Load ):
        # trying to load an unregistered tmpvar
        raise PyMTLSyntaxError( s.blk, node,
          'tmpvar ' + node.id + ' used before assignment!' )
      else:
        # This is the first time we see this tmp var
        s.tmp_var_env.add( node.id )
        ret = bir.TmpVar( node.id, s._upblk_name )
      ret.ast = node
      return ret

    else:
      return super().visit_Name( node )

  def visit_If( s, node ):
    cond = s.visit( node.test )
    body = []
    for body_stmt in node.body:
      body.append( s.visit( body_stmt ) )
    orelse = []
    for orelse_stmt in node.orelse:
      orelse.append( s.visit( orelse_stmt ) )
    ret = bir.If( cond, body, orelse )
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
    var = bir.LoopVarDecl( node.target.id )
    if not isinstance( node.iter, ast.Call ):
      raise PyMTLSyntaxError( s.blk, node,
        "for loops can only use range() after 'in'!" )
    if node.iter.func.id != 'range':
      raise PyMTLSyntaxError( s.blk, node,
        "for loops can only use range() after 'in'!" )
    args = node.iter.args

    if len( args ) == 1:
      # range( end )
      start = bir.Number( 0 )
      end = s.visit( args[0] )
      step = bir.Number( 1 )
    elif len( args ) == 2:
      # range( start, end )
      start = s.visit( args[0] )
      end = s.visit( args[1] )
      step = bir.Number( 1 )
    elif len( args ) == 3:
      # range( start, end, step )
      start = s.visit( args[0] )
      end = s.visit( args[1] )
      step = s.visit( args[2] )
    else:
      raise PyMTLSyntaxError( s.blk, node,
        "1~3 arguments should be given to range!" )

    # Then visit all statements inside the loop
    body = []
    for body_stmt in node.body:
      body.append( s.visit( body_stmt ) )

    # Before we return, clear the loop variable in the loop variable
    # environment
    s.loop_var_env.remove( loop_var_name )
    ret = bir.For( var, start, end, step, body )
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

    ret = bir.BoolOp( op, values )
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
    ret = bir.BinOp( left, op, right )
    ret.ast = node
    return ret

  def visit_UnaryOp( s, node ):
    if not type(node.op) in s.opmap:
      raise PyMTLSyntaxError( s.blk, node,
        'Operator ' + str( node.op ) + ' is not supported!' )
    op  = s.opmap[ type( node.op ) ]
    op.ast = node.op
    operand = s.visit( node.operand )
    ret = bir.UnaryOp( op, operand )
    ret.ast = node
    return ret

  def visit_IfExp( s, node ):
    cond = s.visit( node.test )
    body = s.visit( node.body )
    orelse = s.visit( node.orelse )
    ret = bir.IfExp( cond, body, orelse )
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
    ret = bir.Compare( left, op, right )
    ret.ast = node
    return ret
