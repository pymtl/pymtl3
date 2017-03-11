class Value(object):

  def __init__( self, v ):
    self.v = v

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

  def connect( s, other ):
    assert isinstance( other, Connectable ), "Unconnectable object!"

    s._root = s._find_root()
    other._root = other._find_root()
    assert s._root != other._root, "Two nets are already unionized."

    s._root._connected.extend( other._root._connected )
    delattr(other._root, "_connected" ) # Purge merged signal
    other._root = s._root

  def __ior__( s, other ):
    s.connect( other )
    return s

class ConnectableValue(Connectable,Value):
  pass
