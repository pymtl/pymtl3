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

from errors import NotElaboratedError
import re

class NamedObject(object):

  def __new__( cls, *args, **kwargs ):
    inst = super( NamedObject, cls ).__new__( cls )

    # Save parameters for elaborate

    inst._args        = args
    inst._kwargs      = kwargs
    inst._constructed = False

    inst._param_dict = { None:{} } # None is for regex patterns

    return inst

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def _construct( s ):
    if not s._constructed:

      kwargs = s._kwargs.copy()
      if "elaborate" in s._param_dict:
        kwargs.update( { x: y for x, y in s._param_dict[ "elaborate" ].iteritems()
                              if x } )

      if not kwargs: s.construct( *s._args )
      else:          s.construct( *s._args, **kwargs )

      s._constructed = True

  def __setattr_for_elaborate__( s, name, obj ):

    # I use non-recursive traversal to reduce error message depth
    # TODO _purely_ emulate recursion

    if not name.startswith("_"):
      stack = [ (obj, []) ]
      while stack:
        u, indices = stack.pop()

        if   isinstance( u, NamedObject ):
          try:
            u._parent_obj  = s
            u._level   = s._level + 1
            u._my_name = u_name = name + "".join([ "[{}]".format(x) for x in indices ])

            u._param_dict = { None:{} }

            # print s, s._param_dict[ None ]

            if u_name in s._param_dict:
              u._param_dict.update( s._param_dict[ u_name ] )

            for pattern, (compiled_re, subdict) in s._param_dict[ None ].iteritems():
              if compiled_re.match( u_name ):
                for x, y in subdict.iteritems(): # to merge two None subdicts
                  if x is None:
                    u._param_dict[ None ].update( subdict )
                  else:
                    u._param_dict[ x ] = y

            s_name = s._full_name
            u._full_name = ( s_name + "." + u_name )
            u._construct()
          except AttributeError:
            raise AttributeError("In {}:\n   Please put all logic in construct " \
                                 "instead of __init__.".format( s.__class__) )

        # ONLY LIST IS SUPPORTED, SORRY.
        # I don't want to support any iterable object because later "Wire"
        # can be infinitely iterated and cause infinite loop. Special casing
        # Wire will be a mess around everywhere.

        elif isinstance( u, list ):
          for i, v in enumerate( u ):
            stack.append( (v, indices+[i]) )

    super( NamedObject, s ).__setattr__( name, obj )

  # recursively and exhaustively
  # I changed dfs to bfs with stack

  def _collect_all( s, filt=lambda x: isinstance( x, NamedObject ) ):

    ret = set()
    stack = [s]
    while stack:
      u = stack.pop()
      if   isinstance( u, NamedObject ):

        if filt( u ): # Check if m satisfies the filter
          ret.add( u )

        for name, obj in u.__dict__.iteritems():

          # If the id is string, it is a normal children field. Otherwise it
          # should be an tuple that represents a slice

          if   isinstance( name, basestring ): # python2 specific
            if not name.startswith("_"): # filter private variables
              stack.append( obj )

          elif isinstance( name, tuple ): # name = [1:3]
            stack.append( obj )

      # ONLY LIST IS SUPPORTED
      elif isinstance( u, list ):
        stack.extend( u )

    return ret

  # Developers should use repr(x) everywhere to get the name

  def __repr__( s ):
    try:
      return s._full_name
    except AttributeError:
      return super( NamedObject, s ).__repr__()

  def elaborate( s ):
    if s._constructed:
      return

    # Initialize the top level

    s._parent_obj = None
    s._level     = 0
    s._my_name   = "s"
    s._full_name = "s"

    # Override setattr for elaboration, and then remove it

    NamedObject.__setattr__ = NamedObject.__setattr_for_elaborate__

    try:
      s._construct()
    except Exception:
      # re-raise here after deleting __setattr__
      del NamedObject.__setattr__ # not harming the rest of execution
      raise

    del NamedObject.__setattr__

  def construct( s, *args, **kwargs ):
    pass

  #-----------------------------------------------------------------------
  # Public APIs (only can be called after elaboration)
  #-----------------------------------------------------------------------

  def set_parameter( s, string, value ):
    strs = string.split( "." )

    assert strs[0] == "top", "The component should start at top"

    strs     = strs[1:]
    strs_len = len(strs)
    assert strs_len >= 1

    current_dict = s._param_dict

    for x in strs[:-1]:
      # TODO should we only allow * as regular expression to accelerate
      # the common case? or always store as regex no matterwhat?
      if "*" in x:
        # We lump all regex patterns into key=None
        if x not in current_dict[ None ]: # use name to index
          current_dict[ None ][ x ] = ( re.compile(x), {} )

        current_dict = current_dict[ None ][ x ][ 1 ]

      # This is a normal string
      else:
        if x not in current_dict:
          current_dict[ x ] = { None: {} }
        current_dict = current_dict[ x ]

    # The last element in strs
    x = strs[-1]
    assert "*" not in x, "We don't allow the last name to be *"
    if x not in current_dict:
      current_dict[ x ] = value

  def is_component( s ):
    raise NotImplemented

  def is_signal( s ):
    raise NotImplemented

  def is_interface( s ):
    raise NotImplemented

  def get_field_name( s ):
    try:
      return s._my_name
    except AttributeError:
      raise NotElaboratedError()

  def get_parent_object( s ):
    try:
      return s._parent_obj
    except AttributeError:
      raise NotElaboratedError()

  def get_all_object_filter( s, filt ):
    assert callable( filt )
    return s._collect( filt )
