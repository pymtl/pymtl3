from pymtl.components import NamedObject

#-------------------------------------------------------------------------
# recursive_tag_name
#-------------------------------------------------------------------------
# Tag each child obj with full instance name. This has to executed again
# after elaboration during which new objects may be created.
# TODO two different names point to the same object

def recursive_tag_name( model ):

  def _recursive_tag_expand( model, name, child, idx ):

    # Jump back to main function when it's another named object
    if isinstance( child, NamedObject ):
      child._name_idx = ( model._name_idx[0] + [name], model._name_idx[1] + [list(idx)] )
      _recursive_tag_name( child )

    # If child is neither iterable or NamedObject, ignore it
    try:
      iterator = iter(child)
    except TypeError:
      return

    # Still the same name. Add another idx. Keep peeling the onion.
    for i, o in enumerate( child ):
      _recursive_tag_expand( model, name, o, idx+[i] )

  def _recursive_tag_name( model ):

    for name, child in model.__dict__.iteritems():

      # Jump to the expand function to analyze the type of child object
      if not name.startswith("_"): # filter private variables
        _recursive_tag_expand( model, name, child, [] )

  model._name_idx = ( ["top"], [ [] ] )
  _recursive_tag_name( model )
