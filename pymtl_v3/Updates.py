import re, inspect, ast
p = re.compile('( *(@|def))')
from collections import defaultdict, deque

class TS:
  def __init__( self, func ):
    self.func = func
  def __lt__( self, other ):
    return (self.func, other.func)
  def __gt__( self, other ):
    return (other.func, self.func)

class Updates( object ):

  def __new__( cls, *args, **kwargs ):
    inst = object.__new__( cls, *args, **kwargs )
    inst._blkid_upblk = {}
    inst._constraints = []
    inst._upblks = []
    inst._schedule_list = []
    return inst

  def update( s, blk ):
    s._blkid_upblk[ id(blk) ] = blk
    s._upblks.append( blk )
    s.__dict__[ blk.__name__ ] = blk
    return blk

  def set_constraints( s, *args ):
    s._constraints.extend( [ x for x in args ] )

  def _elaborate( s, model ):

    for name, obj in model.__dict__.iteritems():
      if   isinstance( obj, Updates ):
        s._elaborate( obj )

        model._blkid_upblk.update( obj._blkid_upblk )
        model._upblks.extend( obj._upblks )
        print obj._blkid_upblk

  def _schedule( s ):

    N = len( s._upblks )
    edges = [ [] for _ in xrange(N) ] 
    InDeg = [ 0  for _ in xrange(N) ]
    Q     = deque()

    # Discretize in O(NlogN), to avoid later O(logN) lookup

    id_vtx = dict()
    for i in xrange(N):
      id_vtx[ id(s._upblks[i]) ] = i

    # Prepare the graph

    for (x, y) in s._constraints:
      vtx_x = id_vtx[ id(x) ]
      vtx_y = id_vtx[ id(y) ]
      edges[ vtx_x ].append( vtx_y )
      InDeg[ vtx_y ] += 1

    # Perform topological sort in O(N+M)

    for i in xrange(N):
      if InDeg[i] == 0:
        Q.append( i )

    while Q:
      u = Q.popleft()
      s._schedule_list.append( s._upblks[u] )
      for v in edges[u]:
        InDeg[v] -= 1
        if InDeg[v] == 0:
          Q.append( v )

  def elaborate( s ):
    s._elaborate( s )
    s._schedule()

  def cycle( s ):
    for blk in s._schedule_list:
      blk()

  def print_schedule( s ):
    for blk in s._schedule_list:
      print blk.__name__
