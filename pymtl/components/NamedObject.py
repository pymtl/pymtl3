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
    if not name[-1]: # The only place we allow slicing is the end
      assert len(idx[-1]) == 1
      return ".".join( [ "{}{}".format( name[i], "".join(["[{}]".format(x) for x in idx[i]]) ) \
                         for i in xrange(len(name)-1) ]
                     ) + "[{}:{}]".format( idx[-1][0].start, idx[-1][0].stop )
    return ".".join( [ "{}{}".format( name[i], "".join( ["[{}]".format(x) for x in idx[i]] ) ) \
                        for i in xrange(len(name)) ] )
