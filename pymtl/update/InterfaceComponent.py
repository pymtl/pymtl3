#=========================================================================
# InterfaceComponent.py
#=========================================================================
# Interfaces are supported at this level. By connecting interfaces we
# allow two components to be connected. This means that all connected
# components will have to access the same method of a representative
# object. I use disjoint set to maintain this relation ship in O(aN)

from collections import defaultdict, deque

from UpdateComponent import UpdateComponent, _int
from MethodComponent import MethodComponent, M

class InterfaceComponent( MethodComponent ):

  def __new__( cls, *args, **kwargs ):
    inst = super( InterfaceComponent, cls ).__new__( cls, *args, **kwargs )

    inst._root = inst # Use disjoint set to resolve connections
    inst.connected = False

    return inst

  def find_root( s ): # Disjoint set path compression
    if s._root == s:
      return s
    s._root = s._root.find_root()
    return s._root

  def connect( s, other ):
    s.connected = other.connected = True

    s._root = s.find_root()
    other._root = other.find_root()
    assert s._root != other._root, "Two nets are already unionized."
    other._root = s._root

  def __ior__( s, other ):
    s.connect( other )
    return s

  # Override
  def _elaborate_vars( s ):
    if s.find_root() == s:
      super( InterfaceComponent, s )._elaborate_vars()

    else:
      new_partial = list( s._partial_constraints )
      root = s._root

      # copy all functions over
      for x in dir( s ):
        origin = getattr( s, x )

        if hasattr( root, x ):
          inroot = getattr( root, x )
        else:
          setattr( s._root, x, origin )
          inroot = origin
        assert callable(origin) == callable(inroot)

        if callable( origin ):
          setattr( s, x, inroot )

          # replace involved ids with root's corresponding method's id
          for i in xrange( len(new_partial) ):
            x, y = new_partial[i]
            if x == id(origin): x = id(inroot)
            if y == id(origin): y = id(inroot)
            new_partial[i] = (x, y)

      # replace involved ids with root's corresponding upblk's id
      for name in s._name_upblk:
        assert name in root._name_upblk, "Connecting two different classes %s and %s" % \
                (s.__class__.__name__, root.__class__.__name__)

        origin = id( s._name_upblk[name] )
        inroot = id( root._name_upblk[name] )

        for i in xrange( len(new_partial) ):
          x, y = new_partial[i]
          if x == id(origin): x = id(inroot)
          if y == id(origin): y = id(inroot)
          new_partial[i] = (x, y)

      root._partial_constraints.update( new_partial )
      s._partial_constraints = set( new_partial ) # TODO Understand why it is correct
