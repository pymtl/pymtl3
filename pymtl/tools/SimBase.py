from pymtl.components import NamedObject

class SimBase(object):

  def __init__( self, model ):
    self.model = model

    self.recursive_tag_name( model )

  #-------------------------------------------------------------------------
  # recursive_tag_name
  #-------------------------------------------------------------------------
  # Tag each child obj with full instance name. This has to executed again
  # after elaboration during which new objects may be created.
  # TODO two different names point to the same object

  @staticmethod
  def recursive_tag_name( m ):

    def _recursive_tag_expand( child, parent, cur_name, cur_idx ):

      # Jump back to main function when it's another named object
      if isinstance( child, NamedObject ):
        child._parent   = parent
        pname, pidx     = parent._name_idx
        child._name_idx = ( pname + cur_name, pidx + [ cur_idx ] )
        _recursive_tag_name( child )

      # If child is neither iterable or NamedObject, ignore it
      try:
        iterator = iter(child)
      except TypeError:
        return

      # Still the same name. Add another idx. Keep peeling the onion.
      for i, o in enumerate( child ):
        if o != child:
          _recursive_tag_expand( o, parent, cur_name, cur_idx + [i] )

    # If the id is string, it is a normal children field. Otherwise it
    # should be an tuple that represents a slice

    def _recursive_tag_name( m ):

      # Jump to the expand function to analyze the type of child object
      for name, obj in m.__dict__.iteritems():
        if isinstance( name, basestring ): # python2 specific
          if not name.startswith("_"): # filter private variables
            _recursive_tag_expand( obj, m, [name], [] )
        else:
          assert isinstance( name, tuple ) # name = [1:3]
          _recursive_tag_expand( obj, m, [], [ slice(name[0], name[1]) ] )

    m._name_idx = ( ["top"], [ [] ] )
    _recursive_tag_name( m )
