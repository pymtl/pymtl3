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
from UpdatesCall     import UpdatesCall
from ASTHelper       import get_method_calls, get_ast
from ConstraintTypes import U, M

class MethodsExpl( UpdatesCall ):

  # Override
  def __new__( cls, *args, **kwargs ):
    inst = super( MethodsExpl, cls ).__new__( cls, *args, **kwargs )

    # These will be collected recursively
    inst._method_blks    = defaultdict(list)
    inst._method_caller = {}
    inst._partial_constraints = set() # contains ( func, func )s

    # These are only processed at the current level
    inst._blkid_methods = defaultdict(list)
    inst._method_methods = defaultdict(list)

    if not "_method_ast" in cls.__dict__:
      cls._method_ast = {}

    for name in dir(cls):
      if name not in dir(MethodsExpl) and not name.startswith("_"):
        method = getattr( inst, name )
        if callable(method):
          setattr( inst, name, method ) # attach bounded method to instance

          if name not in cls._method_ast:
            cls._method_ast[ name ] = get_ast( method )

          get_method_calls( cls._method_ast[ name ], method, \
                            inst._method_methods[ name ] )

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

    # Find s.x[0][*][2]
    def expand_array_index( obj, name_depth, name, idx_depth, idx, id_blks, id_obj, blk_id ):
      if idx_depth >= len(idx):
        lookup_method( obj, name_depth+1, name, id_blks, id_obj, blk_id )
        return

      # assert isinstance( obj, list ) or isinstance( obj, deque ), "%s is %s, not a list" % (field, type(obj))

      if isinstance( idx[idx_depth], int ): # handle x[2]'s case
        assert idx[idx_depth] < len(obj), "Index out of bound. Check the declaration of %s" % (".".join([ x[0]+"".join(["[%s]"%str(y) for y in x[1]]) for x in name]))
        expand_array_index( obj[ idx[idx_depth] ], name_depth, name, idx_depth+1, idx, id_blks, id_obj, blk_id )
      elif idx[idx_depth] == "*":
        for i in xrange(len(obj)):
          expand_array_index( obj[i], name_depth, name, idx_depth+1, idx, id_blks, id_obj, blk_id )
      else:
        return False

    # Add an array of objects, s.x = [ [ A() for _ in xrange(2) ] for _ in xrange(3) ]
    def add_all( obj, name, id_blks, id_obj, blk_id ):
      if callable( obj ):
        id_blks[ id(obj) ].add( blk_id )
        id_obj [ id(obj) ] = obj

        if verbose:
          print " - method", name, "()", hex(id(obj)),
          if blk_id in s._blkid_upblk:
            print "in blk:", hex(blk_id), s._blkid_upblk[blk_id].__name__
          else:
            print "in method:", hex(id(obj))
        return
      if isinstance( obj, list ) or isinstance( obj, deque ):
        for i in xrange(len(obj)):
          add_all( obj[i], id_blks, id_obj, blk_id )

    # Find the object s.a.b.c, if c is c[] then jump to expand_array_index
    def lookup_method( obj, depth, name, id_blks, id_obj, blk_id ):
      if depth >= len(name):
        if callable( obj ):
          add_all( obj, name, id_blks, id_obj, blk_id ) # if this object is a list/array again...
        return

      (field, idx) = name[ depth ]

      # We don't throw assertion when nonexistent methods are called
      # -- instantiate different components based on parameter

      if not hasattr( obj, field ): return
      obj = getattr( obj, field )

      if not idx: # just a variable
        lookup_method( obj, depth+1, name, id_blks, id_obj, blk_id )
      else: # let another function handle   s.x[4].y[*]
        # assert isinstance( obj, list ) or isinstance( obj, deque ), "%s is %s, not a list" % (field, type(obj))
        expand_array_index( obj, depth, name, 0, idx, id_blks, id_obj, blk_id )

    # First check and bind update blocks that calls the method to it

    method_blks   = defaultdict(set)
    method_caller = defaultdict(set)
    id_obj        = {}

    for blk_id, method_calls in s._blkid_methods.iteritems():
      for method in method_calls:
        lookup_method( s, 0, method, method_blks, id_obj, blk_id )
    for i in method_blks:
      s._method_blks[i].extend( list( method_blks[i] ) )

    # Then check which method calls what other methods

    for method_name, method_calls in s._method_methods.iteritems():
      method_id = id( getattr( s, method_name ) )
      for method in method_calls:
        lookup_method( s, 0, method, method_caller, id_obj, method_id )

    for method_id, caller in method_caller.iteritems():
      assert len(caller) == 1
      s._method_caller[method_id] = list(caller)[0]

    s._id_obj.update( id_obj )

  def _synthesize_partial_constraints( s ):

    # If a method calls another method, they share the same constraint.

    temp_dependency = set()

    for (x,y) in s._partial_constraints:

      if id(x) not in s._blkid_upblk: # x is a method, find all methods that call x
        u = id(x)
        assert u in s._id_obj, "%s has method-method constraint, but the method is not called anywhere." % (x.full_name())
        while True:
          temp_dependency.add( (s._id_obj[u], y) )
          if u not in s._method_caller:
            break
          u = s._method_caller[u]

      if id(y) not in s._blkid_upblk: # y is a method, find all methods that call y
        u = id(y)
        assert u in s._id_obj, "%s has method-method constraint, but the method is not called anywhere." % (y.full_name())
        while True:
          temp_dependency.add( (x, s._id_obj[u]) )
          if u not in s._method_caller:
            break
          u = s._method_caller[u]

    s._partial_constraints = temp_dependency

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

            else:
              if v in method_blks:
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

            else:
              if v in method_blks:
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
      for k in child._method_caller:
        assert k not in s._method_caller, "Each method should only be called in one place"
        s._method_caller[k] = child._method_caller[k]

      s._partial_constraints |= child._partial_constraints

  # Override
  def _synthesize_constraints( s ):
    s._synthesize_partial_constraints()
    super( MethodsExpl, s )._synthesize_constraints()
