#=========================================================================
# PyMTLObject.py
#=========================================================================
# This is the very base class of PyMTL objects. I put it to enable all
# pymtl components to share the functionality of recursively collecting
# objects and tagging objects with the full name.

class PyMTLObject(object):

  # Elaboration is performed after collecting data from all child modules.

  def _elaborate_vars( s ):
    pass

  # Parent calls this function to collecting variables in a child.

  def _collect_child_vars( s, child ):
    pass

  # With this nested function that enumerate potential child types and
  # calls _recursive_elaborate back, it is easier to support arbitrary
  # list index and high dimensional array.
  
  def _enumerate_types( s, name, obj, idx ):
    if   isinstance( obj, list ):
      for i in xrange(len(obj)):
        s._enumerate_types( name, obj[i], idx + [i] )

    if isinstance( obj, PyMTLObject ):
      obj._father   = s
      obj._name_idx = ( s._name_idx[0] + [name], s._name_idx[1] + [list(idx)] )
      obj._recursive_elaborate()

      s._collect_child_vars( obj )

  # Enumerate all child objects and call _enumerate_types to figure out
  # what to do with the child object

  def _recursive_elaborate( s ):

    for name, obj in s.__dict__.iteritems():
      if not name.startswith("_"): # filter private variables
        s._enumerate_types( name, obj, [] )

    s._elaborate_vars()

  def _elaborate( s ):
    s._recursive_elaborate()

  def full_name( s ):
    name, idx = s._name_idx
    return ".".join( [ name[i] + "".join(["[%s]" % x for x in idx[i]]) \
                        for i in xrange(len(name)) ] )
