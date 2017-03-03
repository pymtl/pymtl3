#=========================================================================
# UpdateComponent.py
#=========================================================================
# At the bottom level, we only have update blocks and "total constraint"s.
# Each update block is called exactly once every cycle. PyMTL will
# schedule all update blocks based on the constraints. A total constraint
# between two update blocks specifies the order of the two blocks, i.e.
# who is called before whom.

import re, inspect, ast
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
    t = node
    while hasattr( t, "value" ): # don't record the last "s."
      if isinstance( t, ast.Attribute ):
        obj_name.append( t.attr )
      else:
        assert isinstance( t, ast.Subscript )
      t = t.value

    obj_name.reverse()
    return obj_name

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
    inst = object.__new__( cls, *args, **kwargs )
    inst._upblks = []
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
    s._upblks.append( blk )
    s._name_upblk[ blk.__name__ ] = blk
    s._blkid_upblk[ blk_id ] = blk

    # I store the ast of each update block to parse method calls. To also
    # cache them across different instances of the same class, I attach
    # the information to the class object.

    if not "_blkid_ast" in type(s).__dict__:
      type(s)._blkid_ast = dict()

    if blk_id not in type(s)._blkid_ast:
      src = p.sub( r'\2', inspect.getsource( blk ) )
      type(s)._blkid_ast[ blk_id ] = ast.parse( src )

    # Parse the ast to extract variable writes and reads
    # First check if it's a valid AST and remove the @s.update and empty
    # arguments

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
    for x in args:
      # print "hard constraint",
      s._expl_constraints.add( (id(x[0].func), id(x[1].func)) )

  def _synthesize_impl_constraints( s, model ):

    # First check if each load/store variable exists, then bind update
    # blocks that reads/writes the variable to the variable

    load_blks  = defaultdict(set)
    store_blks = defaultdict(set)

    for blk_id, loads in model._blkid_loads.iteritems():
      for load_name in loads:
        obj = model
        for field in load_name:
          assert hasattr( obj, field ), "\"%s\" is not a field of class %s"%(field, type(obj).__name__)
          obj = getattr( obj, field )

        if not callable(obj): # exclude function calls
          print " - load",load_name, type(obj), id(obj)
          load_blks[ id(obj) ].add( blk_id )

    for blk_id, stores in model._blkid_stores.iteritems():
      for store_name in stores:
        obj = model
        for field in store_name:
          assert hasattr( obj, field ), "\"%s\" is not a field of class %s"%(field, type(obj).__name__)
          obj = getattr( obj, field )

        if not callable(obj): # exclude function calls
          print " - store",store_name, type(obj), id(obj)
          store_blks[ id(obj) ].add( blk_id )

    # Turn associated sets into lists, as blk_id are now unique.
    # O(logn) -> O(1)

    # Synthesize total constraints between two upblks that read/write to
    # the same variable. Note that one side of the new constraint comes
    # only from variables called at the current level to avoid redundant
    # scans, but the other side is from all recursively collected vars
    # plus those called the current level.

    for i in load_blks:
      m = load_blks[i] = list( load_blks[i] )
      model._load_blks[i].extend( m )

    for i in store_blks:
      m = store_blks[i] = list( store_blks[i] )
      model._store_blks[i].extend( m )

    for load, ld_blks in load_blks.iteritems():# called at current level
      st_blks = model._store_blks[ load ] # matching stores
      for st in st_blks:
        for ld in ld_blks:
          if st != ld:
            # print "local ld < all st",
            model._impl_constraints.add( (st, ld) ) # wr < rd by default

    for store, st_blks in store_blks.iteritems():# called at current level
      ld_blks = model._load_blks[ store ]
      for st in st_blks:
        for ld in ld_blks:
          if st != ld:
            # print "local st < all ld",
            model._impl_constraints.add( (st, ld) ) # wr < rd by default

  def _recursive_elaborate( s, model ):

    for name, obj in model.__dict__.iteritems():
      if   isinstance( obj, int ): # to create unique id for int
        model.__dict__[ name ] = _int(obj)

      elif isinstance( obj, UpdateComponent ):
        s._recursive_elaborate( obj )

        model._upblks.extend( obj._upblks )
        model._name_upblk.update( obj._name_upblk )
        model._blkid_upblk.update( obj._blkid_upblk )

        model._impl_constraints.update( obj._impl_constraints )
        model._expl_constraints.update( obj._expl_constraints )

        for k in obj._load_blks:
          model._load_blks[k].extend( obj._load_blks[k] )
        for k in obj._store_blks:
          model._store_blks[k].extend( obj._store_blks[k] )

    s._synthesize_impl_constraints( model )

  def _schedule( s ):

    s._total_constraints = s._expl_constraints.copy()

    for (x, y) in s._impl_constraints:
      print s._blkid_upblk[x].__name__," (<) ", s._blkid_upblk[y].__name__

    for (x, y) in s._expl_constraints:
      print s._blkid_upblk[x].__name__,"  <  ", s._blkid_upblk[y].__name__

    for (x, y) in s._impl_constraints:
      if (y, x) not in s._expl_constraints: # no conflicting expl
        s._total_constraints.add( (x, y) )

      if (x, y) in s._expl_constraints or (y, x) in s._expl_constraints:
        print "implicit constraint is overriden -- ",s._blkid_upblk[x].__name__, " (<) ", \
               s._blkid_upblk[y].__name__

    s._total_constraints = list(s._total_constraints)

    N = len( s._upblks )
    edges = [ [] for _ in xrange(N) ]

    # Discretize in O(NlogN), to avoid later O(logN) lookup

    id_vtx = dict()
    for i in xrange(N):
      id_vtx[ id(s._upblks[i]) ] = i

    # Prepare the graph

    for (x, y) in s._total_constraints:
      vtx_x = id_vtx[ x ]
      vtx_y = id_vtx[ y ]
      edges[ vtx_x ].append( vtx_y )

    # Perform topological sort in O(N+M)

    InDeg = [0] * N
    for x in edges:
      for y in x:
        InDeg[y] += 1

    Q = deque()
    for i in xrange(N):
      if InDeg[i] == 0:
        Q.append( i )

    while Q:
      import random
      random.shuffle(Q) # to catch corner cases; will be removed later

      u = Q.popleft()
      s._schedule_list.append( s._upblks[u] )
      for v in edges[u]:
        InDeg[v] -= 1
        if InDeg[v] == 0:
          Q.append( v )

    if len(s._schedule_list) < len(s._upblks):
      raise Exception("Update blocks have cyclic dependencies.")

  def elaborate( s ):
    s._recursive_elaborate( s )
    s._schedule()

  def cycle( s ):
    for blk in s._schedule_list:
      blk()

  def print_schedule( s ):
    print
    for (x, y) in s._total_constraints:
      print s._blkid_upblk[x].__name__," < ", s._blkid_upblk[y].__name__
    for blk in s._schedule_list:
      print blk.__name__
