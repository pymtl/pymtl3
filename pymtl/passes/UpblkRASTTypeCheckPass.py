#========================================================================
# UpblkRASTTypeCheckPass.py
#========================================================================
# Perform type checking on an existing RAST.
#
# Author : Peitian Pan
# Date   : Jan 6, 2019

import RAST
import RASTTypeSystem

from pymtl    import *
from BasePass import BasePass
from errors   import PyMTLTypeError

class UpblkRASTTypeCheckPass( BasePass ):
  def __init__( s, type_env ):
    s.type_env = type_env

  def __call__( s, m ):
    """perform type checking on all RASTs in m._rast"""

    visitor = UpblkRASTTypeCheckVisitor( m, s.type_env )

    for ( blk, ast ) in m.get_update_block_ast_pairs():
      visitor.enter( blk, m._rast[ blk ] )

#-----------------------------------------------------------------------
# Visitor that performs type checking on RAST
#-----------------------------------------------------------------------

class UpblkRASTTypeCheckVisitor( RAST.RASTNodeVisitor ):

  def __init__( s, component, type_env ):
    s.component = component
    s.type_env = type_env

  def enter( s, blk, rast ):
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

    s.visit( rast )

  #---------------------------------------------------------------------
  # Valid RAST nodes
  #---------------------------------------------------------------------
  def visit_CombUpblk( s, node ):
    for stmt in node.body:
      s.visit( stmt )

    node.Type = None

  def visit_Assign( s, node ):
    for target in node.targets:
      s.visit( target )
    s.visit( node.value )
    
    # RHS should have the same type as LHS
    rhs_type = node.value.Type
    lhs_type_list = [ target.Type for target in node.targets ]

    if node.value.Type.nbits != 0:
      if not reduce( lambda x, y: x and ( y == rhs_type ), lhs_type_list, True ):
        raise PyMTLTypeError(
          s.blk, node.ast, 'rhs and lhs of assignment should have the same type!'
        )

    node.Type = None

  def visit_Module( s, node ):
    # Mark this node as having type module and find out its corresponding object
    node.Type = RASTTypeSystem.module( node.module )

  def visit_Const( s, node ):
    node.Type = RASTTypeSystem.constant( node.nbits )

  def visit_BinOp( s, node ):
    s.visit( node.left )
    s.visit( node.right )
    op = node.op

    # check whether both sides have agreeable types
    if ( not isinstance( node.left.Type, \
        ( RASTTypeSystem.signal, RASTTypeSystem.constant ) ) ) or \
       ( not isinstance( node.right.Type, \
        ( RASTTypeSystem.signal, RASTTypeSystem.constant ) ) ):
      raise PyMTLTypeError(
        s.blk, node.ast, 'rhs and lhs of BinOp must be signal or constant!'
      )

    l_nbits = node.left.Type.nbits
    r_nbits = node.right.Type.nbits

    if isinstance(op, (RAST.Add,RAST.Sub,RAST.BitAnd,RAST.BitOr,RAST.BitXor)):
      if l_nbits != 0 and r_nbits != 0 and l_nbits != r_nbits:
        raise PyMTLTypeError(
          s.blk, node.ast, 'rhs and lhs of BinOp must have the same nbits!'
        )
      if isinstance( node.left.Type, RASTTypeSystem.constant ) and \
          isinstance( node.right.Type, RASTTypeSystem.constant ):
        node.Type = RASTTypeSystem.constant( l_nbits )
      else:
        node.Type = RASTTypeSystem.signal( l_nbits )

    elif isinstance( op, ( RAST.ShiftLeft, RAST.ShiftRightLogic ) ):
      if not isinstance( node.right.Type, RASTTypeSystem.constant ):
        raise PyMTLTypeError(
          s.blk, node.ast, 'rhs of shift opertions must be constant!'
        )
      node.Type = node.left.Type

    # Operators have None type
    node.op.Type = None

  def visit_Attribute( s, node ):
    s.visit( node.value )

    if not isinstance( node.value.Type, RASTTypeSystem.module ):
      raise PyMTLTypeError(
        s.blk, node.ast, 'the base of an attribute must be a module!'
      )

    # Make sure node.value has an attribute of attr
    if not node.attr in node.value.Type.module.__dict__:
      raise PyMTLTypeError(
        s.blk, node.ast, 'class {base} does not have attribute {attr}!'.\
        format( base = node.value.Type.module.__class__.__name__,
                attr = node.attr
        )
      )

    # value.attr has the type that is specified in the type environment
    attr_obj = node.value.Type.module.__dict__[ node.attr ]
    node.Type = s.type_env[ freeze( attr_obj ) ]

  def visit_Index( s, node ):
    s.visit( node.value )
    s.visit( node.idx )

    # must perform indexing on an array
    if not isinstance( node.value.Type, RASTTypeSystem.array ):
      raise PyMTLTypeError(
        s.blk, node.ast, 'the base of an index must be an array!'
      )

    # index must be a constant integer
    if not isinstance( node.idx.Type, RASTTypeSystem.constant ):
      raise PyMTLTypeError(
        s.blk, node.ast, 'index must be a constant integer!'
      )

    # The result type should be array.Type
    node.Type = node.value.Type.Type

  def visit_Slice( s, node ):
    s.visit( node.value )
    s.visit( node.lower )
    s.visit( node.upper )

    # Slicing should only be performed on signals
    if not isinstance( node.value.Type, RASTTypeSystem.signal ):
      raise PyMTLTypeError(
        s.blk, node.ast, 'the base of a slice must be a signal!'
      )

    # both upper and lower bounds must be constants
    if not isinstance( node.lower.Type, RASTTypeSystem.constant ) or\
        not isinstance( node.upper.Type, RASTTypeSystem.constant ):
      raise PyMTLTypeError(
        s.blk, node.ast, 'upper and lower of a slice must be a constatnt!'
      )

    # 0 means an unset bitwidth because currently the value of the constant is
    # not inferred
    node.Type = RASTTypeSystem.signal( 0 )

#-----------------------------------------------------------------------
# Helper functions
#-----------------------------------------------------------------------

def freeze( obj ):
  """Freeze a potentially mutable object recursively."""
  if isinstance( obj, list ):
    return tuple( freeze( o ) for o in obj )
  return obj
