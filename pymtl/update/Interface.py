#=========================================================================
# Interface.py
#=========================================================================
# Interface is tightly coupled with MethodComponent since an interface is
# a proxy of methods.

class Interface( object ):

  def __new__( cls, *args, **kwargs ):
    inst = super( Interface, cls ).__new__( cls )

    # This interface has the actual method entities. Other connected
    # interfaces should only be proxies.

    inst._is_entity = False
    inst._methods   = []
    if args:
      inst._is_entity = True
      for x in args:
        method = x.__name__
        assert hasattr( inst, method )
        assert callable( getattr( inst, method ) )
        setattr( inst, method, x )
        inst._methods.append( method )

    inst._root = inst # Use disjoint set to resolve connections

    return inst

  def find_root( s ): # Disjoint set path compression
    if s._root == s:  return s
    s._root = s._root.find_root()
    return s._root

  def connect( s, other ):
    s.connected = other.connected = True

    s._root = s.find_root()
    other._root = other.find_root()
    assert s._root != other._root, "Two nets are already unionized."
    assert not s._root._is_entity or not other._root._is_entity, \
           "Cannot have two interfaces initialized with methods."

    if other._root._is_entity:
      s._root = other._root

  def _connect_to_root( s ):
    for x in s._root._methods:
      assert hasattr( s, x ), "Method %s is not in %s" % ( x, type(s) )
      setattr( s, x, getattr( s._root, x ) )

  def __ior__( s, other ):
    s.connect( other )
    return s
