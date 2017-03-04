#=========================================================================
# MethodComponent.py
#=========================================================================
# At this level, we add methods, and partial constraints on top of update
# blocks and total constraints, to improve productivity.
# Two update blocks communicate via methods of the same component.
# A partial constraint is specified between one update block and one
# method, or two methods. PyMTL will try to chain partial constraints to
# produce total constraints.

import re, inspect, ast
p = re.compile('( *(@|def))')
from collections import defaultdict, deque

from UpdateComponent import UpdateComponent, U, _int

class M(object): # method wrapper
  def __init__( self, func ):
    self.func = func
  def __lt__( self, other ):
    return (self, other)
  def __gt__( self, other ):
    return (other, self)
  def __call__( self ):
    self.func()

class MethodComponent( UpdateComponent ):

  def __new__( cls, *args, **kwargs ):
    inst = super( MethodComponent, cls ).__new__( cls, *args, **kwargs )

    inst._blkid_methods = defaultdict(list)
    inst._method_blks   = defaultdict(list)
    inst._predecessor   = defaultdict(set)
    inst._successor     = defaultdict(set)
    return inst

  # Override
  def update( s, blk ):
    super( MethodComponent, s ).update( blk )

    # Parse the ast to extract method calls

    blk_id = id(blk)
    tree = type(s)._blkid_ast[ blk_id ]

    for node in ast.walk(tree):
      # Check if the node is a function call and the function name is not
      # not min,max,etc; it should be a component method call s.x.y.z()

      if     isinstance( node, ast.Call ) and \
         not isinstance( node.func, ast.Name ):

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

    # Total constraint will definitely be in the final graph.
    # Otherwise, we need to synthesize partial constraints between upblks
    # and methods later.

    for (x0, x1) in args:

      if isinstance( x0, U ) and isinstance( x1, U ): # Two upblks!
        s._add_expl_constraints( id(x[0].func), id(x[1].func) )
      else:
        x0_func = x0.func
        x1_func = x1.func

        # Store the method descriptor to instance dictionary for unique id

        if isinstance( x0, M ):
          if not x0.func.__name__  in s.__dict__:
            s.__dict__[ x0.func.__name__ ] = x0.func
          x0_func = s.__dict__[ x0.func.__name__ ]

        if isinstance( x1, M ):
          if not x1.func.__name__  in s.__dict__:
            s.__dict__[ x1.func.__name__ ] = x1.func
          x1_func = s.__dict__[ x1.func.__name__ ]

        # Partial constraints, x0 < x1
        s._predecessor[ id(x1_func) ].add( id(x0_func) )
        s._successor  [ id(x0_func) ].add( id(x1_func) )

  def _synthesize_partial_constraints( s, model ):
    if not isinstance( model, MethodComponent ):  return

    # First check if the methods exist, then bind update blocks that calls
    # the method to the method

    method_blks = defaultdict(set)

    for blk_id, method_calls in model._blkid_methods.iteritems():
      for (object_name, method_name) in method_calls:
        obj = model
        for field in object_name:
          assert hasattr( obj, field ), "\"%s\" is not a field of class %s"%(field, type(obj).__name__)
          obj = getattr( obj, field )

        assert hasattr( obj, method_name ), "\"%s\" is not a method of class %s"%(method_name, type(obj).__name__)
        method = getattr( obj, method_name )
        assert callable( method ), "\"%s\" is not callable %s"%(method_name, type(obj).__name__)

        method_blks[ id(method) ].add( blk_id )

    # Do bfs to find out all potential total constraints associated with
    # each method, direction conflicts, and incomplete constraints
    #
    # upX=methodA < methodB=upY ---> upX < upY
    # upX=methodA < upY         ---> upX < upY

    # Turn associated sets into lists, as blk_id are now unique.
    # O(logn) -> O(1)
    # Then append variables called at the current level to the big dict

    # We only find constraints for upblks at the current level. However,
    # there might be some constraints in grandchild or deeper submodels.
    # So, we append these to  all previous method_blks

    for i in method_blks:
      method_blks[i] = list( method_blks[i] )
      model._method_blks[i].extend( method_blks[i] )

    for method_id in method_blks:
      assoc_blks = method_blks[ method_id ]

      Q = deque( [ (method_id, 0) ] ) # -1: pred, 0: don't know, 1: succ
      while Q:
        (u, w) = Q.popleft()

        if w <= 0:
          for v in model._predecessor[u]:
            if v in model._blkid_upblk:
              assert v != blk_id, "Self loop at %s" % model._blkid_upblk[blk_id].__name__

              # find total constraint (upY < upX) by upY < methodA=upX
              for blk in assoc_blks:
                model._expl_constraints.add( (v, blk) )
            else:
              # find total constraint (upY < upX) by upY=methodB < methodA=upX
              v_blks = model._method_blks[ v ]
              for y in v_blks:
                for blk in assoc_blks:
                  model._expl_constraints.add( (y, blk) )

              Q.append( (v, -1) ) # ? < v < u < ... < method < blk_id

        if w >= 0:
          for v in model._successor[u]:
            if v in model._blkid_upblk:
              assert v != blk_id, "Self loop at %s" % model._blkid_upblk[blk_id].__name__

              # find total constraint (upX < upY) by upX=methodA < upY
              for blk in assoc_blks:
                model._expl_constraints.add( (blk, v) )
            else:
              # find total constraint (upX < upY) by upX=methodA < methodB=upY
              v_blks = model._method_blks[ v ]
              for y in v_blks:
                for blk in assoc_blks:
                  model._expl_constraints.add( (blk, y) )

              Q.append( (v, 1) ) # blk_id < method < ... < u < v < ?

  # Override
  def _recursive_elaborate( s, model ):

    for name, obj in model.__dict__.iteritems():
      if   isinstance( obj, int ): # to create unique id for int
        model.__dict__[ name ] = _int(obj)

      elif isinstance( obj, UpdateComponent ):
        s._recursive_elaborate( obj )

        model._blkid_upblk.update( obj._blkid_upblk )
        model._impl_constraints.update( obj._impl_constraints )
        model._expl_constraints.update( obj._expl_constraints )

        for k in obj._load_blks:
          model._load_blks[k].extend( obj._load_blks[k] )
        for k in obj._store_blks:
          model._store_blks[k].extend( obj._store_blks[k] )

        if isinstance( obj, MethodComponent ):
          for k in obj._predecessor:
            model._predecessor[k].update( obj._predecessor[k] )
          for k in obj._successor:
            model._successor[k].update( obj._successor[k] )
          for k in obj._method_blks:
            model._method_blks[k].extend( obj._method_blks[k] )

    s._synthesize_impl_constraints( model )
    s._synthesize_partial_constraints( model )
