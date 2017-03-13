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

from collections     import defaultdict
from Updates         import Updates
from ASTHelper       import get_ast
from ConstraintTypes import U, M
from Connectable     import Method

class MethodsExpl( Updates ):

  def __new__( cls, *args, **kwargs ):
    inst = super( MethodsExpl, cls ).__new__( cls, *args, **kwargs )

    inst._blkid_methods = defaultdict(list)
    inst._method_blks   = defaultdict(list)

    inst._partial_constraints = set() # contains ( id(func), id(func) )s

    return inst

  # Override
  def update( s, blk ):
    super( MethodsExpl, s ).update( blk )

    blk_id = id(blk)
    tree = type(s)._blkid_ast[ blk_id ]

    # Walk the ast to extract method calls
    for node in ast.walk(tree):
      # Check if the node is a function call and the function name is not
      # not min,max,etc; it should be a component method call s.x.y.z()

      if isinstance( node, ast.Call ) and not isinstance( node.func, ast.Name ):

        t = node.func.value
        obj_name = []
        while hasattr( t, "value" ): # don't record the last "s."
          obj_name.append( t.attr )
          t = t.value

        obj_name.reverse()
        method_name = node.func.attr
        s._blkid_methods[ blk_id ].append( (obj_name, method_name) )

    return blk

  # Override
  def add_constraints( s, *args ):

    for (x0, x1) in args:

      # Two upblks! Forward total constraints to the final graph
      if isinstance( x0, U ) and isinstance( x1, U ):
        s._add_expl_constraints( id(x0.func), id(x1.func) )

      # Keep partial constraints for later synthesis
      # Store the method descriptor to host instance dictionary for unique id
      else:
        x = x0.func
        y = x1.func
        xobj = yobj = s

        if isinstance( x0, M ):
          xobj = x.__self__
          if not x.__name__  in xobj.__dict__:
            xobj.__dict__[ x.__name__ ] = x
          x = xobj.__dict__[ x.__name__ ]

        if isinstance( x1, M ):
          yobj = y.__self__
          if not y.__name__  in yobj.__dict__:
            yobj.__dict__[ y.__name__ ] = y
          y = yobj.__dict__[ y.__name__ ]

        # Partial constraints, x0 < x1
        xobj._partial_constraints.add( (id(x), id(y)) )
        yobj._partial_constraints.add( (id(x), id(y)) )

        if verbose: print hex(id(x)), "p<",hex(id(y))

  # Override
  def _elaborate_vars( s ):
    super( MethodsExpl, s )._elaborate_vars()

    # First check and bind update blocks that calls the method to it
    # This method elaborates the variables for implicit binding

    method_blks = defaultdict(set)

    for blk_id, method_calls in s._blkid_methods.iteritems():
      for (object_name, method_name) in method_calls:
        obj = s
        for field in object_name:
          assert hasattr( obj, field ), "\"%s\", in %s, is not a field of class %s" \
                 %(field, s._blkid_upblk[blk_id].__name__, type(obj).__name__)
          obj = getattr( obj, field )

        assert hasattr( obj, method_name ), "\"%s\", in %s, is not a method of class %s" \
               %(method_name, s._blkid_upblk[blk_id].__name__, type(obj).__name__)
        method = getattr( obj, method_name )
        assert callable( method ), "\"%s\" is not callable %s"%(method_name, type(obj).__name__)

        if verbose: print " - ", object_name, method_name,"()", hex(id(method)), "in blk:", hex(blk_id), s._blkid_upblk[blk_id].__name__

        method_blks[ id(method) ].add( blk_id )

    # Turn associated sets into lists. O(logn) -> O(1)

    for i in method_blks:
      s._method_blks[i].extend( list( method_blks[i] ) )

  def _synthesize_partial_constraints( s ):

    # Do bfs to find out all potential total constraints associated with
    # each method, direction conflicts, and incomplete constraints

    pred = defaultdict(set)
    succ = defaultdict(set)
    for (x, y) in s._partial_constraints:
      pred[y].add( x )
      succ[x].add( y )

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

    elif isinstance( child, Interface ):
      child._connect_to_root()

  # Override
  def _synthesize_constraints( s ):
    super( MethodsExpl, s )._synthesize_constraints()
    s._synthesize_partial_constraints()
