#=========================================================================
# SystemVerilogTranslationPass.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Aug 23, 2018

from pymtl import *
from pymtl.dsl import ComponentLevel1
from BasePass import BasePass
from GenDAGPass import GenDAGPass
from SimpleSchedPass import SimpleSchedPass
from collections import defaultdict, deque
from errors import TranslationError
import ast

vmodule_template = """
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

  // Logic blocks
  {blk_srcs}

endmodule
"""

# TODO Now just assume signals written in update_on_edge are registers
class SystemVerilogTranslationPass( BasePass ):

  def __call__( self, top ):

    GenDAGPass()( top )
    SimpleSchedPass()( top )

    # Generate all names

    model_name      = top.__class__.__name__
    verilog_file    = model_name + '.v'
    temp_file       = model_name + '.v.tmp'
    # c_wrapper_file  = model_name + '_v.cpp'
    # py_wrapper_file = model_name + '_v.py'
    # lib_file        = 'lib{}_v.so'.format( model_name )
    # obj_dir         = 'obj_dir_' + model_name
    # blackbox_file   = model_name + '_blackbox.v'

    # We translate the module in the deepest hierarchy first

    all_components = sorted( top.get_all_components(), key=repr )
    all_components.reverse()

    # Distribute net connections into components' assignments

    nets = top.get_all_value_nets()
    adjs = top.get_signal_adjacency_dict()

    connections_self_child  = defaultdict(set)
    connections_self_self   = defaultdict(set)
    connections_child_child = defaultdict(set)

    for writer, net in nets:
      S = deque( [ writer ] )
      visited = set( [ writer ] )
      while S:
        u = S.pop() # u is the current writer
        writer_host        = u.get_host_component()
        writer_host_parent = writer_host.get_parent_object()

        for v in adjs[u]: # v is the reader
          if v not in visited:
            visited.add( v )
            S.append( v )
            reader_host        = v.get_host_component()
            reader_host_parent = reader_host.get_parent_object()

            # 1. have the same host: writer_host(x)/reader_host(x)
            if   writer_host is reader_host:
              connections_self_self[ writer_host ].add( (u, v) )

            # 2. reader_host(x) is writer_host(x.y)'s parent
            elif writer_host_parent is reader_host:
              connections_self_child[ reader_host ].add( (u, v) )

            # 3. writer_host(x) is reader_host(x.y)'s parent
            elif writer_host is reader_host_parent:
              connections_self_child[ writer_host ].add( (u, v) )

            # 4. hosts have the same parent: writer_host(x.y)/reader_host(x.z)
            # This means that the connection is fulfilled in x
            elif writer_host_parent == reader_host_parent:
              connections_child_child[ writer_host_parent ].add( (u, v) )

            # 5. neither host is the other's parent nor the same.
            else: assert False

    ret = ""
    with open( temp_file, 'w+' ) as fd:
      for obj in all_components:
        ret += self.translate_component( obj, connections_self_self[ obj ],
                                              connections_self_child[ obj ],
                                              connections_child_child[ obj ] )
    print ret

  def translate_component( self, m, connections_self_self,
                                    connections_self_child,
                                    connections_child_child ):
    """ translate_component translates a component to verilog source """

    module_name = m.__class__.__name__ # FIXME

    #---------------------------------------------------------------------
    # Input/output declarations
    #---------------------------------------------------------------------

    # deduplicate code across inport/outport/wire
    def gen_signal_width_name( x ):
      try:
        nbits     = x._dsl.Type.nbits
        width_str = "" if nbits == 1 else " [{}:0]".format(nbits-1)
        return "{} {}".format( width_str, x.get_field_name() )
      except AttributeError: # it is not a Bits type
        print x.Type.nbits
        assert False, "TODO Implement data struct translation"

    input_strs = [ "input logic{}".format( gen_signal_width_name(x) )
                    for x in sorted( m.get_input_value_ports(), key=repr ) ]

    output_strs = [ "output logic{}".format( gen_signal_width_name(x) )
                    for x in sorted( m.get_output_value_ports(), key=repr ) ]

    input_decls = ",\n  ".join( input_strs )
    if output_strs: # add comma if it isn't the last declaration
      input_decls += ","

    output_decls = ",\n  ".join( output_strs )

    #---------------------------------------------------------------------
    # Local wire declarations
    #---------------------------------------------------------------------

    # TODO don't declare wires that are not used

    wire_strs  = [ "logic{};".format( gen_signal_width_name(x) )
                    for x in sorted( m.get_wires(), key=repr ) ]
    wire_decls = "\n  ".join( wire_strs )

    #---------------------------------------------------------------------
    # Instantiate child components
    #---------------------------------------------------------------------

    children_strs = []
    # TODO only declare children signals used in the current component?

    for child in m.get_child_components():
      child_name = child.get_field_name()

      # Turn child's input ports into temporary signal declaration and
      # wiring in instantiation.

      sig_decls  = []
      in_wiring  = []
      out_wiring = []

      # TODO align all declarations
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

      # Instantiate the child module

      children_strs.extend( sig_decls )
      children_strs.append( "" )
      children_strs.append( child.__class__.__name__ + " " + child_name ) # FIXME
      children_strs.append( "(" )
      children_strs.append( "  // Child's inputs" )
      children_strs.extend( in_wiring )
      children_strs.append( "  // Child's outputs" )
      children_strs.extend( out_wiring )
      children_strs[-2 if not out_wiring else -1].rstrip(",") # Remove the last comma

      children_strs.append( ");" )

    children_decls = "\n  ".join( children_strs )

    #---------------------------------------------------------------------
    # Assignments
    #---------------------------------------------------------------------

    assign_strs = []

    for writer, reader in connections_self_self:
      assign_strs.append( "assign {} = {};".format( reader.get_field_name(),
                                                    writer.get_field_name() )
                        )

    for writer, reader in connections_child_child:
      assign_strs.append( "assign {}${} = {}${};".format(
                          reader.get_host_component().get_field_name(),
                          reader.get_field_name(),
                          writer.get_host_component().get_field_name(),
                          writer.get_field_name() )
                        )

    for writer, reader in connections_self_child:
      if writer.get_host_component() is m:
        assign_strs.append( "assign {}${} = {};".format(
                            reader.get_host_component().get_field_name(),
                            reader.get_field_name(),
                            writer.get_field_name() )
                          )
      else:
        assign_strs.append( "assign {} = {}${};".format(
                            reader.get_field_name(),
                            writer.get_host_component().get_field_name(),
                            writer.get_field_name() ) )

    assignments = "\n  ".join( assign_strs )

    #---------------------------------------------------------------------
    # Update blocks
    #---------------------------------------------------------------------

    blk_src = []

    translator = FuncUpblkTranslator( m )

    for blk in m.get_update_blocks():
      x = translator.enter( blk, m.get_update_block_ast( blk ) )
      blk_src.append( x )

    # for name, func in m._name_func.iteritems():
      # func_src.append( translate_func( func ) )

    blk_srcs = "\n".join( blk_src )

    return vmodule_template.format( **vars() )

#-------------------------------------------------------------------------
# Visitor for update block translation
#-------------------------------------------------------------------------

class FuncUpblkTranslator( ast.NodeVisitor ):
  def __init__( self, component ):
    self.component = component
    self.mapping   = component.get_astnode_obj_mapping()

  def enter( self, blk, ast ):
    self.blk     = blk
    self.nindent = 2

    self.globals = blk.func_globals
    self.closure = {}
    for i, var in enumerate( blk.func_code.co_freevars ):
      try:  self.closure[ var ] = blk.func_closure[i].cell_contents
      except ValueError: pass

    ret = self.visit( ast )
    return ret

  def newline( self, string ):
    return "\n{}{}".format( ' '*self.nindent, string )

  def newstmts( self, stmts ):
    self.nindent += 2
    ret = ''.join( [ self.visit(stmt) for stmt in stmts ] )
    self.nindent -= 2
    return ret

  # This helper function returns a string format functor depending on
  # whether the expr node needs parentheses around. The purpose is to
  # make the code more pretty. There are two ways to do so. We can either
  # wrap all binary expressions with parentheses and check at the
  # assignment level to remove the outmost parentheses, or use this helper
  # inside each binary expression to wrap their left/right and by default
  # don't wrap any binary expression as a whole

  def visit_expr_wrap( self, node ):
    if isinstance( node, ast.Attribute ) or isinstance( node, ast.Subscript ) or \
       isinstance( node, ast.Name ) or isinstance( node, ast.Num ) or \
       isinstance( node, ast.Call ):
      return "{}".format( self.visit(node) )
    return "({})".format( self.visit(node) )

  #-----------------------------------------------------------------------
  # Valid ast nodes
  #-----------------------------------------------------------------------

  def visit_Module( self, node ):
    assert len(node.body) == 1 and isinstance( node.body[0], ast.FunctionDef )
    return self.visit( node.body[0] )

  # statements

  def visit_FunctionDef( self, node ):
    assert len(node.decorator_list) == 1

    decorator_attr = node.decorator_list[0].attr

    # the schedule anyways

    if decorator_attr not in [ 'update', 'func', 'update_on_edge' ]:
      raise TranslationError( self.blk, "@s." + decorator_attr )

    if decorator_attr == 'func':
      ret = 'task' # TODO

    else:
      if node.args.args:
        raise TranslationError( self.blk, "update block cannot have args" )

      if decorator_attr == 'update':
        ret = self.newline( 'always @(*) begin' )
      elif decorator_attr == 'update_on_edge':
        ret = self.newline( 'always @(posedge clk) begin' )

    ret += self.newstmts( node.body )
    ret += self.newline( 'end' )

    return ret

  # TODO remove outmost parentheses
  def visit_Assign( self, node ): # a = ...
    # if len(node.targets) != 1 or isinstance(node.targets[0], (ast.Tuple)):
      # raise TranslationError( self.blk,
        # 'Assignments can only have one item on the left-hand side!\n'
        # 'Please modify "x,y = ..." to be two separate lines.',
      # )

    assign = '=' # if node._is_blocking else '<='
    rhs    = self.visit( node.value )

    return "".join( [ self.newline( '{} {} {};'.format(self.visit(lhs), assign, rhs) )
                      for lhs in node.targets ] )

  def visit_AugAssign( self, node ): # a += ...

    newline = '\n' + ' ' * self.nindent
    lhs    = self.visit( node.target )
    assign = '=' # if node._is_blocking else '<='
    op     = opmap[ type(node.op) ]
    rhs    = self.visit( node.value )

    return self.newline( '{lhs} {assign} {lhs} {op} {rhs};'.format(**vars()) )

  def visit_If( self, node ):

    ret  = self.newline( 'if ({})'.format( self.visit( node.test ) ) )

    # remove begin/end pair if there is only one non-if stmt

    if len( node.body ) == 1 and not isinstance( node.body[0], ast.If ):
      ret += self.newstmts( node.body )
    else:
      ret += ' begin'
      ret += self.newstmts( node.body )
      ret += self.newline( 'end' )

    if len(node.orelse) == 1:
      if isinstance( node.orelse[0], ast.If ): # special, don't indent
        ret += self.newline( 'else' )
        ret += self.visit( node.orelse[0] )
      else: # non-if, remove begin/end, but indent
        ret += self.newline( 'else' )
        ret += self.newstmts( node.orelse )

    elif node.orelse:
      ret   += self.newline( 'else begin' )
      ret   += self.newstmts( node.orelse )
      ret   += self.newline( 'end' )

    return ret

  # The only case we allow an expression without lvalue is function call

  def visit_Expr( self, node ):
    assert isinstance( node.value, ast.Call )
    return self.newline( self.visit( node.value ) + ";" )

  # Expressions

  def visit_BoolOp( self, node ):
    return "{}".format( " {} ".format( opmap[ type(node.op) ] )
                          .join([ self.visit_expr_wrap( expr ) for expr in node.values ] ) )

  def visit_BinOp( self, node ):
    return "{} {} {}".format( self.visit_expr_wrap( node.left ),
                              opmap[ type(node.op) ],
                              self.visit_expr_wrap( node.right ) )

  def visit_UnaryOp( self, node ):
    return "{}{}".format( opmap[ type(node.op) ],
                           self.visit_expr_wrap( node.operand ) )

  def visit_IfExp( self, node ):
    return "{} ? {} : {}".format( self.visit_expr_wrap( node.test ),
                                  self.visit( node.body ),
                                  self.visit( node.orelse ) )

  def visit_Compare( self, node ):
    return "{} {} {}".format( self.visit_expr_wrap( node.left ),
                              opmap[ type(node.ops[0]) ],
                              self.visit_expr_wrap( node.comparators[0] ) )

  # call cs/type
  def visit_Call( self, node ):
    # func_globals will have BitsX types
    actual_node = node.func

    if actual_node in self.mapping:
      call = self.mapping[actual_node][0]
    else:
      try:
        if   actual_node.id in self.globals:
          call = self.globals[ actual_node.id ]
        elif actual_node.id in self.closure:
          call = self.closure[ actual_node.id ]
        else:
          raise NameError
      except AttributeError:
        raise TranslationError( self.blk, node, node.func )
      except NameError:
        raise TranslationError( self.blk, node, node.func.id )

    try:
      nb = call.nbits
    except AttributeError as e:
      # This is an actual function call.
      # TODO max, min,
      return "{}( {} )".format( call.__name__,
                                ", ".join( [ self.visit( arg )
                                              for arg in node.args ] ) )

    # This is for BitsX
    assert len( node.args ) == 1
    arg = node.args[0]

    if arg in self.mapping:
      try:
        obj_nb = self.mapping[ arg ][0]._dsl.Type.nbits
      except AttributeError:
        # This is not a signal. Use the value instead.
        return "{}'d{}".format( nb, self.mapping[ arg ][0] )

      if obj_nb < nb:
        return "{{{}'d0, {}}}".format( nb-obj_nb, self.visit(arg) )
      elif obj_nb == nb:
        return self.visit(arg)
      else:
        raise TranslationError( self.blk, node,  )

    else: # TODO check case "a = Bits32( SEL_A )" where SEL_A is 0
      if   isinstance( arg, ast.Num ):
        return "{}'d{}".format( nb, self.visit( arg ) )
      elif isinstance( arg, ast.Name ):
        return "{}'d{}".format( nb, self.visit( arg ) )

  def visit_Attribute( self, node ):
    pred     = node.value
    # TODO check if all objects in the list have the same type
    pred_obj = self.mapping[pred][0]

    if pred_obj.is_interface():
      return "{}_{}".format( self.visit( pred ), node.attr )

    assert pred_obj.is_component()

    if pred_obj is self.component:
      return "{}".format( node.attr )

    # pred_obj is not the host component
    return "{}${}".format( self.visit( pred ), node.attr )

  def visit_Subscript( self, node ):
    pred = node.value
    return "{}[{}]".format( self.visit( pred ), self.visit( node.slice ) )

  # temporary variable or other constants
  def visit_Name( self, node ):
    if   node.id in self.globals:
      return self.globals[ node.id ]
    elif node.id in self.closure:
      return self.closure[ node.id ]
    else:
      # This is a temporary variable
      assert False

  def visit_Num( self, node ):
    return node.n

  # slices

  def visit_Slice( self, node ):
    return "{} -1:{}".format( self.visit(node.upper), self.visit(node.lower) )

  def visit_Index( self, node ):
    return self.visit( node.value )

  #-----------------------------------------------------------------------
  # TODO ast nodes
  #-----------------------------------------------------------------------

  # TODO $display
  def visit_Print( self, node ):
    raise

  # TODO simple loop
  def visit_For( self, node ):
    raise

  # TODO hls?
  def visit_While( self, node ):
    raise

  # TODO function
  def visit_Return( self, node ):
    raise

  # TODO SV assertion
  def visit_Assert( self, node ):
    raise

  # TODO support this concatenation?
  def visit_Extslice( self, node ):
    raise

  #-----------------------------------------------------------------------
  # Invalid ast nodes
  #-----------------------------------------------------------------------

  def visit_LambdaOp( self, node ):
    raise TranslationError( self.blk, node, "lambda op" )
  def visit_Dict( self, node ):
    raise TranslationError( self.blk, node, "dict" )
  def visit_Set( self, node ):
    raise TranslationError( self.blk, node, "set" )
  def visit_ListComp( self, node ):
    raise TranslationError( self.blk, node, "listcomp" )
  def visit_SetComp( self, node ):
    raise TranslationError( self.blk, node, "setcomp" )
  def visit_DictComp( self, node ):
    raise TranslationError( self.blk, node, "dictcomp" )
  def visit_GeneratorExp( self, node ):
    raise TranslationError( self.blk, node, "generatorexp" )
  def visit_Yield( self, node ):
    raise TranslationError( self.blk, node, "yield" )
  def visit_Repr( self, node ):
    raise TranslationError( self.blk, node, "repr" )
  def visit_Str( self, node ):
    raise TranslationError( self.blk, node, "str" )
  def visit_List( self, node ):
    raise TranslationError( self.blk, node, "list" )
  def visit_Tuple( self, node ):
    raise TranslationError( self.blk, node, "tuple" )
  def visit_ClassDef( self, node ):
    raise TranslationError( self.blk, node, "classdef" )
  def visit_Delete( self, node ):
    raise TranslationError( self.blk, node, "delete" )
  def visit_With( self, node ):
    raise TranslationError( self.blk, node, "with" )
  def visit_Raise( self, node ):
    raise TranslationError( self.blk, node, "raise" )
  def visit_TryExcept( self, node ):
    raise TranslationError( self.blk, node, "try except" )
  def visit_TryFinally( self, node ):
    raise TranslationError( self.blk, node, "try finally" )
  def visit_Import( self, node ):
    raise TranslationError( self.blk, node, "import" )
  def visit_ImportFrom( self, node ):
    raise TranslationError( self.blk, node, "importfrom" )
  def visit_Exec( self, node ):
    raise TranslationError( self.blk, node, "exec" )
  def visit_Global( self, node ):
    raise TranslationError( self.blk, node, "global" )
  def visit_Pass( self, node ):
    raise TranslationError( self.blk, node, "pass" )
  def visit_Break( self, node ):
    raise TranslationError( self.blk, node, "break" )
  def visit_Continue( self, node ):
    raise TranslationError( self.blk, node, "continue" )

#-----------------------------------------------------------------------
# opmap
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

def get_closure_dict( fn ):
  closure_objects = [c.cell_contents for c in fn.func_closure]
  return dict( zip( fn.func_code.co_freevars, closure_objects ))
