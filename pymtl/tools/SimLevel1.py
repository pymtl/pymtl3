from SimBase import SimBase
from pymtl.components import UpdateOnly, NamedObject
from collections import defaultdict, deque
import py, ast

class SimLevel1( SimBase ):

  def __init__( self, model ):
    self.model = model

    self.recursive_tag_name( model )
    self.recursive_elaborate( model )

    # print_upblk_dag( self._blkid_upblk, self._constraints )

    serial, batch = self.schedule( self._blkid_upblk, self._U_U_constraints )
    print_schedule( serial, batch )

    self.tick = self.generate_tick_func( serial )

    if hasattr( model, "line_trace" ):
      self.line_trace = model.line_trace

  def _declare_vars( self ):
    self._name_upblk  = {}
    self._blkid_upblk = {}
    self._U_U_constraints = set()

  def _elaborate_vars( self, m ):
    pass

  def _collect_vars( self, m ):
    if isinstance( m, UpdateOnly ):
      self._name_upblk.update ( m._name_upblk )
      self._blkid_upblk.update( m._blkid_upblk )
      self._U_U_constraints.update( m._U_U_constraints )

  def _recursive_elaborate( self, m ):

    def _recursive_expand( child ):

      # Jump back to main function when it's another named object
      if isinstance( child, NamedObject ):
        self._recursive_elaborate( child )

      # SORRY
      if isinstance( child, list ) or isinstance( child, deque ):
        for i, o in enumerate( child ):
          _recursive_expand( o )

    for name, obj in m.__dict__.iteritems():
      if ( isinstance( name, basestring ) and not name.startswith("_") ) \
        or isinstance( name, tuple):
          _recursive_expand( obj )

    self._elaborate_vars( m )
    self._collect_vars( m )

  # Enumerate all child objects and call recursive_expand to figure out
  # what to do with the child object, and collect variables from child.
  # Then elaborate all variables at the current level.

  def recursive_elaborate( self, m ):
    self._declare_vars()
    self._recursive_elaborate( m )

  #-------------------------------------------------------------------------
  # schedule
  #-------------------------------------------------------------------------
  # Based on all constraints on the update block list, calculate a feasible
  # static schedule for update blocks. This schedule funtion returns two
  # schedules: serial_schedule and batch_schedule. The former is just ready
  # to go, while the latter one is more for dataflow analysis purpose.

  @staticmethod
  def schedule( upblk_dict, constraints ):

    # Construct the graph

    vs  = upblk_dict.keys()
    es  = defaultdict(list)
    InD = { v:0 for v in vs }
    OuD = { v:0 for v in vs }

    for (u, v) in list(constraints): # u -> v, always
      InD[v] += 1
      OuD[u] += 1
      es [u].append( v )

    # Perform topological sort for a serial schedule.

    Q = deque()
    for v in vs:
      if not InD[v]:
        Q.append( v )
      # if not InD[v] and not OuD[v]:
        # print "Warning: update block \"{}\" has no constraint".format( upblk_dict[v].__name__ )

    serial_schedule = []
    while Q:
      # random.shuffle(Q) # to catch corner cases; will be removed later
      u = Q.pop()
      serial_schedule.append( upblk_dict[u] )
      for v in es[u]:
        InD[v] -= 1
        if not InD[v]:
          Q.append( v )

    if len(serial_schedule) != len(vs):
      assert False, """
  Update blocks have cyclic dependencies.
  * Please consult update dependency graph for details."
      """

    # Extract batches of frontiers which gives better idea for dataflow

    InD = { v:0 for v in vs }

    for u in es.values():
      for v in u:
        InD[v] += 1

    Q = deque()
    for v in vs:
      if not InD[v]:
        Q.append( v )

    batch_schedule = []

    while Q:
      Q2 = deque()
      batch_schedule.append( [ upblk_dict[v] for v in Q ] )
      for u in Q:
        for v in es[u]:
          InD[v] -= 1
          if not InD[v]:
            Q2.append( v )
      Q = Q2

    return serial_schedule, batch_schedule

  #-------------------------------------------------------------------------
  # generate_tick_func
  #-------------------------------------------------------------------------
  # After we come up with a schedule, we generate a tick function that calls
  # all update blocks. We can do "JIT" here.

  def generate_tick_func( self, schedule, mode='unroll' ):

    if mode == 'normal':
      def tick_normal():
        for blk in schedule:
          blk()

      return tick

    if mode == 'unroll': # Berkin's recipe
      strs = map( "  update_blk{}()".format, xrange( len( schedule ) ) )
      gen_schedule_src = py.code.Source("""
        {}
        def tick_unroll():
          # The code below does the actual calling of update blocks.
          {}

        """.format( "; ".join( map(
                    "update_blk{0} = schedule[{0}]".format,
                        xrange( len( schedule ) ) ) ),
                    "\n          ".join( strs ) ) )

      exec gen_schedule_src.compile() in locals()
      return tick_unroll

    if mode == 'hacky':
      top      = self.model
      rewriter = RewriteSelf()

      # Construct a new FunctionDef AST node and the Module wrapper

      newfunc = ast.FunctionDef()
      newfunc.col_offset = 0
      newfunc.lineno     = 0
      newfunc.name = "tick_hacky"
      newfunc.decorator_list = []
      newfunc.body = []
      newfunc.args = ast.arguments()
      newfunc.args.args = []
      newfunc.args.kwarg = None
      newfunc.args.defaults = []
      newfunc.args.vararg = None

      newroot = ast.Module()
      newroot.body = [ newfunc ]

      # Concatenate update block statements

      for blk in schedule:
        hostobj = blk.hostobj.full_name()
        root    = blk.ast

        # in the form of:
        # >>> hostobj = top.reg # this is hostobj_stmt
        # >>> hostobj.out = hostobj.in_ # stmt

        if hostobj != "s":
          hostobj_stmt = ast.parse( "hostobj = " + hostobj ).body[0]
          newfunc.body.append( ast.fix_missing_locations( hostobj_stmt ) )

        for stmt in root.body[0].body:
          if hostobj != "s": rewriter.visit( stmt )
          newfunc.body.append( stmt )

      exec compile( newroot, "<string>", "exec") in locals()
      return tick_hacky

def print_upblk_dag( upblk_dict, constraints ):
  from graphviz import Digraph
  dot = Digraph()
  dot.graph_attr["rank"] = "source"
  dot.graph_attr["ratio"] = "fill"
  dot.graph_attr["margin"] = "0.1"
  for x in upblk_dict.values():
    # dot.node( x.__name__+"@"+hex(id(x)) )
    dot.node( x.__name__ )
  for (x, y) in constraints:
    dot.edge( upblk_dict[x].__name__, upblk_dict[y].__name__ )
  dot.render("/tmp/upblk_dag.gv", view=True)

def print_schedule( schedule, batch_schedule ):
  print
  for (i, blk) in enumerate( schedule ):
    print i, blk.__name__
  for x in batch_schedule:
    print [ y.__name__ for y in x ]

class RewriteSelf(ast.NodeVisitor):
  def visit_Attribute( self, node ):
    if isinstance( node.value, ast.Name ): # s.x
      if node.value.id == "s": # this is not optimized by "common writer"
        node.value.id = "hostobj"
    else:
      self.visit( node.value )
