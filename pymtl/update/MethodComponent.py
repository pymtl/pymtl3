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

from UpdateComponent import UpdateComponent, U

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
    inst._predecessor   = defaultdict(set)
    inst._successor     = defaultdict(set)

    return inst

  # Override
  def update( s, blk ):
    super( MethodComponent, s ).update( blk )

    blk_id = id(blk)

    # I store the ast of each update block to parse method calls. To also
    # cache them across different instances of the same class, I attach
    # the information to the class object.

    if not "_blkid_ast" in type(s).__dict__:
      type(s)._blkid_ast = dict()

    if blk_id not in type(s)._blkid_ast:
      src = p.sub( r'\2', inspect.getsource( blk ) )
      type(s)._blkid_ast[ blk_id ] = ast.parse( src )

    # Parse the ast

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
        s._total_constraints.append( (id(x0.func), id(x1.func)) )
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

  # Override
  def _recursive_collect( s, model ):

    # First collect all constraints in the submodules

    for name, obj in model.__dict__.iteritems():
      if   isinstance( obj, UpdateComponent ):
        s._recursive_collect( obj )

        model._blkid_upblk.update( obj._blkid_upblk )
        model._upblks.extend( obj._upblks )
        model._total_constraints.update( obj._total_constraints )

        model._predecessor.update( obj._predecessor )
        model._successor.update( obj._successor )

    # Then synthesize partial constraints

    pred = model._predecessor
    succ = model._successor

    methodid_blks = defaultdict(set)

    # First check if the methods exist, then
    # bind the method to the update blocks that calls the method

    for blk_id, method_calls in model._blkid_methods.iteritems():

      for (object_name, method_name) in method_calls:
        obj = model
        for field in object_name:
          assert hasattr( obj, field ), "\"%s\" is not a field of class %s"%(field, type(obj).__name__)
          obj = getattr( obj, field )

        assert hasattr( obj, method_name ), "\"%s\" is not a method of class %s"%(method_name, type(obj).__name__)
        method = getattr( obj, method_name )

        methodid_blks[ id(method) ].add( blk_id )

    # Do bfs to find out all potential total constraints associated with
    # each method, direction conflicts, and incomplete constraints
    #
    # upX=methodA < methodB=upY ---> upX < upY
    # upX=methodA < upY         ---> upX < upY

    for i in methodid_blks:
      methodid_blks[i] = list( methodid_blks[i] )

    for method_id in methodid_blks:
      assoc_blks = methodid_blks[ method_id ]


      Q = deque( [ (method_id, 0) ] ) # -1: pred, 0: don't know, 1: succ
      while Q:
        (u, w) = Q.popleft()

        if w <= 0:
          for v in pred[u]:
            if v in model._blkid_upblk:
              assert v != blk_id, "Self loop at %s" % model._blkid_upblk[blk_id].__name__

              # find total constraint (upY < upX) by upY < methodA=upX
              for blk in assoc_blks:
                model._total_constraints.add( (v, blk) )
            else:
              # find total constraint (upY < upX) by upY=methodB < methodA=upX
              v_blks = methodid_blks[ v ]
              for y in v_blks:
                for x in assoc_blks:
                  model._total_constraints.add( (y, x) )

              Q.append( (v, -1) ) # ? < v < u < ... < method < blk_id

        if w >= 0:
          for v in succ[u]:
            if v in model._blkid_upblk:
              assert v != blk_id, "Self loop at %s" % model._blkid_upblk[blk_id].__name__

              # find total constraint (upX < upY) by upX=methodA < upY
              for blk in assoc_blks:
                model._total_constraints.add( (v, blk) )
            else:
              # find total constraint (upX < upY) by upX=methodA < methodB=upY
              v_blks = methodid_blks[ v ]
              for x in assoc_blks:
                for y in v_blks:
                  model._total_constraints.add( (x, y) )

              Q.append( (v, 1) ) # blk_id < method < ... < u < v < ?
