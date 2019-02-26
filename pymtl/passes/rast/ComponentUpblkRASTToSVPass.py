#=========================================================================
# ComponentUpblkRASTToSVPass.py
#=========================================================================
# Translate RAST of all upblks in a component to SystemVerilog.
#
# Author : Peitian Pan
# Date   : Jan 23, 2019

from pymtl                import *
from pymtl.passes         import BasePass, PassMetadata
from pymtl.passes.Helpers import freeze, make_indent

from RAST                 import *
from RASTType             import *

class ComponentUpblkRASTToSVPass( BasePass ):
  def __call__( s, m ):
    """Translate all upblk in m to a list of strings."""

    m._pass_component_upblk_rast_to_sv = PassMetadata()

    m._pass_component_upblk_rast_to_sv.sv = {}

    visitor = UpblkRASTToSVVisitor( m )

    for blk in m.get_update_blocks():
      m._pass_component_upblk_rast_to_sv.sv[ blk ] =\
        visitor.enter( blk, m._pass_component_upblk_rast_gen.rast[ blk ] )

#-------------------------------------------------------------------------
# UpblkRASTToSVVisitor
#-------------------------------------------------------------------------
# Visitor that translates RAST to SystemVerilog for a single upblk.

class UpblkRASTToSVVisitor( RASTNodeVisitor ):

  def __init__( s, component ):
    s.component = component

    # Should use enum here, but enum is a python 3 feature...
    s.NONE          = 0
    s.COMBINATIONAL = 1
    s.SEQUENTIAL    = 2
    s.upblk_type    = s.NONE

    # The dictionary of operator-character pairs
    s.ops = {
      # Unary operators
      Invert : '~', Not : '!', UAdd : '+', USub : '-',
      # Boolean operators
      And : '&&', Or : '||',
      # Binary operators
      Add : '+', Sub : '-', Mult : '*', Div : '/', Mod : '%', Pow : '**',
      ShiftLeft : '<<', ShiftRightLogic : '>>', 
      BitAnd : '&', BitOr : '|', BitXor : '^',
      # Comparison operators
      Eq : '==', NotEq : '!=', Lt : '<', LtE : '<=', Gt : '>', GtE : '>='
    }

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

    # import pdb
    # pdb.set_trace()

    return s.visit( rast )

  def visit_expr_wrap( s, node ):
    """ Helper function that selectively wraps expressions with brackets """
    if isinstance( node, ( IfExp, UnaryOp, BoolOp, BinOp, Compare ) ):
      return '({})'.format( s.visit( node ) )

    else:
      return s.visit( node )

  #-----------------------------------------------------------------------
  # visit_CombUpblk
  #-----------------------------------------------------------------------
  # CombUpblk concatenates string representation of statements inside it
  # and return the result string.

  def visit_CombUpblk( s, node ):
    blk_name = node.name
    src      = []
    body     = []

    s.upblk_type = s.COMBINATIONAL

    # Add name of the upblk to this always block
    src.extend( [ 'always_comb begin : {blk_name}'.format(
      blk_name = blk_name
    ) ] )
    
    for stmt in node.body:
      body.extend( s.visit( stmt ) )

    make_indent( body, 1 )
    src.extend( body )

    src.extend( [ 'end' ] )

    s.upblk_type = s.NONE

    return src

  #-----------------------------------------------------------------------
  # visit_SeqUpblk
  #-----------------------------------------------------------------------
  # SeqUpblk concatenates string representation of statements inside it
  # and return the result string.

  def visit_SeqUpblk( s, node ):
    blk_name = node.name
    src      = []
    body     = []

    s.upblk_type = s.SEQUENTIAL

    # Add name of the upblk to this always block
    src.extend( [ 'always_ff @(posedge clk) begin : {blk_name}'.format(
      blk_name = blk_name
    ) ] )
    
    for stmt in node.body:
      body.extend( s.visit( stmt ) )

    make_indent( body, 1 )
    src.extend( body )

    src.extend( [ 'end' ] )

    s.upblk_type = s.NONE

    return src

  #-----------------------------------------------------------------------
  # Statements
  #-----------------------------------------------------------------------
  # All statement nodes return a list of strings.

  #-----------------------------------------------------------------------
  # visit_Assign
  #-----------------------------------------------------------------------

  def visit_Assign( s, node ):
    target        = s.visit( node.target )
    value         = s.visit( node.value )
    assignment_op = '<=' if s.upblk_type == s.SEQUENTIAL else '='

    ret = '{target} {op} {value};'.format(
      target = target, op = assignment_op, value = value 
    )

    return [ ret ]

  #-----------------------------------------------------------------------
  # visit_AugAssign
  #-----------------------------------------------------------------------

  def visit_AugAssign( s, node ):
    # SystemVerilog supports augmented assignment syntax.
    target        = s.visit( node.target )
    value         = s.visit( node.value )
    assignment_op = s.ops[ type( node.op ) ] + '='

    ret = '{target} {op} {value};'.format(
      target = target, op = assignment_op, value = value 
    )

    return [ ret ]

  #-----------------------------------------------------------------------
  # visit_If
  #-----------------------------------------------------------------------

  def visit_If( s, node ):
    src    = []
    body   = []
    orelse = []

    # Grab condition, if-body, and orelse-body

    cond = s.visit( node.cond )

    for stmt in node.body:
      body.extend( s.visit( stmt ) )

    make_indent( body, 1 )

    for stmt in node.orelse:
      orelse.extend( s.visit( stmt ) )

    # Assemble the statement, starting with if-body

    if_begin   = 'if ({})'.format(cond) + (' begin' if len(node.body) > 1 else '')

    src.extend( [ if_begin ] )
    src.extend( body )
    
    if len( node.body ) > 1:
      src.extend( [ 'end' ] )

    # If orelse-body is not empty, add it to the list of strings

    if node.orelse != []:

      # If an if statement is the only statement in the orelse-body
      if len( node.orelse ) == 1 and isinstance( node.orelse[ 0 ], If ):
        # No indent will be added, also append if-begin to else-begin
        else_begin = 'else ' + orelse[ 0 ]
        orelse = orelse[ 1 : ]

      # Else indent orelse-body
      else:
        else_begin = 'else' + ( ' begin' if len( node.orelse ) > 1 else '' )
        make_indent( orelse, 1 )

      src.extend( [ else_begin ] )
      src.extend( orelse )

      if len( node.orelse ) > 1:
        src.extend( [ 'end' ] )

    return src

  #-----------------------------------------------------------------------
  # visit_For
  #-----------------------------------------------------------------------

  def visit_For( s, node ):
    src      = []
    body     = []
    loop_var = s.visit( node.var )
    start    = s.visit( node.start )
    end      = s.visit( node.end )

    begin    = ' begin' if len( node.body ) > 1 else ''

    cmp_op   = '<' if node.step.value > 0 else '<'
    inc_op   = '+' if node.step.value > 0 else '-'

    step_abs = s.visit( node.step )
    step_abs = step_abs if node.step.value > 0 else step_abs[ 1 : ]

    for stmt in node.body:
      body.extend( s.visit( stmt ) )

    make_indent( body, 1 )

    for_begin =\
      'for ( int {v} = {s}; {v} {comp} {t}; {v} {inc}= {stp} ){begin}'.format(
      v = loop_var, s = start, t = end, stp = step_abs,
      comp = cmp_op, inc = inc_op, begin = begin
    )

    # Assemble for statement

    src.extend( [ for_begin ] )
    src.extend( body )

    if len( node.body ) > 1:
      src.extend( [ 'end' ] )

    return src

  #-----------------------------------------------------------------------
  # Expressions
  #-----------------------------------------------------------------------
  # All expression nodes return a single string.  

  #-----------------------------------------------------------------------
  # visit_Number
  #-----------------------------------------------------------------------

  def visit_Number( s, node ):
    # Create a number without width specifier
    return str( node.value )

  #-----------------------------------------------------------------------
  # visit_Bitwidth
  #-----------------------------------------------------------------------

  def visit_Bitwidth( s, node ):
    if isinstance( node.value, Number ):
      return "{}'d{}".format( node.nbits, node.value.value )
    else:
      return s.visit( node.value )

  #-----------------------------------------------------------------------
  # visit_IfExp
  #-----------------------------------------------------------------------

  def visit_IfExp( s, node ):
    cond  = s.visit_expr_wrap( node.cond )
    true  = s.visit( node.body )
    false = s.visit( node.orelse )

    return '( {cond} ) ? {true} : {false}'.format(
      cond = cond, true = true, false = false
    )

  #-----------------------------------------------------------------------
  # visit_UnaryOp
  #-----------------------------------------------------------------------

  def visit_UnaryOp( s, node ):
    op      = s.ops[ type( node.op ) ]
    operand = s.visit_expr_wrap( node.operand )

    return '{op}{operand}'.format( op = op, operand = operand )

  #-----------------------------------------------------------------------
  # visit_BoolOp
  #-----------------------------------------------------------------------

  def visit_BoolOp( s, node ):
    op     = s.ops[ type( node.op ) ]
    values = []

    for value in node.values:
      values.append( s.visit_expr_wrap( value ) )

    src = ( ' {op} '.format( op = op ) ).join( values )

    return src

  #-----------------------------------------------------------------------
  # visit_BinOp
  #-----------------------------------------------------------------------

  def visit_BinOp( s, node ):
    op  = s.ops[ type( node.op ) ]
    lhs = s.visit_expr_wrap( node.left )
    rhs = s.visit_expr_wrap( node.right )

    return '{lhs}{op}{rhs}'.format( lhs = lhs, op = op, rhs = rhs )

  #-----------------------------------------------------------------------
  # visit_Compare
  #-----------------------------------------------------------------------

  def visit_Compare( s, node ):
    op  = s.ops[ type( node.op ) ]
    lhs = s.visit_expr_wrap( node.left )
    rhs = s.visit_expr_wrap( node.right )

    return '( {lhs} {op} {rhs} )'.format( lhs = lhs, op = op, rhs = rhs )

  #-----------------------------------------------------------------------
  # visit_Attribute
  #-----------------------------------------------------------------------

  def visit_Attribute( s, node ):
    # import pdb
    # pdb.set_trace()

    attr  = node.attr
    value = s.visit( node.value )

    if isinstance( node.value, Base ) and node.value.base is s.component:
      # The base of this attribute node is the component 's'.
      # Example: s.out, s.STATE_IDLE
      ret = attr

    elif isinstance( node.value.Type, Module ):
      # Reference to submodule's port
      # Example: s.b.in_
      # In SystemVerilog you (obviously) cannot refer to the port through
      # attribute without using interface. Instead this should generate
      # the name of the wire that connects to that port.
      ret = '{value}${attr}'.format( value = value, attr = attr )

    else:
      # Hierarchical reference to a field of struct
      ret = '{value}.{attr}'.format( value = value, attr = attr )

    return ret

  #-----------------------------------------------------------------------
  # visit_Index
  #-----------------------------------------------------------------------

  def visit_Index( s, node ):
    idx   = s.visit( node.idx )
    value = s.visit( node.value )

    return '{value}[{idx}]'.format( value = value, idx = idx )

  #-----------------------------------------------------------------------
  # visit_Slice
  #-----------------------------------------------------------------------

  def visit_Slice( s, node ):
    lower = s.visit( node.lower )
    upper = s.visit( node.upper )
    value = s.visit( node.value )

    return '{val}[{y}-1:{x}]'.format( val = value, x = lower, y = upper )

  #-----------------------------------------------------------------------
  # visit_Base
  #-----------------------------------------------------------------------

  def visit_Base( s, node ):
    return str( node.base )

  #-----------------------------------------------------------------------
  # visit_LoopVar
  #-----------------------------------------------------------------------

  def visit_LoopVar( s, node ):
    return node.name

  #-----------------------------------------------------------------------
  # visit_FreeVar
  #-----------------------------------------------------------------------

  def visit_FreeVar( s, node ):
    return node.name

  #-----------------------------------------------------------------------
  # visit_TmpVar
  #-----------------------------------------------------------------------

  def visit_TmpVar( s, node ):
    return node.name

  #-----------------------------------------------------------------------
  # Declarations
  #-----------------------------------------------------------------------

  #-----------------------------------------------------------------------
  # visit_LoopVarDecl
  #-----------------------------------------------------------------------

  def visit_LoopVarDecl( s, node ):
    return node.name
