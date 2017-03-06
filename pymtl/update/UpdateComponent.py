#=========================================================================
# UpdateComponent.py
#=========================================================================
# At the bottom level, we only have update blocks and "total constraint"s.
# Each update block is called exactly once every cycle. PyMTL will
# schedule all update blocks based on the constraints. A total constraint
# between two update blocks specifies the order of the two blocks, i.e.
# who is called before whom.

import re, inspect, ast, random, copy
p = re.compile('( *(@|def))')
from collections import defaultdict, deque

class _int(int): pass # subclass int for different ids

class U(object): # update block wrapper
  def __init__( self, func ):
    self.func = func
  def __lt__( self, other ):
    return (self, other)
  def __gt__( self, other ):
    return (other, self)
  def __call__( self ):
    self.func()

class DetectLoadsAndStores( ast.NodeVisitor ):

  def __init__( self ):
    self.load = []
    self.store = []

  def enter( self, node, load, store ):
    self.visit( node )
    load.extend ( self.load )
    store.extend( self.store )

  def get_full_name( self, node ):
    obj_name = []
    while hasattr( node, "value" ): # don't record the last "s."
      if isinstance( node, ast.Attribute ):
        obj_name.append( node.attr )
      else:
        assert isinstance( node, ast.Subscript )
      node = node.value
    return obj_name[::-1]

  def visit_Attribute( self, node ): # s.a.b
    obj_name = self.get_full_name( node )

    if   isinstance( node.ctx, ast.Load ):
      self.load  += [ obj_name ]
    elif isinstance( node.ctx, ast.Store ):
      self.store += [ obj_name ]
    else:
      assert False, type( node.ctx )

  def visit_Subscript( self, node ): # s.a.b[0:3] ld/st is in subscript
    obj_name = self.get_full_name( node )

    if   isinstance( node.ctx, ast.Load ):
      self.load  += [ obj_name ]
    elif isinstance( node.ctx, ast.Store ):
      self.store += [ obj_name ]
    else:
      assert False, type( node.ctx )

class UpdateComponent( object ):

  def __new__( cls, *args, **kwargs ):
    inst = super(UpdateComponent, cls).__new__( cls, *args, **kwargs )

    inst._name_upblk = {}
    inst._blkid_upblk = {}
    inst._blkid_loads = defaultdict(list)
    inst._blkid_stores = defaultdict(list)

    inst._load_blks = defaultdict(list)
    inst._store_blks = defaultdict(list)

    inst._impl_constraints = set() # contains ( id(func), id(func) )s
    inst._expl_constraints = set() # contains ( id(func), id(func) )s
    inst._schedule_list = []
    return inst

  def update( s, blk ):
    if blk.__name__ in s._name_upblk:
      raise Exception("Cannot declare two update blocks using the same name!")

    blk_id = id(blk)
    s._name_upblk[ blk.__name__ ] = s._blkid_upblk[ blk_id ] = blk

    # I store the ast of each update block to parse method calls. To also
    # cache them across different instances of the same class, I attach
    # the information to the class object.

    if not "_blkid_ast" in type(s).__dict__:
      type(s)._blkid_ast = dict()

    if blk_id not in type(s)._blkid_ast:
      src = p.sub( r'\2', inspect.getsource( blk ) )
      type(s)._blkid_ast[ blk_id ] = ast.parse( src )

    # Traverse the ast to extract variable writes and reads
    # First check and remove @s.update and empty arguments

    tree = type(s)._blkid_ast[ blk_id ]
    assert isinstance(tree, ast.Module)
    tree = tree.body[0]
    assert isinstance(tree, ast.FunctionDef)

    for stmt in tree.body:
      DetectLoadsAndStores().enter(
        stmt, s._blkid_loads[ blk_id ], s._blkid_stores[ blk_id ] )
    return blk

  def get_update_block( s, name ):
    return s._name_upblk[ name ]

  def add_constraints( s, *args ):
    s._expl_constraints.update([ (id(x[0].func), id(x[1].func)) for x in args ])

  def _elaborate_vars( s ):

    # First check if each load/store variable exists, then bind the actual
    # variable id (not name anymore) to upblks that reads/writes it.

    load_blks  = defaultdict(set)
    store_blks = defaultdict(set)

    for blk_id, loads in s._blkid_loads.iteritems():
      for load_name in loads:
        obj = s
        for field in load_name:
          assert hasattr( obj, field ), "\"%s\", in %s, is not a field of class %s" \
                 %(field, s._blkid_upblk[blk_id].__name__, type(obj).__name__)
          obj = getattr( obj, field )

        if not callable(obj): # exclude function calls
          # print " - load",load_name, type(obj), id(obj)
          load_blks[ id(obj) ].add( blk_id )

    for blk_id, stores in s._blkid_stores.iteritems():
      for store_name in stores:
        obj = s
        for field in store_name:
          assert hasattr( obj, field ), "\"%s\", in %s, is not a field of class %s" \
                 %(field, s._blkid_upblk[blk_id].__name__, type(obj).__name__)
          obj = getattr( obj, field )

        if not callable(obj): # exclude function calls
          # print " - store",store_name, type(obj), id(obj)
          store_blks[ id(obj) ].add( blk_id )

    # Turn associated sets into lists, as blk_id are now unique.
    # O(logn) -> O(1)

    for i in load_blks:
      s._load_blks[i].extend( list( load_blks[i] ) )

    for i in store_blks:
      s._store_blks[i].extend( list( store_blks[i] ) )

  def _synthesize_impl_constraints( s ):

    # Synthesize total constraints between two upblks that read/write to
    # the same variable. This is done after the recursive elaboration

    load_blks  = s._load_blks
    store_blks = s._store_blks

    for load, ld_blks in load_blks.iteritems():
      st_blks = store_blks[ load ] # stores to the same variable
      for st in st_blks:
        for ld in ld_blks:
          if st != ld:
            s._impl_constraints.add( (st, ld) ) # wr < rd by default

    for store, st_blks in store_blks.iteritems():
      ld_blks = load_blks[ store ]
      for st in st_blks:
        for ld in ld_blks:
          if st != ld:
            s._impl_constraints.add( (st, ld) ) # wr < rd by default

  def _collect_child_vars( s, child ):
    s._blkid_upblk.update( child._blkid_upblk )
    s._impl_constraints.update( child._impl_constraints )
    s._expl_constraints.update( child._expl_constraints )

    for k in child._load_blks:
      s._load_blks[k].extend( child._load_blks[k] )
    for k in child._store_blks:
      s._store_blks[k].extend( child._store_blks[k] )

  def _synthesize_constraints( s ):
    s._synthesize_impl_constraints()

  def _recursive_elaborate( s ):

    for name, obj in s.__dict__.iteritems():
      if not name.startswith("_"): # filter private variables

        if   isinstance( obj, int ): # to create unique id for int
          s.__dict__[ name ] = _int(obj)

        elif isinstance( obj, UpdateComponent ):
          obj._recursive_elaborate()
          s._collect_child_vars( obj )

    s._elaborate_vars()

  def _schedule( s ):

    s._total_constraints = s._expl_constraints.copy()

    for (x, y) in s._impl_constraints:
      print s._blkid_upblk[x].__name__.center(25)," (<) ", s._blkid_upblk[y].__name__.center(25)

    for (x, y) in s._expl_constraints:
      print s._blkid_upblk[x].__name__.center(25),"  <  ", s._blkid_upblk[y].__name__.center(25)

    for (x, y) in s._impl_constraints:
      if (y, x) not in s._expl_constraints: # no conflicting expl
        s._total_constraints.add( (x, y) )

      if (x, y) in s._expl_constraints or (y, x) in s._expl_constraints:
        print "implicit constraint is overriden -- ",s._blkid_upblk[x].__name__, " (<) ", \
               s._blkid_upblk[y].__name__

    s._total_constraints = list(s._total_constraints)

    # from graphviz import Digraph
    # dot = Digraph(comment = s.__class__)
    # dot.graph_attr["rank"] = "source"
    # dot.graph_attr["ratio"] = "fill"
    # dot.graph_attr["margin"] = "0.1"
    # for (x, y) in s._total_constraints:
      # dot.edge( s._blkid_upblk[x].__name__+"@"+hex(x), s._blkid_upblk[y].__name__+"@"+hex(y) )
      # dot.render("/tmp/pymtl.gv", view=True)

    N = len( s._blkid_upblk )
    edges = [ [] for _ in xrange(N) ]
    upblks = s._blkid_upblk.keys()
    InDeg = [0] * N

    # Discretize in O(NlogN), to avoid later O(logN) lookup

    id_vtx = dict()
    for i in xrange(N):
      id_vtx[ upblks[i] ] = i

    # Prepare the graph

    for (x, y) in s._total_constraints:
      vtx_x = id_vtx[ x ]
      vtx_y = id_vtx[ y ]
      edges[ vtx_x ].append( vtx_y )
      InDeg[ vtx_y ] += 1

    # Perform topological sort in O(N+M). Note that this gives us a linear
    # schedule.

    Q = deque()
    for i in xrange(N):
      if InDeg[i] == 0:
        Q.append( i )

    while Q:
      random.shuffle(Q) # to catch corner cases; will be removed later

      u = Q.popleft()
      s._schedule_list.append( s._blkid_upblk[ upblks[u] ] )
      for v in edges[u]:
        InDeg[v] -= 1
        if InDeg[v] == 0:
          Q.append( v )

    if len(s._schedule_list) < N:
      raise Exception("Update blocks have cyclic dependencies.")

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
    for blk in s._schedule_list:
      blk()

  def print_schedule( s ):
    print
    for blk in s._schedule_list:
      print blk.__name__
    for x in s._batch_schedule:
      print [ y.__name__ for y in x ]
