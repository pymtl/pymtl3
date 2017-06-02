from SimLevel3 import SimLevel3
from collections import defaultdict, deque
import ast

class DFGVisualizer( SimLevel3 ):

  def __init__( self, model, tick_mode='unroll' ):
    self.model = model

    self.recursive_tag_name( model )  # tag name first for error message
    self.recursive_elaborate( model ) # turn "string" into objects
    self.recursive_tag_name( model )  # slicing will spawn extra objects
    self.check_port_in_upblk()        # in/out port check in all upblks
    # self.print_read_write()

    self.resolve_var_connections() # resolve connected nets
    self.check_port_in_net()       # in/out port check in all nets
    self.compact_net_readers()     # remove unread objs, for simulation
    # self.print_nets( self._nets )
    self.generate_net_block()

    expl, impl    = self.synthesize_var_constraints()
    serial, batch = self.schedule( self._blkid_upblk, self._constraints )

    # I need to traverse the ast to figure out the variable data flow
    # dependencies. During elaboration, the objects appeared in update
    # blocks have been attached to the corresponding AST nodes. For net
    # blocks I can just look at collected nets.
    # I also need the batch schedule to find the first batch of nets that
    # contains sequential logic.

    # self.print_upblk_dag( self._blkid_upblk, self._constraints )
    self.visualize()

  def visualize( self ):
    deps = defaultdict(set)
    visitor = DetectDataDependency( deps, self._id_obj )

    for blk in self._blkid_upblk.values():
      print 
      print "+++++++++++++++++++++++++++++++++++++++++++++++++++"
      print "+ {} at {} ".format( blk.__name__ , blk.hostobj.full_name() )
      print "+++++++++++++++++++++++++++++++++++++++++++++++++++"
      print 
      visitor.enter( blk )

    from graphviz import Digraph

    dot = Digraph()
    dot.graph_attr["rank"] = "source"
    dot.graph_attr["ratio"] = "fill"
    dot.graph_attr["margin"] = "0.1"
    for (x, y) in deps:
      dot.edge( self._id_obj[x].full_name(), self._id_obj[y].full_name() )
    dot.render("/tmp/dataflow.gv", view=True)

import astor # DEBUG
_DEBUG = False

class DetectDataDependency( ast.NodeVisitor ):
  def __init__( self, dependencies, id_obj ):
    self.dependencies = dependencies
    self.id_obj = id_obj

  # https://docs.python.org/2/library/ast.html

  def enter( self, blk ):
    self.blk = blk
    self.context_reads = set()
    self.visit( blk.ast )
    assert not self.context_reads

  #-----------------------------------------------------------------------
  # Enumerate all kinds of expr
  #-----------------------------------------------------------------------

  def visit_BoolOp( self, node ):
    if _DEBUG: print "BoolOp", astor.to_source( node ); print
    objs = set()
    for expr in node.values:
      objs |= self.visit( expr )
    return objs

  def visit_BinOp( self, node ):
    if _DEBUG: print "BinOp", astor.to_source( node ); print
    return self.visit( node.left ) | self.visit( node.right )

  def visit_UnaryOp( self, node ):
    if _DEBUG: print "UnaryOp", astor.to_source( node ); print
    return self.visit( node.operand )

  # invalid
  def visit_LambdaOp( self, node ):
    if _DEBUG: print "LambdaOp", astor.to_source( node ); print

  def visit_IfExp( self, node ):
    if _DEBUG: print "IfExp", astor.to_source( node ); print
    return self.visit( node.test ) | self.visit( node.body ) | self.visit( node.orelse )

  # invalid
  def visit_Dict( self, node ):
    if _DEBUG: print "Dict", astor.to_source( node ); print

  # invalid
  def visit_Set( self, node ):
    if _DEBUG: print "Set", astor.to_source( node ); print

  # invalid
  def visit_ListComp( self, node ):
    if _DEBUG: print "ListComp", astor.to_source( node ); print

  # invalid
  def visit_SetComp( self, node ):
    if _DEBUG: print "SetComp", astor.to_source( node ); print

  # invalid
  def visit_DictComp( self, node ):
    if _DEBUG: print "DictComp", astor.to_source( node ); print

  # invalid
  def visit_GeneratorExp( self, node ):
    if _DEBUG: print "GeneratorExp", astor.to_source( node ); print

  # invalid
  def visit_Yield( self, node ):
    if _DEBUG: print "Yield", astor.to_source( node ); print

  def visit_Compare( self, node ):
    if _DEBUG: print "Compare", astor.to_source( node ); print
    assert len(node.ops) == 1

    objs = self.visit( node.left )
    for expr in node.comparators:
      objs |= self.visit( expr )
    return objs

  # call cs
  def visit_Call( self, node ):
    if _DEBUG: print "Call", astor.to_source( node ); print

  # invalid
  def visit_Repr( self, node ):
    if _DEBUG: print "Repr", astor.to_source( node ); print

  # invalid
  def visit_Num( self, node ):
    if _DEBUG: print "Num", astor.to_source( node ); print
    return set()

  # ignore
  def visit_Str( self, node ):
    if _DEBUG: print "Str", astor.to_source( node ); print
    return set()

  def visit_Attribute( self, node ):
    if _DEBUG: print "Attribute", astor.to_source( node ); print
    objs = node._objs[ id(self.blk) ] if hasattr( node, "_objs" ) else set()
    return objs | self.visit( node.value )

  def visit_Subscript( self, node ):
    if _DEBUG: print "Subscript", astor.to_source( node ); print
    objs = node._objs[ id(self.blk) ] if hasattr( node, "_objs" ) else set()
    return objs | self.visit( node.value ) | self.visit( node.slice )

  # temporary variable?
  def visit_Name( self, node ):
    if _DEBUG: print "Name", astor.to_source( node ); print
    return set()

  # invalid
  def visit_List( self, node ):
    if _DEBUG: print "List", astor.to_source( node ); print

  # invalid
  def visit_Tuple( self, node ):
    if _DEBUG: print "Tuple", astor.to_source( node ); print

  #-----------------------------------------------------------------------
  # Enumerate all kinds of stmt
  #-----------------------------------------------------------------------

  # def cs(), task?
  def visit_FunctionDef( self, node ):
    if _DEBUG: print "FunctionDef", astor.to_source( node ); print

    assert node.decorator_list and not node.args.args 

    for stmt in node.body:
      self.visit( stmt )

  # invalid
  def visit_ClassDef( self, node ):
    if _DEBUG: print "ClassDef", astor.to_source( node ); print

  # invalid
  def visit_Return( self, node ):
    if _DEBUG: print "Return", astor.to_source( node ); print

  # invalid
  def visit_Delete( self, node ):
    if _DEBUG: print "Delete", astor.to_source( node ); print

  def visit_Assign( self, node ):
    if _DEBUG: print "Assign", astor.to_source( node ); print

    value_reads = self.visit( node.value ) | self.context_reads
    value_writes = set()
    for expr in node.targets:
      value_writes |= self.visit( expr )

    print
    print "--- source ---:", astor.to_source( node )
    print "context_reads:", [ self.id_obj[x].full_name() for x in self.context_reads ]

    for rd_id in value_reads:
      for wr_id in value_writes:
        print "{} -> {}".format( self.id_obj[rd_id].full_name(), self.id_obj[wr_id].full_name() )

        self.dependencies[ (rd_id, wr_id) ].add( node.lineno )

  def visit_AugAssign( self, node ):
    if _DEBUG: print "AugAssign", astor.to_source( node ); print

    value_reads = self.visit( node.value ) | self.context_reads
    value_writes = self.visit( target )

    for rd in value_reads:
      for wr in value_writes:
        self.dependencies[ (id(rd), id(wr)) ].add( node.lineno )

  # invalid
  def visit_Print( self, node ):
    if _DEBUG: print "Print", astor.to_source( node ); print

  # TODO
  def visit_For( self, node ):
    if _DEBUG: print "For", astor.to_source( node ); print

  # invalid, hls?
  def visit_While( self, node ):
    if _DEBUG: print "While", astor.to_source( node ); print

  def visit_If( self, node ):
    if _DEBUG: print "If", astor.to_source( node ); print

    # The test expression is added to data dependency of the rest of if

    test_reads  = self.visit( node.test )

    need_to_pop = test_reads.copy()
    self.context_reads |= test_reads

    for stmt in node.body:
      self.visit( stmt )

    for stmt in node.orelse:
      tmp_reads    = self.visit( stmt )
      need_to_pop |= tmp_reads
      self.context_reads |= tmp_reads

    self.context_reads -= need_to_pop
    return test_reads

  # invalid
  def visit_With( self, node ):
    if _DEBUG: print "With", astor.to_source( node ); print

  # invalid
  def visit_Raise( self, node ):
    if _DEBUG: print "Raise", astor.to_source( node ); print

  # invalid
  def visit_TryExcept( self, node ):
    if _DEBUG: print "TryExcept", astor.to_source( node ); print

  # invalid
  def visit_TryFinally( self, node ):
    if _DEBUG: print "TryFinally", astor.to_source( node ); print

  # invalid
  def visit_Assert( self, node ):
    if _DEBUG: print "Assert", astor.to_source( node ); print

  # invalid
  def visit_Import( self, node ):
    if _DEBUG: print "Import", astor.to_source( node ); print

  # invalid
  def visit_ImportFrom( self, node ):
    if _DEBUG: print "ImportFrom", astor.to_source( node ); print

  # invalid
  def visit_Exec( self, node ):
    if _DEBUG: print "Exec", astor.to_source( node ); print

  # invalid
  def visit_Global( self, node ):
    if _DEBUG: print "Global", astor.to_source( node ); print

  # invalid hanger expression
  def visit_Expr( self, node ):
    if _DEBUG: print "Expr", astor.to_source( node ); print

  # invalid
  def visit_Pass( self, node ):
    if _DEBUG: print "Pass", astor.to_source( node ); print

  # invalid
  def visit_Break( self, node ):
    if _DEBUG: print "Break", astor.to_source( node ); print

  # invalid
  def visit_Continue( self, node ):
    if _DEBUG: print "Continue", astor.to_source( node ); print

  #-----------------------------------------------------------------------
  # Enumerate all kinds of slice
  #-----------------------------------------------------------------------

  def visit_Slice( self, node ):
    if _DEBUG: print "Slice", astor.to_source( node ); print

  def visit_Extslice( self, node ):
    if _DEBUG: print "ExtSlice", astor.to_source( node ); print

  def visit_Index( self, node ):
    if _DEBUG: print "Index", astor.to_source( node ); print
    return self.visit( node.value )
