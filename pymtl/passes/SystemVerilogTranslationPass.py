#=========================================================================
# SystemVerilogTranslationPass.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Aug 23, 2018

from pymtl                import *
from pymtl.dsl            import ComponentLevel1
from BasePass             import BasePass
from GenDAGPass           import GenDAGPass
from SimpleSchedPass      import SimpleSchedPass
from collections          import defaultdict, deque
from errors               import TranslationError
from inspect              import getsource
import ast

vmodule_upblk_template = """
module {module_name}
(
  // Input declarations
  {input_decls}

  // Output declarations
  {output_decls}
);

  // Local wire declarations
  {wire_decls}

  // Submodule declarations
  {children_decls}

  // Assignments due to net connection and submodule interfaces
  {assignments}

  // Logic block of {module_name}
  {blk_srcs}

endmodule
"""

class SystemVerilogTranslationPass( BasePass ):

  def __call__( s, top ):
    model_name            = top.__class__.__name__
    verilog_file          = model_name + 'sv'
    systemverilog_file    = model_name + '.sv'
    c_wrapper_file        = model_name + '_v.cpp'
    py_wrapper_file       = model_name + '_v.py'
    lib_file              = 'lib{}_v.so'.format( model_name )
    obj_dir               = 'obj_dir_' + model_name

    GenDAGPass()( top )
    SimpleSchedPass()( top )

    # Get all modules in the component hierarchy and translate the 
    # deepest component first

    all_components = sorted( top.get_all_components(), key = repr )
    all_components.reverse()

    # Distribute net connections into components' assignments

    nets = top.get_all_value_nets()
    adjs = top.get_signal_adjacency_dict()

    connections_self_child    = defaultdict(set)
    connections_self_self     = defaultdict(set)
    connections_child_child   = defaultdict(set)

    for writer, net in nets:
      S = deque( [ writer ] )
      visited = set( [ writer ] )
      while S:
        u = S.pop()
        writer_host         = u.get_host_component()
        writer_host_parent  = writer_host.get_parent_object() 

        for v in adjs[u]:
          if v not in visited:
            visited.add( v )
            S.append( v )
            reader_host         = v.get_host_component()
            reader_host_parent  = reader_host.get_parent_object()

            if writer_host is reader_host:
              connections_self_self[ writer_host ].add( ( u, v ) )

            elif writer_host_parent is reader_host:
              connections_self_child[ reader_host ].add( ( u, v ) )

            elif writer_host is reader_host_parent:
              connections_self_child[ writer_host ].add( ( u, v ) )

            elif writer_host_parent == reader_host_parent:
              connections_child_child[ writer_host_parent ].add( ( u, v ) )

            else: assert False

    ret = ""
    for obj in all_components: 
      ret += s.translate_component( obj, connections_self_self[ obj ],
                                         connections_self_child[ obj ],
                                         connections_child_child[ obj ] )

    with open( systemverilog_file, 'w' ) as sv_out_file:
      sv_out_file.write( ret )

  def translate_component( s, m, connections_self_self, 
                                 connections_self_child, 
                                 connections_child_child ):
    """ translate a single update block into SystemVerilog """
    module_name = m.__class__.__name__

    #-------------------------------------------------------------------
    # Input/output declarations
    #-------------------------------------------------------------------

    def gen_signal_width_name( x ):

      try:
        nbits     = x._dsl.Type.nbits
        width_str = "" if nbits == 1 else " [{}:0]".format(nbits-1)
        return "{} {}".format( width_str, x.get_field_name() )
      except AttributeError: # it is not a Bits type
        print x.Type.nbits
        assert False, "TODO Implement data struct translation"

    input_strs = [ 'input logic{}'.format( gen_signal_width_name(x) ) 
                    for x in sorted( m.get_input_value_ports(), key = repr ) ]

    output_strs = [ 'output logic{}'.format( gen_signal_width_name(x) ) 
                    for x in sorted( m.get_output_value_ports(), key = repr ) ]

    input_decls = ',\n  '.join( input_strs )
    if output_strs:
      input_decls += ','

    output_decls = ',\n  '.join( output_strs )

    #-------------------------------------------------------------------
    # Local wire declarations
    #-------------------------------------------------------------------

    # TODO: dont declare wires that are unused

    wire_strs = [ 'logic{};'.format( gen_signal_width_name( x ) ) 
                    for x in sorted( m.get_wires(), key = repr ) ]

    wire_decls = '\n  '.join( wire_strs )

    #-------------------------------------------------------------------
    # Instantiate child components
    #-------------------------------------------------------------------

    children_strs = []

    # TODO: only declare children signals used in the current component

    for child in m.get_child_components():
      child_name = child.get_field_name()

      # Turn a child's input ports into temporary signal declaration and
      # wiring in instantiation

      sig_decls   = []
      in_wiring   = []
      out_wiring  = []

      # TODO: align all declarations
      for port in sorted( child.get_input_value_ports(), key=repr ):
        fname = port.get_field_name()
        nbits = port._dsl.Type.nbits
        width = "" if nbits == 1 else " [{}:0]".format(nbits-1)
        sig_decls.append("logic{} {}${};".format( width, child_name, fname ) )
        in_wiring.append("  .{0:6}( {1}${0} ),".format( fname, child_name ) )

      for port in sorted( child.get_output_value_ports(), key=repr ):
        fname = port.get_field_name()
        nbits = port._dsl.Type.nbits
        width = "" if nbits == 1 else " [{}:0]".format(nbits-1)
        sig_decls .append("logic{} {}${};".format( width, child_name, fname ) )
        out_wiring.append("  .{0:6}( {1}${0} ),".format( fname, child_name ) )

      children_strs.extend( sig_decls )
      children_strs.append( '' )
      children_strs.append( child.__class__.__name__+' '+child_name)
      children_strs.append( '(' )
      children_strs.append( "  // Child's inputs" )
      children_strs.extend( in_wiring )
      children_strs.append( "  // Child's outputs" )
      children_strs.extend( out_wiring )
      children_strs[-2 if not out_wiring else -1].rstrip(',')
      children_strs.append( ');' )

    children_decls = '\n  '.join( children_strs )

    #-------------------------------------------------------------------
    # Assignments
    #-------------------------------------------------------------------

    assign_strs = []

    for writer, reader in connections_self_self:
      assign_strs.append( 'assign {} = {};'.format( reader.get_field_name(), 
                                                    writer.get_field_name() ) 
                        )

    for writer, reader in connections_child_child:
      assign_strs.append( 'assign {}${} = {}${};'.format(
                          reader.get_host_component().get_field_name(),
                          reader.get_field_name(), 
                          writer.get_host_component().get_field_name(), 
                          writer.get_field_name() )
                        )

    for writer, reader in connections_self_child:
      if writer.get_host_component() is m:
        assign_strs.append( 'assign {}${} = {};'.format(
                            reader.get_host_component().get_field_name(), 
                            reader.get_field_name(), 
                            writer.get_field_name() )
                          )

      else:
        assign_strs.append( 'assign {} = {}${};'.format(
                            reader.get_field_name(), 
                            writer.get_host_component().get_field_name(), 
                            writer.get_field_name() )
                          )

    assignments = '\n  '.join( assign_strs )

    #-------------------------------------------------------------------
    # Update blocks
    #-------------------------------------------------------------------

    blk_srcs = ''

    translator = FuncUpblkTranslator( m )

    for blk in m.get_update_blocks():
      blk_src = translator.enter( blk, m.get_update_block_ast( blk ) )

      # Filter the empty lines in the source code
      pymtl_src = filter( lambda a: a != '', getsource( blk ).split('\n') )

      # Remove extra heading spaces and add comments
      pymtl_srcs = '\n'.join( [ '  // ' + x[ s.get_indent( pymtl_src ) : ] 
        for x in pymtl_src ] )

      blk_srcs += '\n  // Original PyMTL update block\n' + pymtl_srcs + blk_src + '\n'

    return vmodule_upblk_template.format( **vars() )


  def get_indent( s, src ):
    """ find the commom indent level for the source code in src """
    for nindent in xrange(64):
      for stmt in src: 
        if not stmt.startswith( ' '*nindent ):
          return nindent-1
    return 63

#-----------------------------------------------------------------------
# Visitor for translating an update block
#-----------------------------------------------------------------------

class FuncUpblkTranslator( ast.NodeVisitor ):

  def __init__( s, component ):
    s.component         = component
    s.mapping           = component.get_astnode_obj_mapping()

    s.immediate_else          = False
    s.inside_posedge_block    = False

  def enter( s, blk, ast ):
    """ entry point for update block translation """
    s.blk     = blk
    s.nindent = 2

    s.globals = blk.func_globals
    s.closure = {}

    for i, var in enumerate( blk.func_code.co_freevars ):

      # Try to collect the cell contents passed by decorators
      try: s.closure[ var ] = blk.func_closure[ i ].cell_contents
      # It's OK if the decorator doesn't pass any parameters
      except ValueError: pass

    ret = s.visit( ast )

    return ret 

  def newline( s, string ):
      return '\n{}{}'.format( ' '*s.nindent, string )

  def newstmts( s, stmts ):
    s.nindent += 2
    ret = ''.join( [ s.visit(stmt) for stmt in stmts ] )
    s.nindent -= 2
    return ret

  # This helper function returns a string format functor depending on
  # whether the expr node needs parentheses around. The purpose is to
  # make the code more pretty. There are two ways to do so. We can either
  # wrap all binary expressions with parentheses and check at the
  # assignment level to remove the outmost parentheses, or use this helper
  # inside each binary expression to wrap their left/right and by default
  # don't wrap any binary expression as a whole

  def visit_expr_wrap( s, node ):
    if isinstance( node, ast.Attribute ) or isinstance( node, ast.Subscript ) or \
       isinstance( node, ast.Name ) or isinstance( node, ast.Num ) or \
       isinstance( node, ast.Call ):
      return '{}'.format( s.visit( node ) )

    return '({})'.format( s.visit( node ) )

  #---------------------------------------------------------------------
  # Valid ast nodes
  #---------------------------------------------------------------------

  def visit_Module( s, node ):
    assert len( node.body ) == 1 and isinstance( node.body[0], ast.FunctionDef)
    return s.visit( node.body[0] )

  def visit_FunctionDef( s, node ):
    assert len( node.decorator_list ) == 1
    decorator_attr = node.decorator_list[0].attr

    if decorator_attr not in [ 'update', 'func', 'update_on_edge' ]:
      raise TranslationError( s.blk, '@s.' + decorator_attr )

    is_posedge_decorator = False

    # TODO: support Verilog task
    if decorator_attr == 'func':
      ret = 'task'
    else:
      if node.args.args:
        raise TranslationError( s.blk, 'update block cannot have args' )
      if decorator_attr == 'update': 
        ret = s.newline( 'always @(*) begin' )
      elif decorator_attr == 'update_on_edge':
        s.inside_posedge_block  = True
        is_posedge_decorator    = True
        ret = s.newline( 'always @(posedge clk) begin' )

    ret += s.newstmts( node.body )
    ret += s.newline( 'end' )
    if is_posedge_decorator and s.inside_posedge_block:
      s.inside_posedge_block = False

    return ret

  def visit_Assign( s, node ):
    assign  = '<=' if s.inside_posedge_block else '='
    rhs     = s.visit( node.value )

    return ''.join( [ s.newline( '{} {} {};'.\
      format( s.visit( lhs ), assign, rhs ) ) for lhs in node.targets ] )

  def visit_AugAssign( s, node ): 
    lhs     = s.visit( node.target )
    assign  = '<=' if s.inside_posedge_block else '='
    op      = opmap[ type( node.op ) ]
    rhs     = s.visit( node.value )

    return s.newline( '{lhs} {assign} {lhs} {op} {rhs};'.format( **vars() ) )

  def visit_If( s, node ):
    if s.immediate_else:
      s.immediate_else = False
      ret = ' if ({})'.format( s.visit( node.test ) )
    else:
      ret = s.newline( 'if ({})'.format( s.visit( node.test ) ) )

    if len( node.body ) == 1 and not isinstance( node.body[0], ast.If ):
      # If there's only 1 non-if statement, dont add the begin-end pair
      ret += s.newstmts( node.body )
    else:
      ret += ' begin'
      ret += s.newstmts( node.body )
      ret += s.newline( 'end' )

    if len( node.orelse ) == 1:
      # Single statement for the else branch
      if isinstance( node.orelse[0], ast.If ):
        # What the user want is:
        # if ( ... ) [begin] ... [end]
        # else if (...) [begin] ... [end]
        ret += s.newline( 'else' )
        s.immediate_else = True
        ret += s.visit( node.orelse[0] )
      else:
        # We need to handle the indent 
        ret += s.newline( 'else' )
        ret += s.newstmts( node.orelse )
    elif node.orelse:
      # More than 1 statements in the else branch
      ret += s.newline( 'else begin' )
      ret += s.newstmts( node.orelse )
      ret += s.newline( 'end' )

    return ret

  def visit_Expr( s, node ):
    assert isinstance( node.value, ast.Call )
    return s.newline( s.visit( node.value ) + ';' )

  def visit_BoolOp( s, node ):
    return '{}'.format( ' {} '.format( opmap[ type(node.op) ] ) \
               .join( [ s.visit_expr_wrap( expr ) for expr in node.values ] ) )

  def visit_BinOp( s, node ):
    return '{} {} {}'.format( s.visit_expr_wrap( node.left ), 
                              opmap[ type(node.op) ], 
                              s.visit_expr_wrap( node.right ) )

  def visit_UnaryOp( s, node ):
    return '{}{}'.format( opmap[ type(node.op) ], 
                          s.visit_expr_wrap( node.operand ) )

  def visit_IfExp( s, node ):
    return '{} ? {} : {}'.format( s.visit_expr_wrap( node.test ), 
                                  s.visit( node.body ),
                                  s.visit( node.orelse ) )

  def visit_Compare( s, node ):
    # Only the first comparator will be translated!
    try: 
      assert len( node.ops ) == 1
    except AssertionError:
      raise TranslationError( s.blk, node, 'The number of comparators \
                                            should be one' )

    return '{} {} {}'.format( s.visit_expr_wrap( node.left ), 
                              opmap[ type(node.ops[0]) ], 
                              s.visit_expr_wrap( node.comparators[0] ) )

  def visit_Call( s, node ):
    # Example: Bits4(2)
    actual_node = node.func

    if actual_node in s.mapping:
      call = s.mapping[ actual_node ][0]
    else:
      try:
        if actual_node.id in s.globals:
          call = s.globals[ actual_node.id ]
        elif actual_node.id in s.closure:
          call = s.closure[ actual_node.id ]
        else:
          raise NameError
      except AttributeError:
        raise TranslationError( s.blk, node, node.func )
      except NameError:
        raise TranslationError( s.blk, node, node.func.id )

    try:
      nbits = call.nbits
    except AttributeError as e: 
      return '{}( {} )'.format( call.__name__, 
                                ', '.join( [ s.visit( arg ) 
                                             for arg in node.args ] ) )

    assert len( node.args ) == 1
    arg = node.args[0]

    if arg in self.mapping:
      try:
        obj_nb = self.mapping[ arg ][0]._dsl.Type.nbits
      except AttributeError:
        return "{}'d{}".format( nbits, s.mapping[ arg ][0] )

      if obj_nbits < nbits:
        return "{{{}'d0, {}}}".format( nbits-obj_nbits, s.visit( arg ) )
      elif obj_nbits == nbits:
        return s.visit( arg )
      else:
        raise TranslationError( s.blk, node,  )

    else: # TODO: a = Bits32( SEL_A ) where SEL_A is 0
      if isinstance( arg, ast.Num ):
        return "{}'d{}".format( nbits, s.visit( arg ) )
      elif isinstance( arg, ast.Name ):
        return "{}'d{}".format( nbits, s.visit( arg ) )

  def visit_Attribute( s, node ):
    pred      = node.value
    pred_obj  = s.mapping[ pred ][0]

    if pred_obj.is_interface():
      # value.attr
      return '{}_{}'.format( s.visit( pred ), node.attr )

    assert pred_obj.is_component()

    if pred_obj is s.component:
      # pred_obj is host component
      return '{}'.format( node.attr )

    # pred_obj may be a child component
    return '{}${}'.format( s.visit( pred ), node.attr )

  def visit_Subscript( s, node ):
    pred = node.value
    return '{}[{}]'.format( s.visit( pred ), s.visit( node.slice ) )

  def visit_Name( s, node ):
    if node.id in s.globals:
      return s.globals[ node.id ]
    elif node.id in s.closure:
      return s.closure[ node.id ]
    else:
      # Temporary variable encountered
      assert False

  def visit_Num( s, node ):
    return node.n

  def visit_Slice( s, node ):
    return '{}-1:{}'.format( s.visit( node.upper ), s.visit( node.lower ) )

  def visit_Index( s, node ):
    return s.visit( node.value )

  #---------------------------------------------------------------------
  # TODO: Some other AST nodes
  #---------------------------------------------------------------------

  # $display
  def visit_Print( s, ndoe ):
    raise

  # for loop
  def visit_For( s, ndoe ):
    raise

  # ??
  def visit_While( s, ndoe ):
    raise

  # function
  def visit_Return( s, node ):
    raise

  # SV assertion
  def visit_Assert( s, node ):
    raise

  # concatenation
  def visit_ExtSlice( s, node ):
    raise

  #---------------------------------------------------------------------
  # Explicitly invalid AST nodes
  #---------------------------------------------------------------------

  def visit_LambdaOp( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: lambda function' )

  def visit_Dict( s, node ):
    raise TranslationError( s.blk, node, 'invalid type: dict' )

  def visit_Set( s, node ):
    raise TranslationError( s.blk, node, 'invalid type: set' )

  def visit_List( s, node ):
    raise TranslationError( s.blk, node, 'invalid type: list' )

  def visit_Tuple( s, node ):
    raise TranslationError( s.blk, node, 'invalid type: tuple' )

  def visit_ListComp( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: list comprehension' )

  def visit_SetComp( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: set comprehension' )

  def visit_DictComp( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: dict comprehension' )

  def visit_GeneratorExp( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: generator expression' )

  def visit_Yield( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: yield' )

  def visit_Repr( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: repr' )

  def visit_Str( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: str' )

  def visit_ClassDef( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: classdef' )

  def visit_Delete( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: delete' )

  def visit_With( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: with' )

  def visit_Raise( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: raise' )

  def visit_TryExcept( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: try-except' )

  def visit_TryFinally( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: try-finally' )

  def visit_Import( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: import' )

  def visit_ImportFrom( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: import-from' )

  def visit_Exec( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: exec' )

  def visit_Global( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: global' )

  def visit_Pass( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: pass' )

  def visit_Break( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: break' )

  def visit_Continue( s, node ):
    raise TranslationError( s.blk, node, 'invalid operation: continue' )

#-----------------------------------------------------------------------
# opmap definition
#-----------------------------------------------------------------------

opmap = {
    ast.Add      : '+',
    ast.Sub      : '-',
    ast.Mult     : '*',
    ast.Div      : '/',
    ast.Mod      : '%',
    ast.Pow      : '**',
    ast.LShift   : '<<',
    ast.RShift   : '>>',
    ast.BitOr    : '|',
    ast.BitAnd   : '&',
    ast.BitXor   : '^',
    ast.FloorDiv : '/',
    ast.Invert   : '~',
    ast.Not      : '!',
    ast.UAdd     : '+',
    ast.USub     : '-',
    ast.Eq       : '==',
    ast.Gt       : '>',
    ast.GtE      : '>=',
    ast.Lt       : '<',
    ast.LtE      : '<=',
    ast.NotEq    : '!=',
    ast.And      : '&&',
    ast.Or       : '||',
}

def get_closure_dict( funct ):
  closure_objects = [ c.cell_contents for c in funct.func_closure ]
  return dict( zip( funct.func_code.co_freevars, closure_objects ) )
