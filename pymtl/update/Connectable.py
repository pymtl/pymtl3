from PyMTLObject     import PyMTLObject

class Connectable(PyMTLObject):

  def __new__( cls, *args, **kwargs ):
    inst = PyMTLObject.__new__( cls )

    # Use disjoint set to resolve connections
    inst._root      = inst
    inst._connected = [ inst ]

    return inst

  def _find_root( s ): # Disjoint set path compression
    if s._root == s:  return s
    s._root = s._root._find_root()
    return s._root

  def connect( s, writer ):
    assert isinstance( writer, Connectable ), "Unconnectable object!"

    x = s._find_root()
    y = writer._find_root()
    assert x != y, "Two nets are already unionized!"
    # assert x == s, "One net signal cannot have two drivers. \n%s" % \
                   # "Please check if the left side signal is already at left side in another connection."

    # merge myself to the writer
    y._connected.extend( x._connected )
    x._connected = []
    x._root = y

  def __ior__( s, writer ):
    s.connect( writer )
    return s

  def collect_nets( s, varid_net ):
    root = s._find_root()
    if len( root._connected ) > 1: # has actual connection
      if id(root) not in varid_net:
        varid_net[ id(root) ] = (root, root._connected)
    else:
      assert root == s, "It doesn't make sense ..."

class Wire(Connectable):

  def __init__( s, type_ ):
    s._type = type_

  def default_value( s ):
    return s._type()

class ValuePort(Wire):
  pass

class MethodPort(Connectable):

  def __init__( self, *args ):
    self._has_method = False
    assert len(args) <= 1
    if args:
      other = args[0]
      assert isinstance( other, MethodPort ), "Cannot connect to %s, which is not a MethodPort."
      self.connect( other )

  def attach_method( self, func ):
    self._func = func
    self._name = func.__name__
    self._has_method = True

  def has_method( self ):
    return self._has_method

  # Override
  def connect( self, other ):
    if self.has_method():
      super( MethodPort, other ).connect( self )
    else:
      super( MethodPort, self ).connect( other )

class PortBundle(Connectable):

  # Override
  def connect( s, other ):

    # Expand the list when needed. Only connect connectables and return,
    # inheritance will figure out what to do with Port/PortBundle

    def recursive_connect( s_obj, other_obj ):
      if   isinstance( s_obj, list ):
        for i in xrange(len(s_obj)):
          recursive_connect( s_obj[i], other_obj[i] )
      elif isinstance( s_obj, Connectable ):
        s_obj.connect( other_obj )

    assert type(s) is type(other), "Invalid connection, %s <> %s." % (type(s).__name__, type(other).__name__)

    for name, obj in s.__dict__.iteritems():
      if not name.startswith("_"):
        recursive_connect( obj, getattr(other, name) )

  # Override
  def collect_nets( s, varid_net ):

    # Expand the list when needed. Only collect connectables and return
    def recursive_collect( obj, varid_net ):
      if   isinstance( obj, list ):
        for i in xrange(len(obj)):
          recursive_collect( obj[i], varid_net )
      elif isinstance( obj, Connectable ):
        obj.collect_nets( varid_net )

    for name, obj in s.__dict__.iteritems():
      if not name.startswith("_"):
        recursive_collect( obj, varid_net )
