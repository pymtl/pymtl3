#=========================================================================
# MethodsExpl.py
#=========================================================================
# At this level, we add methods, and partial constraints on top of update
# blocks, to improve productivity.
# Two update blocks communicate via methods of the same component.
# A partial constraint is specified between one update block and one
# method, or two methods. PyMTL will try to chain partial constraints to
# produce total constraints.
# We collect two types of constraints at this level as well:
# * Implicit binding: upA calls s.a.AA() upA = methodAA
# * Explicit constraint: 3 types, see below
#   - s.add_constraints( upA < upB, methodAA < upA, methodBB < methodAA )
# Explicit constraints will override implicit bindings.

from UpdatesExpl import verbose

from collections     import defaultdict, deque
from Updates         import Updates
from ASTHelper       import get_method_calls
from ConstraintTypes import U, M

class MethodsExpl( Updates ):

  # Override
  def __new__( cls, *args, **kwargs ):
    inst = super( MethodsExpl, cls ).__new__( cls, *args, **kwargs )

    for x in dir(cls):
      if x not in dir(MethodsExpl):
        y = getattr(inst, x)
        if callable(y):
          setattr( inst, x, y )

    # These will be collected recursively
    inst._method_blks = defaultdict(list)
    inst._partial_constraints = set() # contains ( func, func )s

    # These are only processed at the current level
    inst._blkid_methods = defaultdict(list)
    return inst

  # Override
  def update( s, blk ):
    super( MethodsExpl, s ).update( blk )
    get_method_calls( type(s)._blkid_ast[ blk.__name__ ], blk, \
                      s._blkid_methods[ id(blk) ] )
    return blk

  # Override
  def update_on_edge( s, blk ):
    super( MethodsExpl, s ).update_on_edge( blk )
    get_method_calls( type(s)._blkid_ast[ blk.__name__ ], blk, \
                      s._blkid_methods[ id(blk) ] )
    return blk

  # Override
  def add_constraints( s, *args ):
    super( MethodsExpl, s ).add_constraints( *args ) # handle U-U, U-V, V-V

    for (x0, x1) in args:
      # Keep partial constraints x0 < x1 for later synthesis
      if isinstance( x0, M ) or isinstance( x1, M ):
        f0, f1 = x0.func, x1.func
        s._partial_constraints.add( (f0, f1) )

        if verbose: print hex(id(f0)), "p<",hex(id(f1))

  # Override
  def _elaborate_vars( s ):
    super( MethodsExpl, s )._elaborate_vars()

    def add_all( typ, depth, obj, name, method_name, method_blks, blk_id ): # We need this to deal with s.a[*].b[*]
      if depth >= len(name):

        assert hasattr( obj, method_name ), "\"%s\", in %s, is not a method of class %s" \
               %(method_name, s._blkid_upblk[blk_id].__name__, type(obj).__name__)
        method = getattr( obj, method_name )
        assert callable( method ), "\"%s\" is not callable %s"%(method_name, type(obj).__name__)

        if verbose: print " - ", name, method_name,"()", hex(id(method)), "in blk:", hex(blk_id), s._blkid_upblk[blk_id].__name__

        method_blks[ id(method) ].add( blk_id )
        return

      (field, idx) = name[ depth ]
      assert hasattr( obj, field ), "\"%s\", in %s, is not a field of class %s" \
             %(field, s._blkid_upblk[blk_id].__name__, type(obj).__name__)

      obj = getattr( obj, field )
      if   idx == "x":
        add_all( typ, depth+1, obj, name, method_name, method_blks, blk_id )
      elif isinstance( idx, int ):
        assert isinstance( obj, list ) or isinstance( obj, deque ), "%s is %s, not a list" % (field, type(obj))
        add_all( typ, depth+1, obj[idx], name, method_name, method_blks, blk_id )
      else:
        assert idx == "*", "idk"
        assert isinstance( obj, list ), "%s is not a list" % field
        for x in obj:
          add_all( typ, depth+1, x, name, method_name, method_blks, blk_id )

    # First check and bind update blocks that calls the method to it
    # This method elaborates the variables for implicit binding

    method_blks = defaultdict(set)

    for blk_id, method_calls in s._blkid_methods.iteritems():
      for method in method_calls:
        add_all( "method", 0, s, method[0], method[1], method_blks, blk_id )

    # Turn associated sets into lists. O(logn) -> O(1)

    for i in method_blks:
      s._method_blks[i].extend( list( method_blks[i] ) )

  def _synthesize_partial_constraints( s ):

    # Do bfs to find out all potential total constraints associated with
    # each method, direction conflicts, and incomplete constraints

    pred = defaultdict(set)
    succ = defaultdict(set)
    for (x, y) in s._partial_constraints:
      pred[id(y)].add( id(x) )
      succ[id(x)].add( id(y) )

    method_blks = s._method_blks

    for method_id in method_blks:
      assoc_blks = method_blks[ method_id ]
      Q = deque( [ (method_id, 0) ] ) # -1: pred, 0: don't know, 1: succ
      if verbose: print
      while Q:
        (u, w) = Q.popleft()
        if verbose: print (hex(u), w)

        if w <= 0:
          for v in pred[u]:

            if v in s._blkid_upblk:
              # Find total constraint (v < blk) by v < method_u < method_u'=blk
              # INVALID if we have explicit constraint (blk < method_u)

              for blk in assoc_blks:
                if blk not in pred[u]:
                  if v != blk:
                    if verbose: print "w<=0, v is blk".center(10),hex(v), hex(blk)
                    if verbose: print s._blkid_upblk[v].__name__.center(25)," < ", \
                                s._blkid_upblk[blk].__name__.center(25)
                    s._expl_constraints.add( (v, blk) )

            elif v in method_blks:
              # assert v in method_blks, "Incomplete elaboration, something is wrong! %s" % hex(v)
              # TODO Now I'm leaving incomplete dependency chain because I didn't close the circuit loop.
              # E.g. I do port.wr() somewhere in __main__ to write to a port.

              # Find total constraint (vb < blk) by vb=method_v < method_u=blk
              # INVALID if we have explicit constraint (blk < method_v) or (method_u < vb)

              v_blks = method_blks[ v ]
              for vb in v_blks:
                if vb not in succ[u]:
                  for blk in assoc_blks:
                    if blk not in pred[v]:
                      if vb != blk:
                        if verbose: print "w<=0, v is method".center(10),hex(v), hex(blk) 
                        if verbose: print s._blkid_upblk[vb].__name__.center(25)," < ", \
                                    s._blkid_upblk[blk].__name__.center(25)
                        s._expl_constraints.add( (vb, blk) )

              Q.append( (v, -1) ) # ? < v < u < ... < method < blk_id

        if w >= 0:
          for v in succ[u]:

            if v in s._blkid_upblk:
              # Find total constraint (blk < v) by blk=method_u' < method_u < v
              # INVALID if we have explicit constraint (method_u < blk)

              for blk in assoc_blks:
                if blk not in succ[u]:
                  if v != blk:
                    if verbose: print "w>=0, v is blk".center(10),hex(blk), hex(v)
                    if verbose: print s._blkid_upblk[blk].__name__.center(25)," < ", \
                                s._blkid_upblk[v].__name__.center(25)
                    s._expl_constraints.add( (blk, v) )

            elif v in method_blks:
              # assert v in method_blks, "Incomplete elaboration, something is wrong! %s" % hex(v)
              # TODO Now I'm leaving incomplete dependency chain because I didn't close the circuit loop.
              # E.g. I do port.wr() somewhere in __main__ to write to a port.

              # Find total constraint (blk < vb) by blk=method_u < method_v=vb
              # INVALID if we have explicit constraint (vb < method_u) or (method_v < blk)

              v_blks = method_blks[ v ]
              for vb in v_blks:
                if not vb in pred[u]:
                  for blk in assoc_blks:
                    if not blk in succ[v]:
                      if vb != blk:
                        if verbose: print "w>=0, v is method".center(10),hex(blk), hex(v)
                        if verbose: print s._blkid_upblk[blk].__name__.center(25)," < ", \
                                    s._blkid_upblk[vb].__name__.center(25)
                        s._expl_constraints.add( (blk, vb) )

              Q.append( (v, 1) ) # blk_id < method < ... < u < v < ?

  # Override
  def _collect_child_vars( s, child ):
    super( MethodsExpl, s )._collect_child_vars( child )

    if   isinstance( child, MethodsExpl ):
      for k in child._method_blks:
        s._method_blks[k].extend( child._method_blks[k] )
      s._partial_constraints |= child._partial_constraints

  # Override
  def _synthesize_constraints( s ):
    s._synthesize_partial_constraints()
    super( MethodsExpl, s )._synthesize_constraints()
