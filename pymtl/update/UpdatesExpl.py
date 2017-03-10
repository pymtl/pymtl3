#=========================================================================
# UpdatesExpl.py
#=========================================================================
# At the bottom level, we only have update blocks and explicit constraints
# between two update blocks/one update block and the read/write of a
# python variable.
# Each update block is called exactly once every cycle. PyMTL will
# schedule all update blocks based on the constraints. A total constraint
# between two update blocks specifies the order of the two blocks, i.e.
# call A before B.
# We collect two types of explicit constraints at this level:
# * Block constraint: s.add_constraints( U(upA) < U(upB) )
# * Value constraint: s.add_constraints( U(upA) < RD(s.x) )

verbose = False
# verbose = True

import random
from collections     import defaultdict, deque
from ASTHelper       import get_ast, get_read_write, DetectReadsAndWrites
from ConstraintTypes import _int, U, RD, WR

class UpdatesExpl( object ):

  def __new__( cls, *args, **kwargs ):
    inst = super(UpdatesExpl, cls).__new__( cls, *args, **kwargs )

    # These will be collected recursively
    inst._name_upblk       = {}
    inst._blkid_upblk      = {}
    inst._read_blks        = defaultdict(list)
    inst._write_blks       = defaultdict(list)
    inst._expl_constraints = set() # contains ( id(func), id(func) )s
    inst._var_constraints  = set()

    # These are only processed at the current level
    inst._blkid_reads  = defaultdict(list)
    inst._blkid_writes = defaultdict(list)
    return inst

  def update( s, blk ):
    assert blk.__name__ not in s._name_upblk, ("Cannot declare two update blocks using the same name!")

    blk_id = id(blk)
    s._name_upblk[ blk.__name__ ] = s._blkid_upblk[ blk_id ] = blk

    # I write the asts of upblks. To also cache them across different
    # instances of the same class, I attach them to the class object.

    if not "_blkid_ast" in type(s).__dict__:
      type(s)._blkid_ast = dict()
    if blk_id not in type(s)._blkid_ast:
      type(s)._blkid_ast[ blk_id ] = get_ast( blk )

    get_read_write( type(s)._blkid_ast[ blk_id ], \
                    s._blkid_reads[ blk_id ], s._blkid_writes[ blk_id ] )
    return blk

  def get_update_block( s, name ):
    return s._name_upblk[ name ]

  def add_constraints( s, *args ):

    for (x0, x1) in args:
      if isinstance( x0, U ) and isinstance( x1, U ):
        s._expl_constraints.add( (id(x0.func), id(x1.func)) )
      # TODO, add U(up) < RD(s.x)


  def _elaborate_vars( s ):

    # First check if each read/write variable exists, then bind the actual
    # variable id (not name anymore) to upblks that reads/writes it.

    read_blks  = defaultdict(set)
    write_blks = defaultdict(set)

    for blk_id, reads in s._blkid_reads.iteritems():
      for read_name in reads:
        obj = s
        for field in read_name:
          assert hasattr( obj, field ), "\"%s\", in %s, is not a field of class %s" \
                 %(field, s._blkid_upblk[blk_id].__name__, type(obj).__name__)
          obj = getattr( obj, field )

        if not callable(obj): # exclude function calls
          if verbose: print " - read",read_name, type(obj), hex(id(obj)), "in blk:", hex(blk_id), s._blkid_upblk[blk_id].__name__
          read_blks[ id(obj) ].add( blk_id )

    for blk_id, writes in s._blkid_writes.iteritems():
      for write_name in writes:
        obj = s
        for field in write_name:
          assert hasattr( obj, field ), "\"%s\", in %s, is not a field of class %s" \
                 %(field, s._blkid_upblk[blk_id].__name__, type(obj).__name__)
          obj = getattr( obj, field )

        if not callable(obj): # exclude function calls
          if verbose: print " - write",write_name, type(obj), hex(id(obj)), "in blk:", hex(blk_id), s._blkid_upblk[blk_id].__name__
          write_blks[ id(obj) ].add( blk_id )

    # Turn associated sets into lists, as blk_id are now unique.
    # O(logn) -> O(1)

    for i in read_blks:
      s._read_blks[i].extend( list( read_blks[i] ) )

    for i in write_blks:
      s._write_blks[i].extend( list( write_blks[i] ) )

  def _collect_child_vars( s, child ):

    if isinstance( child, UpdatesExpl ):
      s._blkid_upblk.update( child._blkid_upblk )
      s._expl_constraints.update( child._expl_constraints )

      for k in child._read_blks:
        s._read_blks[k].extend( child._read_blks[k] )
      for k in child._write_blks:
        s._write_blks[k].extend( child._write_blks[k] )

  def _synthesize_constraints( s ):

    s._total_constraints = list( s._expl_constraints.copy() )

    if verbose:
      for (x, y) in s._expl_constraints:
        print s._blkid_upblk[x].__name__.center(25),"  <  ", s._blkid_upblk[y].__name__.center(25)

  def _recursive_elaborate( s ):

    for name, obj in s.__dict__.iteritems():
      if not name.startswith("_"): # filter private variables

        if   isinstance( obj, int ): # to create unique id for int
          s.__dict__[ name ] = _int(obj)
        elif isinstance( obj, UpdatesExpl ):
          obj._recursive_elaborate()

        s._collect_child_vars( obj )

    s._elaborate_vars()

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

    for (x, y) in s._total_constraints:
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
      random.shuffle(Q) # to catch corner cases; will be removed later

      u = Q.popleft()
      s._schedule_list.append( s._blkid_upblk[ upblks[u] ] )
      for v in edges[u]:
        InDeg[v] -= 1
        if InDeg[v] == 0:
          Q.append( v )

    assert len(s._schedule_list) == N, "Update blocks have cyclic dependencies."

    # TODO find some lightweight multi-threading library
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
    s._recursive_elaborate()
    s._synthesize_constraints()
    s._schedule()

  def cycle( s ):
    assert hasattr( s, "_schedule_list"), "Please elaborate before you tick cycle()!"
    for blk in s._schedule_list:
      blk()

  def print_schedule( s ):
    assert hasattr( s, "_schedule_list"), "Please elaborate before you print schedule!"
    print
    for blk in s._schedule_list:
      print blk.__name__
    for x in s._batch_schedule:
      print [ y.__name__ for y in x ]
