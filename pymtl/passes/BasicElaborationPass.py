#-------------------------------------------------------------------------
# BasicElaborationPass
#-------------------------------------------------------------------------

from pymtl.passes import BasePass, TagNamePass
from pymtl import NamedObject, UpdateOnly
from collections import deque

class BasicElaborationPass( BasePass ):

  def execute( self, m ):
    m = TagNamePass().execute( m )
    self.recursive_elaborate( m )

    m._blkid_upblk = self._blkid_upblk
    m._constraints = self._constraints

    return m

  # Enumerate all child objects and call recursive_expand to figure out
  # what to do with the child object, and collect variables from child.
  # Then elaborate all variables at the current level.

  def recursive_elaborate( self, m ):
    self._declare_vars()
    self._recursive_elaborate( m )

  def _declare_vars( self ):
    self._blkid_upblk = {}
    self._constraints = set()

  def _elaborate_vars( self, m ):
    pass

  def _collect_vars( self, m ):
    if isinstance( m, UpdateOnly ):
      self._blkid_upblk.update( m._id_upblk )
      self._constraints.update( m._U_U_constraints )

  def _recursive_elaborate( self, m ):

    def _recursive_expand( child ):

      # Jump back to main function when it's another named object
      if isinstance( child, NamedObject ):
        self._recursive_elaborate( child )

      # SORRY
      elif isinstance( child, list ) or isinstance( child, deque ):
        for i, o in enumerate( child ):
          _recursive_expand( o )

    for name, obj in m.object_list:
      if ( isinstance( name, basestring ) and not name.startswith("_") ) \
        or isinstance( name, tuple ):
          _recursive_expand( obj )

    self._elaborate_vars( m )
    self._collect_vars( m )
