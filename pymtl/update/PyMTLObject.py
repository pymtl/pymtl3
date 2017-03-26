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

  # This function expands objects in the list and calls
  # _recursive_elaborate back when it finds another PyMTLObject, it is
  # easier to support arbitrary list index and high dimensional array.

  def recursive_expand( s, name, obj, idx ):
    if   isinstance( obj, list ):
      for i in xrange(len(obj)):
        s.recursive_expand( name, obj[i], idx + [i] )
    elif isinstance( obj, PyMTLObject ):
      obj._father   = s
      obj._name_idx = ( s._name_idx[0] + [name], s._name_idx[1] + [list(idx)] )
      obj._recursive_elaborate()
      s._collect_child_vars( obj )

  # Enumerate all child objects and call recursive_expand to figure out
  # what to do with the child object, and collect variables from child.
  # Then elaborate all variables at the current level.

  def _recursive_elaborate( s ):

    for name, obj in s.__dict__.iteritems():
      if not name.startswith("_"): # filter private variables
        s.recursive_expand( name, obj, [] )

    s._elaborate_vars()

  def _elaborate( s ):
    s._recursive_elaborate()

  def full_name( s ):
    name, idx = s._name_idx
    return ".".join( [ name[i] + "".join(["[%s]" % x for x in idx[i]]) \
                        for i in xrange(len(name)) ] )
