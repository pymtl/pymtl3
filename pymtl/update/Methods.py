#=========================================================================
# Methods.py
#=========================================================================
# At this level, we add the ability to connect methods

from UpdatesExpl import verbose

from collections     import defaultdict, deque
from MethodsExpl     import MethodsExpl
from ASTHelper       import get_method_calls
from Connectable     import MethodProxy

class Methods( MethodsExpl ):

  # Override
  def __new__( cls, *args, **kwargs ):
    inst = super( Methods, cls ).__new__( cls, *args, **kwargs )

    for x in dir(cls):
      if x not in dir(Methods):
        y = getattr(inst, x)
        if callable(y):
          z = MethodProxy()
          z.attach_method( y )
          setattr( inst, x, z )

    inst._methodid_net = dict()
    inst._methodid_head = dict()
    return inst

  def _recursive_collect_method_connections( s, methodid_nets ):
    for name, obj in s.__dict__.iteritems():
      if not name.startswith("_"): # filter private variables

        # handle s.x
        if   isinstance( obj, Methods ):
          obj._recursive_collect_method_connections( methodid_nets )

        elif isinstance( obj, MethodProxy ):
          root = obj._find_root()

          if len( root._connected ) > 1: # has actual connection
            if id(root) not in methodid_nets:
              methodid_nets[ id(root) ] = (root, root._connected)
          else:
            assert root == obj, "It doesn't make sense ..."

          setattr( s, name, root )

        # handle s.x[i]
        elif isinstance( obj, list ):
          for i in xrange(len(obj)):
            if   isinstance( obj[i], Methods ):
              obj[i]._recursive_collect_method_connections( methodid_nets )

            elif isinstance( obj[i], MethodProxy ):
              root = obj[i]._find_root()

              if len( root._connected ) > 1: # has actual connection
                if id(root) not in methodid_nets:
                  methodid_nets[ id(root) ] = (root, root._connected)
              else:
                assert root == obj, "It doesn't make sense ..."

              obj[i] = root

  def _resolve_method_connections( s ):

    s._recursive_collect_method_connections( s._methodid_net )

    # Check if all nets are valid
    # Then inverse nets into a dictionary with {x : head of x's net}

    for (method, net) in s._methodid_net.values():

      # Find the actual method
      has_method, actual_mproxy = None, None

      for m in net:
        if m.has_method():
          assert not has_method, \
            "We don't allow connecting two actual methods, %s and %s" %(actual_mproxy._name, m._name)
          has_method, actual_mproxy = True, m

      method._func = actual_mproxy._func # attach the func to root

      for m in net:
        s._methodid_head[ id(m) ] = method

  def _recursive_replace_with_func( s ):
    for name, obj in s.__dict__.iteritems():
      if not name.startswith("_"): # filter private variables

        # handle s.x
        if   isinstance( obj, Methods ):
          obj._recursive_replace_with_func()

        elif isinstance( obj, MethodProxy ):
          setattr( s, name, obj._func )

        # handle s.x[i]
        elif isinstance( obj, list ):
          for i in xrange(len(obj)):
            if   isinstance( obj[i], Methods ):
              obj[i]._recursive_replace_with_func()
            elif isinstance( obj[i], MethodProxy ):
              obj[i] = obj[i]._func

  def _update_partial_constraints( s ):

    list_partial = list( s._partial_constraints )

    for i in xrange(len(list_partial)):
      x, y = list_partial[ i ]
      xid, yid = id(x), id(y)

      if xid in s._methodid_head:
        x = s._methodid_head[ xid ]
      if yid in s._methodid_head:
        y = s._methodid_head[ yid ]
      list_partial[i] = (x, y)

    s._partial_constraints = set( list_partial )

    if verbose:
      print "new partial constraints:"
      for (x, y) in s._partial_constraints:
        print hex(id(x)), "p<",hex(id(y))

  # Override
  def _elaborate( s ):
    s._resolve_method_connections()
    # assert False
    super( Methods, s )._elaborate()
    s._update_partial_constraints()
    s._recursive_replace_with_func()
