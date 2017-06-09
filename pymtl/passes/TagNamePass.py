#-------------------------------------------------------------------------
# TagNamePass
#-------------------------------------------------------------------------
# Tag each child obj with full instance name. This has to executed again
# after elaboration during which new objects may be created. Stateless.
# TODO two different names point to the same object

from pymtl import *
from pymtl.passes import BasePass
from pymtl.components.NamedObject import NamedObject
from collections import deque

class TagNamePass( BasePass ):

  def execute( self, m ):
    self.recursive_tag_name( m )
    return m

  @staticmethod
  def recursive_tag_name( m ):

    def _recursive_tag_expand( child, parent, cur_name, cur_idx ):

      # Jump back to main function when it's another named object

      if   isinstance( child, NamedObject ):
        child._parent   = parent
        pname, pidx     = parent._name_idx
        child._name_idx = ( pname + cur_name, pidx + [ cur_idx ] )
        _recursive_tag_name( child )

      # ONLY LIST/DEQUE IS SUPPORTED, SORRY.
      # I don't want to support any iterable object because later "Wire"
      # can be infinitely iterated and cause infinite loop. Special casing
      # Wire will be a mess around everywhere.

      elif isinstance( child, list ) or isinstance( child, deque ):
        for i, o in enumerate( child ):
          _recursive_tag_expand( o, parent, cur_name, cur_idx + [i] )

    # If the id is string, it is a normal children field. Otherwise it
    # should be an tuple that represents a slice

    def _recursive_tag_name( m ):

      # Jump to the expand function to analyze the type of child object

      for name, obj in m.object_list:
        if   isinstance( name, basestring ): # python2 specific
          if not name.startswith("_"): # filter private variables
            _recursive_tag_expand( obj, m, [name], [] )
        elif isinstance( name, tuple ): # name = [1:3]
          _recursive_tag_expand( obj, m, [], [ slice(name[0], name[1]) ] )

    m._parent = None
    m._name_idx = ( ["s"], [ [] ] )
    _recursive_tag_name( m )
