from pymtl import *
from pymtl.model import ComponentLevel1
from BasePass import BasePass
from ScheduleUpblkPass import ScheduleUpblkPass
from collections import defaultdict, deque
from errors import TranslationError
import ast

class SVTranslationPass( BasePass ):

  def apply( self, top ):

    if not hasattr( top, "_batch_schedule" ):
      top.elaborate()
      ScheduleUpblkPass().apply( top )

    # Generate all names

    model_name      = top.__class__.__name__
    verilog_file    = model_name + '.v'
    temp_file       = model_name + '.v.tmp'
    c_wrapper_file  = model_name + '_v.cpp'
    py_wrapper_file = model_name + '_v.py'
    lib_file        = 'lib{}_v.so'.format( model_name )
    obj_dir         = 'obj_dir_' + model_name
    blackbox_file   = model_name + '_blackbox.v'

    # Copy metadata from the top level to self

    self._all_nets         = top._all_nets
    self._batch_schedule   = top._batch_schedule
    self._all_read_upblks  = top._all_read_upblks
    self._all_write_upblks = top._all_write_upblks

    # Build a "trie"

    self._trie_root = ( top, {} )
    self._id_trie   = { id(top) : self._trie_root }
    components = []

    for obj in sorted( top._id_obj.values(), key=repr ): # make sure s.x appears before s.x.y
      if isinstance( obj, ComponentLevel1 ):
        components.append( obj )

      tree = self._trie_root[1]

      for x in repr(obj).split(".")[1:]:
        if x not in tree:
          tree[x] = ( obj, {} )
        tree = tree[x][1]

      self._id_trie[ id(obj) ] = tree

    with open( temp_file, 'w+' ) as fd:
      for m in components:
        self.translate_component( m )

  def translate_component( self, m ):

    #---------------------------------------------------------------------
    # Preparation
    #---------------------------------------------------------------------

    # Classify objects

    children = []
    inputs   = []
    outputs  = []
    wires    = []

    for name, (obj, _) in self._id_trie[ id(m) ].iteritems():
      if   isinstance( obj, ComponentLevel1 ): children.append( (name, obj) )
      elif isinstance( obj, InVPort ):    inputs.append( (name, obj) )
      elif isinstance( obj, OutVPort ):   outputs.append( (name, obj) )
      elif isinstance( obj, Wire ):       wires.append( (name, obj) )

    # Decide which wires are registers

    # reg_id = self.check_register( m )

    # Collect local parameters

    blk_src = []

    for name, blk in m._name_upblk.iteritems():
      blk_src.append( self.translate_upblk( blk ) )

    # for name, func in m._name_func.iteritems():
      # func_src.append( translate_func( func ) )

  def translate_upblk( self, upblk ):
    print FuncUpblkTranslator().enter( upblk )

class FuncUpblkTranslator( ast.NodeVisitor ):

  def enter( self, blk ):
    self.blk = blk
    self.nindent = 2
    return self.visit( blk.ast )

  def newline( self, string ):
    return "\n{}{}".format( ' '*self.nindent, string )

  def newstmts( self, stmts ):
    self.nindent += 2
    ret = ''.join( [ self.visit(stmt) for stmt in stmts ] )
    self.nindent -= 2
    return ret

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

    # Note that update_on_edge is useless because we need to look at
    # the schedule anyways

    if decorator_attr not in [ 'update', 'func', 'update_on_edge' ]:
      raise TranslationError( self.blk, "@s." + decorator_attr )

    if decorator_attr in [ 'update', 'update_on_edge' ]:
      if node.args.args:
        raise TranslationError( self.blk, "update block cannot have args" )

      ret  = self.newline( 'always_comb begin' )
      ret += self.newstmts( node.body )
      ret += self.newline( 'end' )

    elif decorator_attr == 'func':
      ret = '' # TODO

    return ret

  # TODO remove outmost parentheses
  def visit_Assign( self, node ): # a = ...
    if len(node.targets) != 1 or isinstance(node.targets[0], (ast.Tuple)):
      raise TranslationError( self.blk, node,
        'Assignments can only have one item on the left-hand side!\n'
        'Please modify "x,y = ..." to be two separate lines.',
      )

    lhs    = self.visit( node.targets[0] )
    assign = '=' # if node._is_blocking else '<='
    rhs    = self.visit( node.value )

    return self.newline( '{lhs} {assign} {rhs};'.format(**vars()) )

  def visit_AugAssign( self, node ): # a += ...

    newline = '\n' + ' ' * self.nindent
    lhs    = self.visit( node.target )
    assign = '=' # if node._is_blocking else '<='
    op     = opmap[ type(node.op) ]
    rhs    = self.visit( node.value )

    return self.newline( '{lhs} {assign} {lhs} {op} {rhs};'.format(**vars()) )

  def visit_If( self, node ):

    ret  = self.newline( 'if ' + self.visit( node.test ) )

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
    return "({})".format( " {} ".format( opmap[ type(node.op) ] )
                          .join([ self.visit( expr ) for expr in node.values ] ) )

  def visit_BinOp( self, node ):
    return "({} {} {})".format( self.visit( node.left ),
                                opmap[ type(node.op) ],
                                self.visit( node.right ) )

  def visit_UnaryOp( self, node ):
    return "({} {})".format( opmap[ type(node.op) ],
                             self.visit( node.operand ) )

  def visit_IfExp( self, node ):
    return "({} ? {} : {}".format( self.visit( node.test ),
                                   self.visit( node.body ),
                                   self.visit( node.orelse ) )

  def visit_Compare( self, node ):
    return "({} {} {})".format( self.visit( node.left ),
                                opmap[ type(node.ops[0]) ],
                                self.visit( node.comparators[0] ) )

  # call cs/type
  def visit_Call( self, node ):
    # func_globals will have BitsX types

    if   hasattr( node, "_funcs" ):
      call = list( node._funcs[ id(self.blk) ] )[0]
    elif node.func.id in self.blk.func_globals:
      call = self.blk.func_globals[ node.func.id ]
    else:
      raise TranslationError( self.blk, node, node.func.id )

    try:
      # This is for BitsX
      nb = call.nbits
      assert len( node.args ) == 1
      return "{}'d{}".format( nb, self.visit( node.args[0] ) )
    except AttributeError:
      # This is an actual function call.
      return "{}( {} )".format( call.__name__,
                                ", ".join( [ self.visit( arg )
                                              for arg in node.args ] ) )

  def visit_Attribute( self, node ):
    assert hasattr( node, "_objs" )
    obj = list( node._objs[ id(self.blk) ] )[0]
    name = repr( obj )

    # process the name: first remove "s.", then mangle $ for children port
    name = name[name.find(".")+1:]
    name = name.replace( ".", "$" )
    return name

  def visit_Subscript( self, node ):
    # DOING
    objs = node._objs[ id(self.blk) ] if hasattr( node, "_objs" ) else set()
    return objs | self.visit( node.value ) | self.visit( node.slice )

  # temporary variable?
  def visit_Name( self, node ):
    return set()

  def visit_Num( self, node ):
    return node.n

  # slices

  def visit_Slice( self, node ):
    return set()

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
