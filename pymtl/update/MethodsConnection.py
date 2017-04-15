#=========================================================================
# MethodsConnection.py
#=========================================================================
# At this level, we add the ability to connect methods

from UpdatesExpl import verbose

from collections import defaultdict, deque
from PyMTLObject import PyMTLObject
from MethodsExpl import MethodsExpl
from ASTHelper   import get_method_calls
from Connectable import MethodPort

class MethodsConnection( MethodsExpl ):

  # Override
  def __new__( cls, *args, **kwargs ):
    inst = super( MethodsConnection, cls ).__new__( cls, *args, **kwargs )

    for x in dir(cls):
      if x not in dir(MethodsConnection):
        y = getattr(inst, x)
        if callable(y):
          z = MethodPort()
          z.attach_method( y )
          setattr( inst, x, z )

    return inst

  def _resolve_method_connections( s ):

    def recursive_collect_connections( parent, methodid_nets ):
      if   isinstance( parent, list ):
        for i in xrange(len(parent)):
          if isinstance( parent[i], MethodPort ):
            root = parent[i]._find_root()
            if id(root) not in methodid_nets:
              methodid_nets[ id(root) ] = (root, root._connected)
            parent[i] = root
          else:
            recursive_collect_connections( parent[i], methodid_nets )

      elif isinstance( parent, PyMTLObject ):
        for name, obj in parent.__dict__.iteritems():
          if not name.startswith("_"):
            if   isinstance( obj, MethodPort ):
              root = obj._find_root()

              if id(root) not in methodid_nets:
                methodid_nets[ id(root) ] = (root, root._connected)
              setattr( parent, name, root )

            else:
              recursive_collect_connections( obj, methodid_nets )

    s._methodid_net = dict()
    s._methodid_head = dict()

    recursive_collect_connections( s, s._methodid_net )

    # Check if all nets are valid
    # Then inverse nets into a dictionary with {x : head of x's net}

    for (method, net) in s._methodid_net.values():

      # Find the actual method
      assert method.has_method(), "Cannot have a bunch connected MethodPorts without an actual method: %s." % method.__dict__

      for m in net:
        assert (m == method) or (not m.has_method()), "We don't allow connecting two actual methods, %s and %s" %(method._name, m._name)
        s._methodid_head[ id(m) ] = method

  def _update_partial_constraints( s ):

    # Update partial constraints for all connected method port

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
    super( MethodsConnection, s )._elaborate()
    s._update_partial_constraints()

