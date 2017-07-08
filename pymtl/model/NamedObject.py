#=========================================================================
# NamedObject.py
#=========================================================================
# This is the very base class of PyMTL objects. I put it to enable all
# pymtl components to share the functionality of recursively collecting
# objects and tagging objects with the full name.
#
# We bookkeep name hierarchy for error message and other purposes.
# For example, s.x[0][3].y[2].z[1:3] is stored as
# ( ["top","x","y","z"], [ [], [0,3], [2], [slice(1,3,0)] ] )
# Note that len(name) == len(idx)-1 only when the variable ends with slice

class NamedObject(object):

  def __new__( cls, *args, **kwargs ):
    inst = super( NamedObject, cls ).__new__( cls, *args, **kwargs )
    inst._name_idx = []
    return inst

  # Developers should use repr(x) everywhere to get the name

  def __repr__( s ):
    if not s._name_idx: # if not tagged, go with class & address ...
      return super( NamedObject, s ).__repr__()

    name, idx = s._name_idx
    ret = ".".join( [ "{}{}".format( name[i],
                                     "".join([ "[{}]".format(x)
                                                for x in idx[i] ]) )
                      for i in xrange(len(name)) ] )

    if len(name) == len(idx): return ret

    # The only place we allow slicing is the end, and only one slice allowed

    assert len(name) == len(idx)-1 and len(idx[-1]) == 1
    return ret + "[{}:{}]".format( idx[-1][0].start, idx[-1][0].stop )

  def _tag_name_collect( s ):

    def _recursive_expand( child, parent, cur_name, cur_idx ):

      # Jump back to main function when it's another named object

      if   isinstance( child, NamedObject ):
        child._parent   = parent
        pname, pidx     = parent._name_idx
        child._name_idx = ( pname + cur_name, pidx + [ cur_idx ] )
        _recursive_tag_collect( child )

      # ONLY LIST IS SUPPORTED, SORRY.
      # I don't want to support any iterable object because later "Wire"
      # can be infinitely iterated and cause infinite loop. Special casing
      # Wire will be a mess around everywhere.

      elif isinstance( child, list ):
        for i, o in enumerate( child ):
          _recursive_expand( o, parent, cur_name, cur_idx + [i] )

    # If the id is string, it is a normal children field. Otherwise it
    # should be an tuple that represents a slice

    def _recursive_tag_collect( m ):

      # Collect m

      s._id_obj[ id(m) ] = m

      # Jump to the expand function to check the type of child object

      for name, obj in m.__dict__.iteritems():

        if   isinstance( name, basestring ): # python2 specific
          if not name.startswith("_"): # filter private variables
            _recursive_expand( obj, m, [name], [] )

        elif isinstance( name, tuple ): # name = [1:3]
          _recursive_expand( obj, m, [], [ slice(name[0], name[1]) ] )

    # Initialize the top level

    s._parent = None
    s._name_idx = ( ["s"], [ [] ] )

    s._id_obj = {}
    _recursive_tag_collect( s )
