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

    def _recursive_tag_expand( child, name, idx, cur_idx ):

      # Jump back to main function when it's another named object
      if isinstance( child, NamedObject ):
        child._name_idx = ( name, idx + [ cur_idx ] )
        _recursive_tag_name( child )

      # If child is neither iterable or NamedObject, ignore it
      try:
        iterator = iter(child)
      except TypeError:
        return

      # Still the same name. Add another idx. Keep peeling the onion.
      for i, o in enumerate( child ):
        if o != child:
          _recursive_tag_expand( o, name, idx, cur_idx + [i] )

    def _recursive_tag_name( m ):

      for name, child in m.__dict__.iteritems():

        # Jump to the expand function to analyze the type of child object
        if not name.startswith("_"): # filter private variables
          _recursive_tag_expand( child,
                                 m._name_idx[0] + [name],
                                 m._name_idx[1], [] )

    m._name_idx = ( ["top"], [ [] ] )
    _recursive_tag_name( m )
