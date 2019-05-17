#=========================================================================
# BehavioralRTLIRGenL1Pass.py
#=========================================================================
# Author : Peitian Pan
# Date   : Oct 20, 2018
"""Provide L1 behavioral RTLIR generation pass."""
from __future__ import absolute_import, division, print_function

import ast
import copy

# from pymtl import *
import pymtl
from pymtl.passes import BasePass
from pymtl.passes.BasePass import PassMetadata

from .BehavioralRTLIR import *
from .errors import PyMTLSyntaxError


class BehavioralRTLIRGenL1Pass( BasePass ):
  def __call__( s, m ):
    """Generate RTLIR for all upblks of m."""
    if not hasattr( m, '_pass_behavioral_rtlir_gen' ):
      m._pass_behavioral_rtlir_gen = PassMetadata()

    m._pass_behavioral_rtlir_gen.rtlir_upblks = {}
    visitor = BehavioralRTLIRGeneratorL1( m )
    upblks = {
      'CombUpblk' : m.get_update_blocks() - m.get_update_on_edge(),
      'SeqUpblk'  : m.get_update_on_edge()
    }

    for upblk_type in ( 'CombUpblk', 'SeqUpblk' ):
      for blk in upblks[ upblk_type ]:
        visitor._upblk_type = upblk_type
        m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ] = \
          visitor.enter( blk, m.get_update_block_ast( blk ) )

class BehavioralRTLIRGeneratorL1( ast.NodeVisitor ):
  def __init__( s, component ):
    s.component = component
    s.mapping   = component.get_astnode_obj_mapping()

  def enter( s, blk, ast ):
    """Entry point of RTLIR generation."""
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

    ret = s.visit( ast )
    ret.component = s.component
    return ret

  def get_call_obj( s, node ):
    if node.starargs:
      raise PyMTLSyntaxError( s.blk, node, 'star argument is not supported!')
    if node.kwargs:
      raise PyMTLSyntaxError( s.blk, node,
        'double-star keyword argument is not supported!')
    if node.keywords:
      raise PyMTLSyntaxError( s.blk, node, 'keyword argument is not supported!')
    func = node.func

    # Find the corresponding object of node.func field
    # TODO: Support Verilog task?
    if func in s.mapping:
      # The node.func field corresponds to a member of this class
      obj = s.mapping[ func ][ 0 ]
    else:
      try:
        # An object in global namespace is used
        if func.id in s.globals:
          obj = s.globals[ func.id ]
        # An object in closure is used
        elif func.id in s.closure:
          obj = s.closure[ func.id ]
        else:
          raise NameError

      except AttributeError:
        raise PyMTLSyntaxError( s.blk, node,
          node.func + ' function call is not supported!' )
      except NameError:
        raise PyMTLSyntaxError( s.blk, node,
          node.func.id + ' function is not found!' )
    return obj

  def visit_Module( s, node ):
    if len( node.body ) != 1 or \
        not isinstance( node.body[0], ast.FunctionDef ):
      raise PyMTLSyntaxError( s.blk, node,
        'Update blocks should have exactly one FuncDef!' )
    ret = s.visit( node.body[0] )
    ret.ast = node
    return ret

  def visit_FunctionDef( s, node ):
    """Return the behavioral RTLIR of function node.

    We do not need to check the decorator list -- the fact that we are
    visiting this node ensures this node was added to the upblk
    dictionary through s.update() (or other PyMTL decorators) earlier!
    """
    # Check the arguments of the function
    if node.args.args or node.args.vararg or node.args.kwarg:
      raise PyMTLSyntaxError( s.blk, node,
        'Update blocks should not have arguments!' )

    # Get the type of upblk from ._upblk_type variable
    ret = eval( s._upblk_type + '( node.name, [] )' )
    for stmt in node.body:
      ret.body.append( s.visit( stmt ) )
    ret.ast = node
    return ret

  def visit_Assign( s, node ):
    if len( node.targets ) != 1:
      raise PyMTLSyntaxError( s.blk, node,
        'Assigning to multiple targets is not allowed!' )

    value = s.visit( node.value )
    target = s.visit( node.targets[0] )
    ret = Assign( target, value )
    ret.ast = node
    return ret

  def visit_Call( s, node ):
    """Return the behavioral RTLIR of method calls.
    
    Some data types are interpreted as function calls in the Python AST.
    Example: Bits4(2)
    These are converted to different RTLIR nodes in different contexts.
    """

    obj = s.get_call_obj( node )
    if ( obj == copy.copy ) or ( obj == copy.deepcopy ):
      assert len( node.args ) == 1, \
        'copy method {} takes exactly 1 argument!'.format( obj )
      ret = s.visit( node.args[0] )
      ret.ast = node
      return ret

    # Now that we have the live Python object, there are a few cases that
    # we need to treat separately:
    # 1. Instantiation: Bits16( 10 ) where obj is an instance of Bits
    # Bits16( 1+2 ), Bits16( s.STATE_A )?
    # 2. concat()
    # 3. zext(), sext()
    # TODO: support the following
    # 4. reduce_and(), reduce_or(), reduce_xor()
    # 5. Real function call: not supported yet

    # Deal with Bits type cast
    if issubclass( obj, pymtl.Bits ):
      nbits = obj.nbits
      if (len( node.args ) != 1) or (node.keywords):
        raise PyMTLSyntaxError( s.blk, node,
          'exactly 1 non-keyword argument should be given to Bits!' )
      if nbits <= 0:
        raise PyMTLSyntaxError( s.blk, node,
          'bit width should be positive integers!' )
      value = s.visit( node.args[0] )
      if not isinstance( value, Number ):
        ret = value
        ret.ast = node
        return ret
      ret = SizeCast( nbits, value )
      ret.ast = node
      return ret

    # concat method
    elif obj is pymtl.concat:
      if (len( node.args ) < 1) or (node.keywords):
        raise PyMTLSyntaxError( s.blk, node,
          'at least 1 non-keyword argument should be given to concat!' )
      values = map( lambda c: s.visit(c), node.args )
      ret = Concat( values )
      ret.ast = node
      return ret

    # zext method
    elif obj is pymtl.zext:
      if (len( node.args ) != 1) or (node.keywords):
        raise PyMTLSyntaxError( s.blk, node,
          'exactly 1 non-keyword argument should be given to zext!' )
      nbits = s.visit( node.args[1] )
      value = s.visit( node.args[0] )
      ret = ZeroExt( nbits, value )
      ret.ast = node
      return ret

    # sext method
    elif obj is pymtl.sext:
      if (len( node.args ) != 1) or (node.keywords):
        raise PyMTLSyntaxError( s.blk, node,
          'exactly 1 non-keyword argument should be given to sext!' )
      nbits = s.visit( node.args[1] )
      value = s.visit( node.args[0] )
      ret = SignExt( nbits, value )
      ret.ast = node
      return ret

    else:
      # Only Bits class instantiation is supported at L1
      raise PyMTLSyntaxError( s.blk, node,
        'Expecting Bits object but found ' + obj.__name__ )

  def visit_Attribute( s, node ):
    ret = Attribute( s.visit( node.value ), node.attr )
    ret.ast = node
    return ret

  def visit_Subscript( s, node ):
    value = s.visit( node.value )
    if isinstance( node.slice, ast.Slice ):
      if not node.slice.step is None:
        raise PyMTLSyntaxError( s.blk, node,
          'Slice with steps is not supported!' )
      lower, upper = s.visit( node.slice )
      ret = Slice( value, lower, upper )
      ret.ast = node
      return ret

    if isinstance( node.slice, ast.Index ):
      idx = s.visit( node.slice )
      ret = Index( value, idx )
      ret.ast = node
      return ret

    raise PyMTLSyntaxError( s.blk, node,
      'Illegal subscript ' + node + ' encountered!' )

  def visit_Slice( s, node ):
    return ( s.visit( node.lower ), s.visit( node.upper ) )

  def visit_Index( s, node ):
    return s.visit( node.value )

  def visit_Name( s, node ):
    if node.id in s.globals:
      # free var from the global name space
      ret = FreeVar( node.id, s.globals[ node.id ] )
      ret.ast = node
      return ret
    elif node.id in s.closure:
      # free var from closure
      obj = s.closure[ node.id ]
      if isinstance( obj, pymtl.Component ):
        # Component freevars are an L1 thing.
        assert obj is s.component, \
            "Component {} is not a sub-component of {}!".format(obj, s.component)
        ret = Base( obj )
      else:
        ret =  FreeVar( node.id, obj )
      ret.ast = node
      return ret
    assert False, 'Temporary variables are not supported at L1!'

  def visit_Num( s, node ):
    ret = Number( node.n )
    ret.ast = node
    return ret

  def visit_AugAssign( s, node ):  raise NotImplementedError()

  def visit_If( s, node ): raise NotImplementedError()

  def visit_For( s, node ): raise NotImplementedError()

  def visit_BoolOp( s, node ): raise NotImplementedError()

  def visit_BinOp( s, node ): raise NotImplementedError()

  def visit_UnaryOp( s, node ): raise NotImplementedError()

  def visit_IfExp( s, node ): raise NotImplementedError()

  def visit_Compare( s, node ): raise NotImplementedError()

  # $display
  def visit_Print( s, node ): raise NotImplementedError()

  # function
  def visit_Return( s, node ): raise NotImplementedError()

  # SV assertion
  def visit_Assert( s, node ): raise NotImplementedError()

  def visit_Expr( s, node ):
    """Return the behavioral RTLIR of an expression.
    
    ast.Expr might be useful when a statement is only a call to a task or 
    a non-returning function.
    """
    raise PyMTLSyntaxError(
      s.blk, node, 'Task is not supported yet!'
    )

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
