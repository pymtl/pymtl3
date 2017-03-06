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
    super( MethodComponent, s )._elaborate_vars()

    if s.find_root() != s:

      # copy all functions over
      for x in dir( s ):
        if callable( getattr( s._root, x) ):
          setattr( s, x, getattr( s._root, x) )

      # copy all variables over
      s.__dict__.update( s._root.__dict__ )
