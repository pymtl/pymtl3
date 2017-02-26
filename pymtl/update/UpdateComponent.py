#=========================================================================
# UpdateComponent.py
#=========================================================================
# At the bottom level, we only have update blocks and "total constraint"s.
# Each update block is called exactly once every cycle. PyMTL will
# schedule all update blocks based on the constraints. A total constraint
# between two update blocks specifies the order of the two blocks, i.e.
# who is called before whom.

from collections import defaultdict, deque

class U(object): # update block wrapper
  def __init__( self, func ):
    self.func = func
  def __lt__( self, other ):
    return (self, other)
  def __gt__( self, other ):
    return (other, self)
  def __call__( self ):
    self.func()

class UpdateComponent( object ):

  def __new__( cls, *args, **kwargs ):
    inst = object.__new__( cls, *args, **kwargs )
    inst._blkid_upblk = {}
    inst._name_upblk = {}
    inst._upblks = []

    inst._total_constraints = set() # contains ( id(func), id(func) )s
    inst._schedule_list = []
    return inst

  def update( s, blk ):
    if blk.__name__ in s._name_upblk:
      raise Exception("Cannot declare two update blocks using the same name!")

    s._blkid_upblk[ id(blk) ] = blk
    s._name_upblk[ blk.__name__ ] = blk
    s._upblks.append( blk )
    return blk

  def get_update_block( s, name ):
    return s._name_upblk[ name ]

  def add_constraints( s, *args ):
    for x in args:
      s._total_constraints.add( (id(x[0].func), id(x[1].func)) )

  def _recursive_collect( s, model ):

    for name, obj in model.__dict__.iteritems():
      if   isinstance( obj, UpdateComponent ):
        s._recursive_collect( obj )

        model._blkid_upblk.update( obj._blkid_upblk )
        model._upblks.extend( obj._upblks )

  def _schedule( s ):

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
    s._recursive_collect( s )
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
