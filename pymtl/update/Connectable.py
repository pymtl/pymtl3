class Value(object):

  def __init__( self, v ):
    self.v = v

  def __str__( self ):
    return v.__str__

class Connectable(object):

  def __new__( cls, *args ):
    inst = object.__new__( cls )

    # Use disjoint set to resolve connections
    inst._root      = inst 
    inst._connected = [ inst ]

    return inst

  def find_root( s ): # Disjoint set path compression
    if s._root == s:  return s
    s._root = s._root.find_root()
    return s._root

  def connect( s, other ):
    s._root = s.find_root()
    other._root = other.find_root()

    assert s._root != other._root, "Two nets are already unionized."

    other._root = s._root
    s._root._connected.extend( other._root._connected )
    delattr(other._root, "_connected" ) # Purge merged signal

  def __ior__( s, other ):
    s.connect( other )
    return s

class ConnectableValue(Connectable,Value):
  pass
