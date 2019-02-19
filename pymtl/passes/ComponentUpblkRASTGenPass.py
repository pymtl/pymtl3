#=========================================================================
# ComponentUpblkRASTGenPass.py
#=========================================================================
# This pass generates the RAST of a given component.
#
# Author : Peitian Pan
# Date   : Oct 20, 2018

import ast

from pymtl       import *
from pymtl.dsl   import ComponentLevel1
from BasePass    import BasePass, PassMetadata
from errors      import PyMTLSyntaxError
from RAST        import *

class ComponentUpblkRASTGenPass( BasePass ):

  def __call__( s, m ):
    """ generate RAST for all upblks of m and write them to m._rast """

    m._pass_component_upblk_rast_gen = PassMetadata()

    m._pass_component_upblk_rast_gen.rast = {}

    visitor = UpblkRASTGenVisitor( m )

    for blk in m.get_update_blocks():
      m._pass_component_upblk_rast_gen.rast[ blk ] =\
        visitor.enter( blk, m.get_update_block_ast( blk ) )

#-------------------------------------------------------------------------
# UpblkRASTGenVisitor
#-------------------------------------------------------------------------
# Visitor class for generating RAST for an update block

class UpblkRASTGenVisitor( ast.NodeVisitor ):

  def __init__( s, component ):
    s.component = component
    s.mapping   = component.get_astnode_obj_mapping()

    s.loop_var_env = set()
    s.tmp_var_env = set()

    # opmap maps an ast operator to its RAST counterpart.
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
  # visit_Module
  #---------------------------------------------------------------------
  # The root of each upblk. RAST does not have a dedicated `module' node
  # type.

  def visit_Module( s, node ):
    if len( node.body ) != 1 or\
       not isinstance( node.body[0], ast.FunctionDef ):
      raise PyMTLSyntaxError(
        s.blk, node, 'Update blocks should have exactly one FuncDef!' 
      )

    ret = s.visit( node.body[0] )
    ret.ast = node

    return ret

  #-----------------------------------------------------------------------
  # visit_FunctionDef
  #-----------------------------------------------------------------------
  # We do not need to check the decorator list -- the fact that we are
  # visiting this node ensures this node was added to the upblk
  # dictionary through s.update() (or other PyMTL decorators) earlier!

  def visit_FunctionDef( s, node ):
    # Check the arguments of the function
    if node.args.args or node.args.vararg or node.args.kwarg:
      raise PyMTLSyntaxError(
        s.blk, node, 'Update blocks should not have arguments!' 
      )

    # Assume this is a combinational update blocks
    # Maybe sequential or other upblks should be collected in different
    # passes?
    ret = CombUpblk( node.name, [] )

    for stmt in node.body:
      ret.body.append( s.visit( stmt ) )

    ret.ast = node

    return ret

  #-----------------------------------------------------------------------
  # visit_Assign
  #-----------------------------------------------------------------------
  # Only one assignement target is allowed!

  def visit_Assign( s, node ):
    if len( node.targets ) != 1:
      raise PyMTLSyntaxError(
        s.blk, node, 'Assigning to multiple targets is not allowed!' 
      )

    value = s.visit( node.value )
    target = s.visit( node.targets[0] )

    ret = Assign( target, value )
    ret.ast = node

    return ret

  #-----------------------------------------------------------------------
  # visit_AugAssign
  #-----------------------------------------------------------------------
  # Preserve the form of augmented assignment instead of transforming it 
  # into a normal assignment.

  def visit_AugAssign( s, node ): 
    value = s.visit( node.value )
    target = s.visit( node.target )

    try:
      op  = s.opmap[ type( node.op ) ]
      op.ast = node.op

    except KeyError:
      raise PyMTLSyntaxError(
        s.blk, node, 'Operator ' + node.op + ' is not supported!'
      )

    ret = AugAssign( target, op, value )
    ret.ast = node

    return ret

  #-----------------------------------------------------------------------
  # visit_If
  #-----------------------------------------------------------------------

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

  #-----------------------------------------------------------------------
  # visit_For
  #-----------------------------------------------------------------------

  def visit_For( s, node ):
    # First fill the loop_var, start, end, step fields

    if node.orelse != []:
      raise PyMTLSyntaxError(
        s.blk, node, "for loops cannot have 'else' branch!"
      )

    if not isinstance( node.target, ast.Name ):
      raise PyMTLSyntaxError(
        s.blk, node, "The loop index must be a temporary variable!"
      )

    loop_var_name = node.target.id

    # Check whether loop_var_name has been defined before
    if loop_var_name in s.loop_var_env:
      raise PyMTLSyntaxError(
        s.blk, node, "Redefinition of loop index " + loop_var_name + "!"
      )

    # Add loop_var to the loop variable environment
    s.loop_var_env.add( loop_var_name )
    
    var = LoopVarDecl( node.target.id )

    if not isinstance( node.iter, ast.Call ):
      raise PyMTLSyntaxError(
        s.blk, node, "for loops can only use (x)range() after 'in'!"
      )

    if not node.iter.func.id in [ 'xrange', 'range' ]:
      raise PyMTLSyntaxError(
        s.blk, node, "for loops can only use (x)range() after 'in'!"
      )

    args = node.iter.args

    for arg in args:
      if not isinstance( arg, ast.Num ):
        raise PyMTLSyntaxError(
          s.blk, node, "(x)range can only have constant arguments!"
        )

    if len( args ) == 1:
      # xrange( end )
      start = Number( 0, 0 )
      end = s.visit( args[0] )
      step = Number( 0, 1 )

    elif len( args ) == 2:
      # xrange( start, end )
      start = s.visit( args[0] )
      end = s.visit( args[1] )
      step = Number( 0, 1 )

    elif len( args ) == 3:
      # xrange( start, end, step )
      start = s.visit( args[0] )
      end = s.visit( args[1] )
      step = s.visit( args[2] )

      if step.value == 0:
        raise PyMTLSyntaxError(
          s.blk, node, "step argument to (x)range cannot be 0!"
        )

    else:
      raise PyMTLSyntaxError(
        s.blk, node, "1~3 arguments should be given to (x)range!"
      )

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

  #-----------------------------------------------------------------------
  # visit_BoolOp
  #-----------------------------------------------------------------------

  def visit_BoolOp( s, node ):
    try:
      op  = s.opmap[ type( node.op ) ]
      op.ast = node.op

    except KeyError:
      raise PyMTLSyntaxError(
        s.blk, node, 'Operator ' + node.op + ' is not supported!'
      )

    values = []
    for value in node.values:
      values.append( s.visit( value ) )

    ret = BoolOp( op, values )
    ret.ast = node

    return ret

  #-----------------------------------------------------------------------
  # visit_Expr
  #-----------------------------------------------------------------------
  # ast.Expr might be useful when a statement is only a call to a task or 
  # a non-returning function.

  def visit_Expr( s, node ):
    # Should only be useful as a call to SystemVerilog tasks
    # Not implemented yet!
    raise PyMTLSyntaxError(
      s.blk, node, 'Task is not supported yet!'
    )

  #-----------------------------------------------------------------------
  # visit_BinOp
  #-----------------------------------------------------------------------

  def visit_BinOp( s, node ):
    left  = s.visit( node.left )
    right = s.visit( node.right )

    try:
      op  = s.opmap[ type( node.op ) ]
      op.ast = node.op

    except KeyError:
      raise PyMTLSyntaxError(
        s.blk, node, 'Operator ' + node.op + ' is not supported!'
      )

    ret = BinOp( left, op, right )
    ret.ast = node

    return ret

  #-----------------------------------------------------------------------
  # visit_UnaryOp
  #-----------------------------------------------------------------------

  def visit_UnaryOp( s, node ):
    try:
      op  = s.opmap[ type( node.op ) ]
      op.ast = node.op

    except KeyError:
      raise PyMTLSyntaxError(
        s.blk, node, 'Operator ' + node.op + ' is not supported!'
      )

    operand = s.visit( node.operand )

    ret = UnaryOp( op, operand )
    ret.ast = node

    return ret

  #-----------------------------------------------------------------------
  # visit_IfExp
  #-----------------------------------------------------------------------

  def visit_IfExp( s, node ):
    cond = s.visit( node.test )
    body = s.visit( node.body )
    orelse = s.visit( node.orelse )

    ret = IfExp( cond, body, orelse )
    ret.ast = node

    return ret

  #-----------------------------------------------------------------------
  # visit_Compare
  #-----------------------------------------------------------------------
  # Continuous comparison like x < y < z is not allowed.

  def visit_Compare( s, node ):
    if len( node.ops ) != 1 or len( node.comparators ) != 1:
      raise PyMTLSyntaxError(
        s.blk, node, 'Comparison can only have 2 operands!'
      )

    try:
      op  = s.opmap[ type( node.ops[0] ) ]
      op.ast = node.ops[0]

    except KeyError:
      raise PyMTLSyntaxError(
        s.blk, node, 'Operator ' + node.ops[0] + ' is not supported!'
      )

    left = s.visit( node.left )
    right = s.visit( node.comparators[0] )

    ret = Compare( left, op, right )
    ret.ast = node
    
    return ret

  #-----------------------------------------------------------------------
  # visit_Call
  #-----------------------------------------------------------------------
  # Some data types are interpreted as function calls in the Python AST
  # Example: Bits4(2)
  # These are converted to different RAST nodes in different contexts.

  def visit_Call( s, node ):
    actual_node = node.func

    # Find the corresponding object of node.func field
    # TODO: Support Verilog task?
    if actual_node in s.mapping:
      # The node.func field corresponds to a member of this class
      obj = s.mapping[ actual_node ][ 0 ]

    else:
      try:
        # An object in global namespace is used
        if actual_node.id in s.globals:
          obj = s.globals[ actual_node.id ]

        # An object in closure is used
        elif actual_node.id in s.closure:
          obj = s.closure[ actual_node.id ]

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

    # Now that we have the live Python object, there are a few cases that
    # we need to treat separately:
    # 1. Instantiation: Bits16( 10 ) where obj is an instance of Bits
    # Bits16( 1+2 ), Bits16( s.STATE_A )?
    # 2. Real function call: not supported yet

    # Deal with Bits instantiation
    if obj.__name__.startswith( 'Bits' ) and obj.__name__[4:].isdigit():
      nbits = obj.nbits

      if len( node.args ) != 1:
        raise PyMTLSyntaxError(
          s.blk, node, 'exactly 1 argument should be given to Bits!'
        )

      if nbits <= 0:
        raise PyMTLSyntaxError(
          s.blk, node, 'bit width should be positive integers!'
        )

      value = s.visit( node.args[0] )

      ret = Bitwidth( nbits, value )
      ret.ast = node

      return ret

    else:
      # Only Bits class instantiation is supported
      raise PyMTLSyntaxError(
        s.blk, node, 'Expecting Bits object but found ' + obj.__name__
      )

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):
    ret = Attribute( s.visit( node.value ), node.attr )
    ret.ast = node
    return ret

  #-----------------------------------------------------------------------
  # visit_Subscript
  #-----------------------------------------------------------------------

  def visit_Subscript( s, node ):
    value = s.visit( node.value )
    if isinstance( node.slice, ast.Slice ):
      if not node.slice.step is None:
        raise PyMTLSyntaxError(
          s.blk, node, 'Slice with steps is not supported!'
        )

      lower, upper = s.visit( node.slice )

      ret = Slice( value, lower, upper )
      ret.ast = node

      return ret

    if isinstance( node.slice, ast.Index ):
      idx = s.visit( node.slice )

      ret = Index( value, idx )
      ret.ast = node

      return ret

    raise PyMTLSyntaxError(
      s.blk, node, 'Illegal subscript ' + node + ' encountered!'
    )

  #-----------------------------------------------------------------------
  # visit_Slice
  #-----------------------------------------------------------------------

  def visit_Slice( s, node ):
    return ( s.visit( node.lower ), s.visit( node.upper ) )

  #-----------------------------------------------------------------------
  # visit_Index
  #-----------------------------------------------------------------------

  def visit_Index( s, node ):
    return s.visit( node.value )

  #-----------------------------------------------------------------------
  # visit_Name
  #-----------------------------------------------------------------------

  def visit_Name( s, node ):
    if node.id in s.globals:
      # free var from global name space
      # return node.id
      return FreeVar( node.id, s.globals[ node.id ] )

    elif node.id in s.closure:
      # free var from closure
      obj = s.closure[ node.id ]
      if isinstance( obj, RTLComponent ):
        ret = Base( obj )
      else:
        ret = FreeVar( node.id, obj )

    else:
      # Temporary variable
      # This can be a LoopVar or a true temporary variable
      if node.id in s.loop_var_env:
        ret = LoopVar( node.id )

      # Else this is a temporary variable but not a loop index

      elif node.id in s.tmp_var_env:
        # This temporaray variable has been registered
        ret = TmpVar( node.id )

      elif isinstance( node.ctx, ast.Load ):
        # Trying to load an unregistered temporaray variable
        raise PyMTLSyntaxError(
          s.blk, node, 'tmpvar ' + node.id + ' used before assignment!'
        )

      else:
        # This is the first time we see this tmp var
        s.tmp_var_env.add( node.id )

    ret.ast = node
    return ret

  #-----------------------------------------------------------------------
  # visit_Num
  #-----------------------------------------------------------------------

  def visit_Num( s, node ):
    ret = Number( node.n )
    ret.ast = node
    return ret

  #---------------------------------------------------------------------
  # TODO: Support some other AST nodes
  #---------------------------------------------------------------------

  # $display
  def visit_Print( s, node ):
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

