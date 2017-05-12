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

    def find_net_head( obj, methodid_head ):
      root = obj._find_root()

      if id(root) in methodid_head:
        return methodid_head[ id(root) ]

      # Find the actual method
      net = root._connected
      head = None

      for m in net:
        assert head == None or not m.has_method(), "We don't allow connecting two actual methods, %s and %s" %(head._name, m._name)
        if m.has_method():
          head = m

      assert head, "Cannot have a bunch connected MethodPorts without an actual method. %s" % [x.full_name() for x in root._connected ]
      for m in net:
        s._methodid_head[ id(m) ] = head

      return head

    def recursive_collect_connections( parent, methodid_head ):
      if   isinstance( parent, list ):
        for i in xrange(len(parent)):
          if isinstance( parent[i], MethodPort ):
            parent[i] = find_net_head( parent[i], methodid_head )
          else:
            recursive_collect_connections( parent[i], methodid_head )

      elif isinstance( parent, PyMTLObject ):
        for name, obj in parent.__dict__.iteritems():
          if not name.startswith("_"):
            if   isinstance( obj, MethodPort ):
              setattr( parent, name, find_net_head( obj, methodid_head ) )
            else:
              recursive_collect_connections( obj, methodid_head )

    s._methodid_head = {}
    recursive_collect_connections( s, s._methodid_head )

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
    PyMTLObject._recursive_tag_name(s) # for debugging
    s._resolve_method_connections()
    super( MethodsConnection, s )._elaborate()
    s._update_partial_constraints()

