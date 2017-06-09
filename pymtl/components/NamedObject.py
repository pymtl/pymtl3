#=========================================================================
# NamedObject.py
#=========================================================================
# This is the very base class of PyMTL objects. I put it to enable all
# pymtl components to share the functionality of recursively collecting
# objects and tagging objects with the full name.

class NamedObject(object):

  def __new__( cls, *args, **kwargs ):
    inst = super( NamedObject, cls ).__new__( cls, *args, **kwargs )

    # Bookkeep name hierarchy here for error message and other purposes
    # For example, s.x[0][3].y[2].z[1:3] turns into
    # ( ["top","x","y","z"], [ [], [0,3], [2], [slice(1,3,0)] ] )
    # len(name) == len(idx) - 1 only when the variable ends with slice

    inst._name_idx = []
    return inst

  @property
  def object_list( s ):
    return s.__dict__.items()

  # Developers should use repr(x) everywhere
  def __repr__( s ):
    if not s._name_idx:
      return super( NamedObject, s ).__repr__()

    name, idx = s._name_idx

    if len(name) == len(idx): # normal
      return ".".join( [ name[i] + "".join(["[%s]" % x for x in idx[i]]) \
                        for i in xrange(len(name)) ] )

    # The only place we allow slicing is the end
    assert len(name) == len(idx) - 1 and len(idx[-1]) == 1

    return ".".join( [ name[i] + "".join(["[%s]" % x for x in idx[i]]) \
                      for i in xrange(len(name)) ] ) + \
                      "[%d:%d]" % ( idx[-1][0].start, idx[-1][0].stop )
