#=========================================================================
# NamedObject.py
#=========================================================================
# This is the very base class of PyMTL objects. I put it to enable all
# pymtl components to share the functionality of recursively collecting
# objects and tagging objects with the full name. This is the template
# traversal function of elaboration in the component hierarchy.

class NamedObject(object):

  def __new__( cls, *args, **kwargs ):
    inst = object.__new__( cls, *args, **kwargs )

    # Bookkeep name hierarchy here for error message and other purposes
    # For example, s.x[0][3].y[2].z turns into
    # ( ["top","x","y","z"], [ [], [0,3], [2], [] ] )

    inst._name_idx = ( ["s"], [ [] ] )
    return inst

  def full_name( s ):
    name, idx = s._name_idx

    if len(name) == len(idx): # normal
      return ".".join( [ name[i] + "".join(["[%s]" % x for x in idx[i]]) \
                        for i in xrange(len(name)) ] )

    # The only place we allow slicing is the end
    assert len(name) == len(idx) - 1 and len(idx[-1]) == 1

    return ".".join( [ name[i] + "".join(["[%s]" % x for x in idx[i]]) \
                      for i in xrange(len(name)) ] ) + \
                      "[%d:%d]" % ( idx[-1][0].start, idx[-1][0].stop )
