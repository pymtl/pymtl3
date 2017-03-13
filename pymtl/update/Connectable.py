class Value(object):

  def __init__( self, v, obj, name, idx ):
    self.v     = v
    self._obj  = obj   # Host object that has self as member
    self._name = name  # The member name in the host object
    self._idx  = idx   # >=0: this is nested in list. <0 otherwise

class Connectable(object):

  def __new__( cls, *args ):
    inst = object.__new__( cls )

    # Use disjoint set to resolve connections
    inst._root      = inst 
    inst._connected = [ inst ]

    return inst

  def _find_root( s ): # Disjoint set path compression
    if s._root == s:  return s
    s._root = s._root._find_root()
    return s._root

  def connect( s, o ):
    assert isinstance( o, Connectable ), "Unconnectable object!"

    x = s._root = s._find_root()
    y = o._root = o._find_root()
    assert x != y, "Two nets are already unionized."

    x._connected.extend( y._connected )
    delattr(y, "_connected" ) # Purge merged signal
    y._root = x

  def __ior__( s, other ):
    s.connect( other )
    return s

class ConnectableValue(Connectable,Value):
  pass

class Method(object):
  def __init__( self, func ):
    self.func  = func
    self._name = func.__name__

  def __call__( self ):
    self.func()
