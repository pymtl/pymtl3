#=========================================================================
# ComponentUpblkRASTTypeCheckPass.py
#=========================================================================
# Perform type checking on all blocks' RAST for a given component. This
# pass does not have a namespace to write to because it only throws an
# exception when a type error is detected.
#
# Author : Peitian Pan
# Date   : Jan 6, 2019

from pymtl                             import *
from pymtl.passes                      import BasePass
from pymtl.passes.utility.pass_utility import freeze

from errors                            import PyMTLTypeError
from RAST                              import *
from RASTType                          import *

class ComponentUpblkRASTTypeCheckPass( BasePass ):
  def __init__( s, type_env ):
    s.type_env = type_env

  def __call__( s, m ):
    """perform type checking on all RAST in _rast"""

    visitor = UpblkRASTTypeCheckVisitor( m, s.type_env )

    for blk in m.get_update_blocks():

      visitor.enter( blk, m._pass_component_upblk_rast_gen.rast[ blk ] )

    return visitor.tmp_var_type_env

#-------------------------------------------------------------------------
# UpblkRASTTypeCheckVisitor
#-------------------------------------------------------------------------
# Visitor that performs type checking on RAST

class UpblkRASTTypeCheckVisitor( RASTNodeVisitor ):

  def __init__( s, component, type_env ):
    s.component = component

    s.type_env = type_env

    s.tmp_var_type_env = {}

    s.BinOp_max_nbits = ( Add, Sub, Mult, Div, Mod, Pow, BitAnd, BitOr,
        BitXor )

    s.BinOp_left_nbits = ( ShiftLeft, ShiftRightLogic )

    #---------------------------------------------------------------------
    # The expected evaluation result types for each type of RAST node
    #---------------------------------------------------------------------

    s.type_expect = {}

    lhs_types = ( Signal, Array, NoneType )

    s.type_expect[ 'Assign' ] = {
      'target' : ( lhs_types, 'lhs of assignment must be signal/array!' ),
      'value' : ( (Const,Signal), 'rhs of assignment should be signal/const!' )
    }
    s.type_expect[ 'AugAssign' ] = {
      'target' : ( lhs_types, 'lhs of assignment must be signal/array!' ),
      'value' : ( (Const,Signal), 'rhs of assignment should be signal/const!' )
    }
    s.type_expect[ 'BinOp' ] = {
      'left' : ( (Const,Signal), 'lhs of binop should be signal/const!' ),
      'right' : ( (Const,Signal), 'rhs of binop should be signal/const!' ),
    }
    s.type_expect[ 'For' ] = {
      'start' : ( Const, 'the start of a for-loop must be a constant expression!' ),
      'end':( Const, 'the end of a for-loop must be a constant expression!' ),
      'step':( Const, 'the step of a for-loop must be a constant expression!' )
    }
    s.type_expect[ 'Attribute' ] = {
      'value':( (Module, Struct, Interface),
        'the base of an attribute must be one of: module, struct, interface!' )
    }
    s.type_expect[ 'Index' ] = {
      'value':( Array, 'the base of an index must be an array!' ),
      'idx':( (Const, Signal), 'index must be a constant expression or a signal!' )
    }
    s.type_expect[ 'Slice' ] = {
      'value':( Signal, 'the base of a slice must be a signal!' ),
      'lower':( Const, 'upper of slice must be a constant expression!' ),
      'upper':( Const, 'lower of slice must be a constant expression!' )
    }

  #-----------------------------------------------------------------------
  # eval_const_binop
  #-----------------------------------------------------------------------

  def eval_const_binop( s, l, op, r ):
    """Evaluate ( l op r ) and return the result as an integer."""
    assert type( l ) == int and type( r ) == int

    op_dict = {
      Add       : '+',  Sub   : '-',  Mult : '*',  Div  : '/',
      Mod       : '%',  Pow   : '**',
      ShiftLeft : '<<', ShiftRightLogic : '>>',
      BitAnd    : '&',  BitOr : '|',  BitXor : '^',
    }

    return eval( '{l}{op}{r}'.format( l = l, op = op_dict[ type(op) ], r = r ) )

  def enter( s, blk, rast ):
    """ entry point for RAST type checking """
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

    # import pdb
    # pdb.set_trace()

    s.visit( rast )

  # Override the default visit()
  def visit( s, node ):
    node_name = node.__class__.__name__
    method = 'visit_' + node_name
    func = getattr( s, method, s.generic_visit )

    # First visit (type check) all child nodes
    for field in node.__dict__.keys():
      value = node.__dict__[ field ]
      if isinstance( value, list ):
        for item in value:
          if isinstance( item, BaseRAST ):
            s.visit( item )
      elif isinstance( value, BaseRAST ):
        s.visit( value )

    # Then verify that all child nodes have desired types
    try:
      # Check the expected types of child nodes
      for field, type_rule in s.type_expect[node_name].iteritems():
        value = node.__dict__[ field ]
        target_type = type_rule[ 0 ]
        exception_msg = type_rule[ 1 ]

        if eval( 'not isinstance( value.Type, target_type )' ):
          raise PyMTLTypeError( s.blk, node, exception_msg )

    except PyMTLTypeError:
      raise
    except:
      # This node does not require type checking on child nodes
      pass

    # Finally call the type check function
    func( node )

  # Override the default generic_visit()
  def generic_visit( s, node ):
    node.Type = None

  #-----------------------------------------------------------------------
  # visit_Assign
  #-----------------------------------------------------------------------

  def visit_Assign( s, node ):
    # RHS should have the same type as LHS
    rhs_type = node.value.Type
    lhs_type = node.target.Type

    if isinstance( node.target, TmpVar ):
      # Creating a temporaray variable
      node.target.Type = rhs_type
      s.tmp_var_type_env[ node.target.name ] = rhs_type

    else:
      if not lhs_type( rhs_type ):
        raise PyMTLTypeError(
          s.blk, node.ast, 'Unagreeable types between assignment LHS and RHS!'
        )

    node.Type = None

  #-----------------------------------------------------------------------
  # visit_AugAssign
  #-----------------------------------------------------------------------

  def visit_AugAssign( s, node ):
    target = node.target
    op = node.op
    value = node.value
    
    # perform type check as if this node corresponds to
    # target = target op value

    l_nbits = target.Type.nbits
    r_nbits = value.Type.nbits

    node.Type = None

  #-----------------------------------------------------------------------
  # visit_If
  #-----------------------------------------------------------------------

  def visit_If( s, node ):
    # Can the type of condition be cast into bool?
    if not Bool()( node.cond.Type ):
      raise PyMTLTypeError(
        s.blk, node.ast, 'the condition of "if" cannot be converted to bool!'
      )

    node.Type = None

  #-----------------------------------------------------------------------
  # visit_For
  #-----------------------------------------------------------------------

  def visit_For( s, node ):
    if isinstance( node.step.Type, Const ) and node.step.Type.is_static:
      if node.step.Type.value == 0:
        raise PyMTLTypeError(
          s.blk, node.ast, 'the step of for-loop cannot be zero!'
        )

    node.Type = None

  #-----------------------------------------------------------------------
  # visit_Base
  #-----------------------------------------------------------------------

  def visit_Base( s, node ):
    # Mark this node as having type module
    node.Type = Module( node.base, s.type_env[freeze( node.base )].type_env )

  #-----------------------------------------------------------------------
  # visit_Number
  #-----------------------------------------------------------------------

  def visit_Number( s, node ):
    # By default, number literals have bitwidth of 32
    node.Type = Const( True, 32, node.value )

  #-----------------------------------------------------------------------
  # visit_Bitwidth
  #-----------------------------------------------------------------------

  def visit_Bitwidth( s, node ):
    nbits = node.nbits
    Type = node.value.Type

    # We do not check for bitwidth mismatch here because the user should
    # be able to *explicitly* convert signals/constatns to different bitwidth.

    if not isinstance( Type, ( Signal, Const ) ):
      # Array, Bool, Module cannot have bitwidth
      raise PyMTLTypeError(
        s.blk, node.ast, 'bitwidth does not apply to' + str(Type) + '!'
      )

    if isinstance( Type, Signal ):
      node.Type = Signal( nbits )

    elif isinstance( Type, Const ):
      node.Type = Const( Type.is_static, nbits, Type.value )

  #-----------------------------------------------------------------------
  # visit_LoopVar
  #-----------------------------------------------------------------------

  def visit_LoopVar( s, node ):
    node.Type = Const( False, 32 )

  #-----------------------------------------------------------------------
  # visit_FreeVar
  #-----------------------------------------------------------------------

  def visit_FreeVar( s, node ):
    node.Type = get_type( node.obj )

  #-----------------------------------------------------------------------
  # visit_TmpVar
  #-----------------------------------------------------------------------

  def visit_TmpVar( s, node ):
    if not node.name in s.tmp_var_type_env:
      # This tmpvar is being created. Later when it is used, its type can
      # be read from tmp_var_type_env.
      node.Type = NoneType()

    else:
      node.Type = s.tmp_var_type_env[ node.name ]

  #-----------------------------------------------------------------------
  # visit_IfExp
  #-----------------------------------------------------------------------

  def visit_IfExp( s, node ):
    # Can the type of condition be cast into bool?
    if not Bool()( node.cond.Type ):
      raise PyMTLTypeError(
        s.blk, node.ast, 'the condition of "if-exp" cannot be converted to bool!'
      )

    # body and orelse must have the same type
    if node.body.Type != node.orelse.Type:
      raise PyMTLTypeError(
        s.blk, node.ast, 'the body and orelse of "if-exp" must have the same type!'
      )

  #-----------------------------------------------------------------------
  # visit_UnaryOp
  #-----------------------------------------------------------------------

  def visit_UnaryOp( s, node ):
    if isinstance( node.op, Not ):
      if not Bool()( node.operand.Type ):
        raise PyMTLTypeError(
          s.blk, node.ast, 'the operand of "unary-expr" cannot be cast to bool!'
        )
      node.Type = Bool()

    else:
      if not isinstance( node.operand.Type, ( Signal, Const ) ):
        raise PyMTLTypeError(
          s.blk, node.ast, 'the operand of "unary-expr" is not signal or constant!'
        )
      node.Type = node.operand.Type

  #-----------------------------------------------------------------------
  # visit_BoolOp
  #-----------------------------------------------------------------------

  def visit_BoolOp( s, node ):
    for value in node.values:
      if not Bool()( value.Type ):
        raise PyMTLTypeError(
          s.blk, node.ast, value + " of '' cannot be cast into bool!"
        )

    node.Type = Bool()

  #-----------------------------------------------------------------------
  # visit_BinOp
  #-----------------------------------------------------------------------

  def visit_BinOp( s, node ):
    op = node.op

    l_type = node.left.Type
    r_type = node.right.Type
    l_nbits = node.left.Type.nbits
    r_nbits = node.right.Type.nbits

    # Enforcing Verilog bitwidth inference rules

    res_nbits = 0

    if isinstance( op, s.BinOp_max_nbits ):
      res_nbits = max( l_nbits, r_nbits )

    elif isinstance( op, s.BinOp_left_nbits ):
      res_nbits = l_nbits

    else:
      raise Exception( 'RASTTypeCheck internal error: unrecognized op!' )

    # Both sides are constant expressions
    if isinstance( l_type, Const ) and isinstance( r_type, Const ):
      # Both sides are static -> result is static
      if l_type.is_static and r_type.is_static:
        l_val = l_type.value
        r_val = r_type.value
        node.Type = Const( True, res_nbits, s.eval_const_binop( l_val, op, r_val ) )
      # Either side is dynamic -> result is dynamic
      else:
        node.Type = Const( False, res_nbits )

    # Non-constant expressions
    else:
      node.Type = Signal( res_nbits )

  #-----------------------------------------------------------------------
  # visit_Compare
  #-----------------------------------------------------------------------

  def visit_Compare( s, node ):
    node.Type = Bool()

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):
    # node.value should subclass RASTType.BaseAttr
    # Make sure node.value has an attribute named attr
    if not node.attr in node.value.Type.obj.__dict__:
      raise PyMTLTypeError(
        s.blk, node.ast, 'class {base} does not have attribute {attr}!'.\
        format( 
          base = node.value.Type.obj.__class__.__name__,
          attr = node.attr
        )
      )

    # value.attr has the type that is specified in the type environment
    attr_obj = node.value.Type.obj.__dict__[ node.attr ]
    node.Type = node.value.Type.type_env[ freeze( attr_obj ) ]

  #-----------------------------------------------------------------------
  # visit_Index
  #-----------------------------------------------------------------------

  def visit_Index( s, node ):
    if isinstance( node.idx.Type, Const ):
      # If the index is a constant expression, it is possible to do static
      # range check.
      # Check whether the index is in the range of the array
      if node.idx.Type.is_static:
        if not ( 0 <= node.idx.Type.value <= node.value.Type.length ):
          raise PyMTLTypeError(
            s.blk, node.ast, 'array index out of range!'
          )

    else:
      # This is a Signal type. No further static checking can be done
      pass

    # The result type should be array.Type
    node.Type = node.value.Type.Type

  #-----------------------------------------------------------------------
  # visit_Slice
  #-----------------------------------------------------------------------

  def visit_Slice( s, node ):
    # Check slice range only if lower and upper bounds are static
    if node.lower.Type.is_static and node.upper.Type.is_static:
      lower_val = node.lower.Type.value
      upper_val = node.upper.Type.value
      signal_nbits = node.value.Type.nbits

      # upper bound must be strictly larger than the lower bound
      if ( lower_val >= upper_val ):
        raise PyMTLTypeError(
          s.blk, node.ast,
          'the upper bound of a slice must be larger than the lower bound!'
        )

      # upper & lower bound should lie in the bit width of the signal
      if not ( 0 <= lower_val < upper_val <= signal_nbits ):
        raise PyMTLTypeError(
          s.blk, node.ast, 'upper/lower bound of slice out of width of signal!'
        )

      node.Type = Signal( upper_val - lower_val )

    else:
      node.Type = Signal( 0 )
