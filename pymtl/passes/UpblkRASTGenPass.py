#========================================================================
# UpblkRASTGenPass.py
#========================================================================
# This pass generates the RAST of a given upblk.
#
# Author : Peitian Pan
# Date   : Oct 20, 2018

import ast
import RAST

from pymtl       import *
from pymtl.model import ComponentLevel1
from BasePass    import BasePass
from collections import defaultdict, deque
from errors      import PyMTLSyntaxError
from inspect     import getsourcefile, getsourcelines

class UpblkRASTGenPass( BasePass ):

  def __call__( s, m ):
    """ generate RAST for all upblks of m and write them to m._rast """

    m._rast = {}

    visitor = UpblkRASTGenVisitor( m )

    for ( blk, ast ) in m.get_update_block_ast_pairs():

      m._rast[ blk ] = visitor.enter( blk, ast )

#-----------------------------------------------------------------------
# Visitor for generating RAST for an update block
#-----------------------------------------------------------------------

class UpblkRASTGenVisitor( ast.NodeVisitor ):

  def __init__( s, component ):
    s.component = component
    s.mapping   = component.get_astnode_obj_mapping()

  def enter( s, blk, ast ):
    """ entry point for RAST generation """
    s.blk     = blk

    # s.globals contains a dict of the global namespace of the module where
    # blk was defined
    s.globals = blk.func_globals

    # s.closure contains the free variables defined in an enclosing scope.
    # Basically this is the model instance s.
    s.closure = {}

    for i, var in enumerate( blk.func_code.co_freevars ):
      try: 
        s.closure[ var ] = blk.func_closure[ i ].cell_contents
      except ValueError: 
        pass

    ret = s.visit( ast )

    return ret 

  #---------------------------------------------------------------------
  # Valid ast nodes
  #---------------------------------------------------------------------

  def visit_Module( s, node ):
    if len( node.body ) != 1 or\
       not isinstance( node.body[0], ast.FunctionDef ):
      raise PyMTLSyntaxError(
        s.blk, node, 'Update blocks should have exactly one FuncDef!' 
      )

    ret = s.visit( node.body[0] )
    ret.ast = node

    return ret

  def visit_FunctionDef( s, node ):
    # We do not need to check the decorator list -- the fact that we are
    # visiting this node ensures this node was added to the upblk
    # dictionary through s.update() (or other PyMTL decorators) earlier!

    # Check the arguments of the function
    if node.args.args or node.args.vararg or node.args.kwarg:
      raise PyMTLSyntaxError(
        s.blk, node, 'Update blocks should not have arguments!' 
      )

    # Assume this is a combinational update blocks
    # Maybe sequential or other upblks should be collected in different
    # passes?
    ret = RAST.CombUpblk( [] )

    for stmt in node.body:
      ret.body.append( s.visit( stmt ) )

    ret.ast = node

    return ret

  def visit_Assign( s, node ):
    value = s.visit( node.value )
    targets = []
    for target in node.targets:
      targets.append( s.visit( target ) )

    ret = RAST.Assign( targets, value )
    ret.ast = node

    return ret

  def visit_AugAssign( s, node ): 
    # x op= y  -->  x = x op y
    value = s.visit( node.value )
    target = s.visit( node.target )
    try:
      op  = opmap[ type( node.op ) ]
      op.ast = node.op
    except KeyError:
      raise PyMTLSyntaxError(
        s.blk, node,  
        'Operator ' + node.op + ' is not supported!'
      )

    expr = RAST.BinOp( target, op, value )
    expr.ast = node

    ret = RAST.Assign( [ target ], expr )
    ret.ast = node

    return ret

  def visit_If( s, node ):
    # Not implemented yet!
    raise

  def visit_Expr( s, node ):
    # Should only be useful as a call to SystemVerilog tasks
    # Not implemented yet!
    raise

  def visit_BinOp( s, node ):
    left  = s.visit( node.left )
    right = s.visit( node.right )

    try:
      op  = opmap[ type( node.op ) ]
      op.ast = node.op
    except KeyError:
      raise PyMTLSyntaxError(
        s.blk, node,  
        'Operator ' + node.op + ' is not supported!'
      )

    ret = RAST.BinOp( left, op, right )
    ret.ast = node

    return ret

  def visit_UnaryOp( s, node ):
    # Not implemented yet
    raise

  def visit_IfExp( s, node ):
    # Not implemented yet
    raise

  def visit_Compare( s, node ):
    # Not implemented yet
    raise

  def visit_Call( s, node ):
    # Some data types are interpreted as function calls in the Python AST
    # Assume only constants are allowed as the argument of BitsX
    # Example: Bits4(2)
    actual_node = node.func

    # Find the corresponding class through the name
    # Currently only BitsX class is supported
    # TODO: Support Verilog task?
    try:
      if actual_node.id in s.globals:
        call = s.globals[ actual_node.id ]
      else:
        raise NameError
    except AttributeError:
      raise PyMTLSyntaxError(
        s.blk, node, node.func + ' function call is not supported!'
      )
    except NameError:
      raise PyMTLSyntaxError(
        s.blk, node, node.func.id + ' function is not found!'
      )

    # Extract the number of bits
    try:
      nbits = call.nbits
    except AttributeError: 
      raise PyMTLSyntaxError(
        s.blk, node, 'Expecting BitsX class but found ' + call.__name__
      )

    if len( node.args ) != 1:
      raise PyMTLSyntaxError(
        s.blk, node, 'Call to ' + call.__name__ + \
        ' should have exactly one arguement!'
      )

    arg = node.args[0]

    if isinstance( arg, ast.Num ):
      if arg.n < 0 or not isinstance( arg.n, int ):
        raise PyMTLSyntaxError(
          s.blk, node, 'only non-negative integers are allowed!'
        )
      if nbits <= 0:
        raise PyMTLSyntaxError(
          s.blk, node, 'bit width should be positive integers!'
        )
      if arg.n >= 2**nbits:
        raise PyMTLSyntaxError(
          s.blk, node, 'constant integer overflow!'
        )
      ret = RAST.Const( nbits, arg.n )
      ret.ast = node
      return ret
    else:
      raise PyMTLSyntaxError(
        s.blk, node, 'Invalid function call argument type ' +\
        arg.__class__.__name__ + '!'
      )

  def visit_Attribute( s, node ):
    ret = RAST.Attribute( s.visit( node.value ), node.attr )
    ret.ast = node
    return ret

  def visit_Subscript( s, node ):
    value = s.visit( node.value )
    if isinstance( node.slice, ast.Slice ):
      if not node.slice.step is None:
        raise PyMTLSyntaxError(
          s.blk, node, 'Slice with steps is not supported!'
        )
      lower, upper = s.visit( node.slice )

      ret = RAST.Slice( value, lower, upper )
      ret.ast = node

      return ret

    if isinstance( node.slice, ast.Index ):
      idx = s.visit( node.slice )

      ret = RAST.Index( value, idx )
      ret.ast = node

      return ret

    raise PyMTLSyntaxError(
      s.blk, node, 'Illegal subscript ' + node + ' encountered!'
    )

  def visit_Slice( s, node ):
    return ( s.visit( node.lower ), s.visit( node.upper ) )

  def visit_Index( s, node ):
    return s.visit( node.value )

  def visit_Name( s, node ):
    if node.id in s.globals:
      # Any examples for this?
      # return s.globals[ node.id ]
      return node.id
    elif node.id in s.closure:
      # Assume only s will appear here.
      # Example: s.x where s is in the closure of this upblk
      # However the local variables defined in the closure of blk, 
      # if they are used in the block, will also appear here. 
      #   s.x = Bits16(10)
      #   FSM_STATE_1 = Bits4(0)
      #   @s.update
      #   def logic():
      #     ...use s.x, FSM_STATE_1
      ret = RAST.Module( s.closure[ node.id ] )
      ret.ast = node

      return ret

    else:
      # Temporary variable encountered, currently unsupported
      raise PyMTLSyntaxError(
        s.blk, node, 'Temporary variable ' + node.id + ' is not supported!'
      )

  def visit_Num( s, node ):
    # nbits = 0 means this constant number is created without specifying 
    # its bitwidth.
    ret = RAST.Const( 0, node.n )
    ret.ast = node

    return ret

  #---------------------------------------------------------------------
  # TODO: Support some other AST nodes
  #---------------------------------------------------------------------

  def visit_For( s, ndoe ):
    raise

  # $display
  def visit_Print( s, ndoe ):
    raise

  # function
  def visit_Return( s, node ):
    raise

  # SV assertion
  def visit_Assert( s, node ):
    raise

  #---------------------------------------------------------------------
  # Explicitly invalid AST nodes
  #---------------------------------------------------------------------

  def visit_LambdaOp( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: lambda function' )

  def visit_Dict( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid type: dict' )

  def visit_Set( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid type: set' )

  def visit_List( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid type: list' )

  def visit_Tuple( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid type: tuple' )

  def visit_ListComp( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: list comprehension' )

  def visit_SetComp( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: set comprehension' )

  def visit_DictComp( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: dict comprehension' )

  def visit_GeneratorExp( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: generator expression' )

  def visit_Yield( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: yield' )

  def visit_Repr( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: repr' )

  def visit_Str( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: str' )

  def visit_ClassDef( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: classdef' )

  def visit_Delete( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: delete' )

  def visit_With( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: with' )

  def visit_Raise( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: raise' )

  def visit_TryExcept( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: try-except' )

  def visit_TryFinally( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: try-finally' )

  def visit_Import( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: import' )

  def visit_ImportFrom( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: import-from' )

  def visit_Exec( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: exec' )

  def visit_Global( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: global' )

  def visit_Pass( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: pass' )

  def visit_Break( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: break' )

  def visit_Continue( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: continue' )

  def visit_While( s, ndoe ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: while' )

  def visit_ExtSlice( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: extslice' )

  def visit_BoolOp( s, node ):
    raise PyMTLSyntaxError( s.blk, node, 'invalid operation: boolop' )

#-----------------------------------------------------------------------
# opmap definition
#-----------------------------------------------------------------------

opmap = {
  ast.Add    : RAST.Add(),
  ast.Sub    : RAST.Sub(),
  ast.LShift : RAST.ShiftLeft(),
  ast.RShift : RAST.ShiftRightLogic(),
  ast.BitOr  : RAST.BitOr(),
  ast.BitAnd : RAST.BitAnd(),
  ast.BitXor : RAST.BitXor(),
}

