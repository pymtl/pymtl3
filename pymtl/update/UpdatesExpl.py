#=========================================================================
# UpdatesExpl.py
#=========================================================================
# At the bottom level, we only have update blocks and explicit constraints
# between two update blocks/one update block. Basically this layer defines
# the scheduling policy/elaboration process.
# Each update block is called exactly once every cycle. PyMTL will
# schedule all update blocks based on the constraints. A total constraint
# between two update blocks specifies the order of the two blocks, i.e.
# call A before B.
# We collect one type of explicit constraints at this level:
# * Block constraint: s.add_constraints( U(upA) < U(upB) )

verbose = False
# verbose = True

import random
from collections     import defaultdict, deque
from ConstraintTypes import U

class UpdatesExpl( object ):

  def __new__( cls, *args, **kwargs ):
    inst = object.__new__( cls, *args, **kwargs )
    # These will be collected recursively
    inst._name_upblk       = {}
    inst._blkid_upblk      = {}
    inst._expl_constraints = set() # contains ( id(func), id(func) )s

    # Bookkeep name hierarchy here for error message and other purposes
    # For example, s.x[0][3].y[2].z turns into
    # ( ["top","x","y","z"], [ [], [0,3], [2], [] ] )
    inst._name_idx = ( ["top"], [ [] ] )
    return inst

  def update( s, blk ):
    assert blk.__name__ not in s._name_upblk, ("Cannot declare two update blocks using the same name!")
    s._name_upblk[ blk.__name__ ] = s._blkid_upblk[ id(blk) ] = blk
    return blk

  def get_update_block( s, name ):
    return s._name_upblk[ name ]

  def add_constraints( s, *args ):
    for (x0, x1) in args:
      if   isinstance( x0, U ) and isinstance( x1, U ):
        s._expl_constraints.add( (id(x0.func), id(x1.func)) )

  def _synthesize_constraints( s ):
    s._total_constraints = s._expl_constraints.copy()

  def _collect_child_vars( s, child ):
    if isinstance( child, UpdatesExpl ):
      s._name_upblk.update( child._name_upblk )
      s._blkid_upblk.update( child._blkid_upblk )
      s._expl_constraints.update( child._expl_constraints )

  def _elaborate_vars( s ):
    pass

  def _enumerate_types( s, name, obj, idx ):
    if isinstance( obj, list ):
      for i in xrange(len(obj)):
        s._enumerate_types( name, obj[i], idx + [i] )

    if isinstance( obj, UpdatesExpl ):
      obj._father   = s
      obj._name_idx = ( s._name_idx[0] + [name], s._name_idx[1] + [list(idx)] )
      obj._recursive_elaborate()
      s._collect_child_vars( obj )

  def _recursive_elaborate( s ):

    for name, obj in s.__dict__.iteritems():
      if not name.startswith("_"): # filter private variables
        s._enumerate_types( name, obj, [] )

    s._elaborate_vars()

  def _elaborate( s ):
    s._recursive_elaborate()

  def _schedule( s ):

    if verbose:
      from graphviz import Digraph
      dot = Digraph(comment = s.__class__)
      dot.graph_attr["rank"] = "source"
      dot.graph_attr["ratio"] = "fill"
      dot.graph_attr["margin"] = "0.1"
      for (x, y) in s._total_constraints:
        dot.edge( s._blkid_upblk[x].__name__+"@"+hex(x), s._blkid_upblk[y].__name__+"@"+hex(y) )
      dot.render("/tmp/pymtl.gv", view=True)

    N = len( s._blkid_upblk )
    edges  = [ [] for _ in xrange(N) ]
    upblks = s._blkid_upblk.keys()
    InDeg  = [0] * N
    OutDeg = [0] * N

    # Discretize in O(NlogN), to avoid later O(logN) lookup

    id_vtx = dict()
    for i in xrange(N):
      id_vtx[ upblks[i] ] = i

    # Prepare the graph

    for (x, y) in list(s._total_constraints):
      vtx_x = id_vtx[ x ]
      vtx_y = id_vtx[ y ]
      edges [ vtx_x ].append( vtx_y )
      InDeg [ vtx_y ] += 1
      OutDeg[ vtx_x ] += 1

    # Perform topological sort in O(N+M). Note that this gives us a linear
    # schedule.

    Q = deque()
    for i in xrange(N):
      if InDeg[i] == 0:
        Q.append( i )
      assert InDeg[i]>0 or OutDeg[i]>0, "Update block \"%s\" has no constraint" % s._blkid_upblk[ upblks[i] ].__name__

    s._schedule_list = []
    while Q:
      # random.shuffle(Q) # to catch corner cases; will be removed later

      u = Q.popleft() # bfs order is faster than dfs order
      s._schedule_list.append( s._blkid_upblk[ upblks[u] ] )
      for v in edges[u]:
        InDeg[v] -= 1
        if InDeg[v] == 0:
          Q.append( v )

    assert len(s._schedule_list) == N, "Update blocks have cyclic dependencies."

    # Maybe we can find some lightweight multi-threading library
    # Perform work partitioning to basically extract batches of frontiers
    # for parallelism

    InDeg = [0] * N
    for x in edges:
      for y in x:
        InDeg[y] += 1

    Q = deque()
    for i in xrange(N):
      if InDeg[i] == 0:
        Q.append( i )

    s._batch_schedule = []

    while Q:
      Q2 = deque()
      s._batch_schedule.append( [ s._blkid_upblk[ upblks[y] ] for y in Q ] )
      for u in Q:
        for v in edges[u]:
          InDeg[v] -= 1
          if InDeg[v] == 0:
            Q2.append( v )
      Q = Q2

  def elaborate( s ):
    s._elaborate()
    s._synthesize_constraints()
    s._schedule()

  def cycle( s ):
    for blk in s._schedule_list:
      blk()

  def print_schedule( s ):
    assert hasattr( s, "_schedule_list"), "Please elaborate before you print schedule!"
    print
    for (i, blk) in enumerate( s._schedule_list ):
      print i, blk.__name__
    for x in s._batch_schedule:
      print [ y.__name__ for y in x ]
