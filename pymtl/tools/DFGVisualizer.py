from SimLevel3 import SimLevel3
from collections import defaultdict, deque
import ast
import astor # DEBUG

class DFGVisualizer( SimLevel3 ):

  def __init__( self, model, tick_mode='unroll' ):
    self.model = model

    self.recursive_tag_name( model )  # tag name first for error message
    self.recursive_elaborate( model ) # turn "string" into objects
    self.recursive_tag_name( model )  # slicing will spawn extra objects
    self.check_port_in_upblk()        # in/out port check in all upblks
    self.print_read_write()

    self.resolve_var_connections() # resolve connected nets
    self.check_port_in_net()       # in/out port check in all nets
    self.compact_net_readers()     # remove unread objs, for simulation
    self.print_nets( self._nets )
    self.generate_net_block()

    expl, impl    = self.synthesize_var_constraints()
    serial, batch = self.schedule( self._blkid_upblk, self._constraints )

    # I need to traverse the ast to figure out the variable data flow
    # dependencies. During elaboration, the objects appeared in update
    # blocks have been attached to the corresponding AST nodes. For net
    # blocks I can just look at collected nets.
    # I also need the batch schedule to find the first batch of nets that
    # contains sequential logic.

    self.visualize()

  def visualize( self ):
    visitor = DetectDataDependency()

    for blkid, blk in self._blkid_upblk.iteritems():
      visitor.enter( blk.ast )

class DetectDataDependency( ast.NodeVisitor ):

  # https://docs.python.org/2/library/ast.html

  def enter( self, node ):
    self.dependencies  = set()
    self.current_reads = []
    self.visit( node )

  #-----------------------------------------------------------------------
  # Enumerate all kinds of expr
  #-----------------------------------------------------------------------

  def visit_BoolOp( self, node ):
    print "BoolOp", astor.to_source( node )

  def visit_BinOp( self, node ):
    print "BinOp", astor.to_source( node )

  def visit_UnaryOp( self, node ):
    print "UnaryOp", astor.to_source( node )

  def visit_LambdaOp( self, node ):
    print "LambdaOp", astor.to_source( node )

  def visit_IfExp( self, node ):
    print "IfExp", astor.to_source( node )

  def visit_Dict( self, node ):
    print "Dict", astor.to_source( node )

  def visit_Set( self, node ):
    print "Set", astor.to_source( node )

  def visit_ListComp( self, node ):
    print "ListComp", astor.to_source( node )

  def visit_SetComp( self, node ):
    print "SetComp", astor.to_source( node )

  def visit_DictComp( self, node ):
    print "DictComp", astor.to_source( node )

  def visit_GeneratorExp( self, node ):
    print "GeneratorExp", astor.to_source( node )

  def visit_Yield( self, node ):
    print "Yield", astor.to_source( node )

  def visit_Compare( self, node ):
    print "Compare", astor.to_source( node )

  def visit_Call( self, node ):
    print "Call", astor.to_source( node )

  def visit_Repr( self, node ):
    print "Repr", astor.to_source( node )

  def visit_Num( self, node ):
    print "Num", astor.to_source( node )

  def visit_Str( self, node ):
    print "Str", astor.to_source( node )

  def visit_Attribute( self, node ):
    print "Attribute", astor.to_source( node )
    return [ node._obj ]

  def visit_Subscript( self, node ):
    print "Subscript", astor.to_source( node )
    return [ node._obj ]

  def visit_Name( self, node ):
    print "Name", astor.to_source( node )

  def visit_List( self, node ):
    print "List", astor.to_source( node )

  def visit_Tuple( self, node ):
    print "Tuple", astor.to_source( node )

  #-----------------------------------------------------------------------
  # Enumerate all kinds of stmt
  #-----------------------------------------------------------------------

  def visit_FunctionDef( self, node ):
    print "FunctionDef", astor.to_source( node )

  # invalid
  def visit_ClassDef( self, node ):
    print "ClassDef", astor.to_source( node )

  # invalid
  def visit_Return( self, node ):
    print "Return", astor.to_source( node )

  # ignore
  def visit_Delete( self, node ): pass

  def visit_Assign( self, node ):
    print "Assign", astor.to_source( node )

  def visit_AugAssign( self, node ):
    print "AugAssign", astor.to_source( node )

  # invalid
  def visit_Print( self, node ):
    print "Print", astor.to_source( node )

  def visit_For( self, node ):
    print "For", astor.to_source( node )

  # invalid, hls?
  def visit_While( self, node ):
    print "While", astor.to_source( node )

  def visit_If( self, node ):

    # The test expression is added to data dependency of the rest of if

    test_reads = self.visit( node.test )
    self.current_reads += test_reads

    for stmt in node.body:
      self.visit( stmt )

    for stmt in node.orelse:
      self.visit( stmt )

    for x in len(test_reads):
      self.current_reads.pop()

  # invalid
  def visit_With( self, node ):
    print "With", astor.to_source( node )

  # ignore
  def visit_Raise( self, node ): pass

  # ignore
  def visit_TryExcept( self, node ): pass

  # ignore
  def visit_TryFinally( self, node ): pass

  # def cs(), task?
  def visit_FunctionDef( self, node ):
    assert node.decorator_list and not node.args.args 

    for stmt in node.body:
      self.visit( stmt )

  # invalid
  def visit_Assert( self, node ):
    print "Assert", astor.to_source( node )

  # ignore
  def visit_Import( self, node ): pass

  # invalid
  def visit_ImportFrom( self, node ):
    print "ImportFrom", astor.to_source( node )

  # ignore
  def visit_Exec( self, node ): pass

  # ignore
  def visit_Global( self, node ): pass

  # invalid hanger expression
  def visit_Expr( self, node ):
    print "Expr", astor.to_source( node )

  # ignore
  def visit_Pass( self, node ): pass

  # invalid
  def visit_Break( self, node ):
    print "Break", astor.to_source( node )

  # invalid
  def visit_Continue( self, node ):
    print "Continue", astor.to_source( node )

  #-----------------------------------------------------------------------
  # Enumerate all kinds of slice
  #-----------------------------------------------------------------------

  def visit_Slice( self, node ):
    print "Slice", astor.to_source( node )

  def visit_Extslice( self, node ):
    print "ExtSlice", astor.to_source( node )

  def visit_Index( self, node ):
    print "Index", astor.to_source( node )
