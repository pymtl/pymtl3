#=========================================================================
# PyMTLObject.py
#=========================================================================
# This is the very base class of PyMTL objects. I put it to enable all
# pymtl components to share the functionality of recursively collecting
# objects and tagging objects with the full name. This is the template
# traversal function of elaboration in the component hierarchy.

class PyMTLObject(object):

  def __new__( cls, *args, **kwargs ):
    inst = object.__new__( cls, *args, **kwargs )
    # Bookkeep name hierarchy here for error message and other purposes
    # For example, s.x[0][3].y[2].z turns into
    # ( ["top","x","y","z"], [ [], [0,3], [2], [] ] )

    inst._name_idx = ( ["s"], [ [] ] )
    return inst

  # Elaboration is performed after collecting data from all child modules.

  def _elaborate_vars( s ):
    pass

  # Parent calls this function to collecting variables in a child.

  def _collect_child_vars( s, child ):
    pass

  # This function expands objects in the list within "s" and calls "obj"'s
  # _recursive_elaborate back when it finds another PyMTLObject, it is
  # easier to support arbitrary list index and high dimensional array.

  def _recursive_expand( s, obj ):
    if   isinstance( obj, list ):
      for i in xrange(len(obj)):
        s._recursive_expand( obj[i] )
    elif isinstance( obj, PyMTLObject ):
      obj._recursive_elaborate()
      s._collect_child_vars( obj )

  # Enumerate all child objects and call recursive_expand to figure out
  # what to do with the child object, and collect variables from child.
  # Then elaborate all variables at the current level.

  def _recursive_elaborate( s ):
    for name, obj in s.__dict__.iteritems():
      if not name.startswith("_"): # filter private variables
        s._recursive_expand( obj )
    s._elaborate_vars()

  # Tag each child obj with full instance name. This has to be put after
  # elaboration because getattr during elaboration may create new objects

  def _recursive_tag_expand( s, name, obj, idx ):
    if   isinstance( obj, list ):
      for i in xrange(len(obj)):
        s._recursive_tag_expand( name, obj[i], idx+[i] )
    elif isinstance( obj, PyMTLObject ):
      obj._name_idx = ( s._name_idx[0]+[name], s._name_idx[1]+[list(idx)] )
      obj._recursive_tag_name()

  # TODO two different names point to the same object
  def _recursive_tag_name( s ):
    for name, obj in s.__dict__.iteritems():
      if not name.startswith("_"): # filter private variables
        s._recursive_tag_expand( name, obj, [] )

  def _elaborate( s ):
    s._recursive_elaborate()
    s._recursive_tag_name()

  def full_name( s ):
    name, idx = s._name_idx
    return ".".join( [ name[i] + "".join(["[%s]" % x for x in idx[i]]) \
                        for i in xrange(len(name)) ] )
