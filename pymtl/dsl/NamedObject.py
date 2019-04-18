#=========================================================================
# NamedObject.py
#=========================================================================
# This is the very base class of PyMTL objects. It enables all pymtl
# components/signals to share the functionality of recursively collecting
# objects and tagging objects with the full name.
#
# We bookkeep name hierarchy for error message and other purposes.
# For example, s.x[0][3].y[2].z[1:3] is stored as
# ( ["top","x","y","z"], [ [], [0,3], [2], [slice(1,3,0)] ] )
# Note that len(name) == len(idx)-1 only when the variable ends with slice
#
# We keep all metadata in inst._dsl.*. This is to create a namespace
# to centralize all DSL-related metadata. Passes will create other
# namespaces to put their created metadata.
#
# Author : Shunning Jiang
# Date   : Nov 3, 2018

from errors import NotElaboratedError
import re

class DSLMetadata(object):
  pass

class NamedObject(object):

  def __new__( cls, *args, **kwargs ):

    inst = super( NamedObject, cls ).__new__( cls )
    inst._dsl = DSLMetadata() # TODO an actual object?

    # Save parameters for elaborate

    inst._dsl.args        = args
    inst._dsl.kwargs      = kwargs
    inst._dsl.constructed = False

    inst._dsl.param_dict = { None:{} } # None is for regex patterns

    return inst

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def _construct( s ):

    if not s._dsl.constructed:

      # Merge the actual keyword args and those args set by set_parameter
      kwargs = s._dsl.kwargs.copy()
      if "elaborate" in s._dsl.param_dict:
        more_args = s._dsl.param_dict[ "elaborate" ].iteritems()
        kwargs.update( { x: y for x, y in more_args if x } )

      s.construct( *s._dsl.args, **kwargs )

      s._dsl.constructed = True

  def __setattr_for_elaborate__( s, name, obj ):

    # I use non-recursive traversal to reduce error message depth

    if not name.startswith("_"):
      stack = [ (obj, []) ]
      while stack:
        u, indices = stack.pop()

        if   isinstance( u, NamedObject ):
          # try:
            u._dsl.parent_obj  = s
            u._dsl.level       = s._dsl.level + 1
            u._dsl.my_name = u_name = name + "".join([ "[{}]".format(x)
                                                      for x in indices ])
            u._dsl.param_dict = { None:{} }

            if u_name in s._dsl.param_dict:
              u._dsl.param_dict.update( s._dsl.param_dict[ u_name ] )

            for pattern, (compiled_re, subdict) in \
                s._dsl.param_dict[ None ].iteritems():
              if compiled_re.match( u_name ):
                for x, y in subdict.iteritems(): # to merge two None subdicts
                  if x is None:
                    u._dsl.param_dict[ None ].update( y )
                  else:
                    u._dsl.param_dict[ x ] = y

            s_name = s._dsl.full_name
            u._dsl.full_name = ( s_name + "." + u_name )
            u._construct()
          # except AttributeError as e:
          #   raise AttributeError(e.message+"\n"+"(Suggestion: in {}:\n   Please put all logic in construct " \
          #                        "instead of __init__.)".format( s.__class__ ) )

        # ONLY LIST IS SUPPORTED, SORRY.
        # I don't want to support any iterable object because later "Wire"
        # can be infinitely iterated and cause infinite loop. Special
        # casing Wire will be a mess around everywhere.

        elif isinstance( u, list ):
          for i, v in enumerate( u ):
            stack.append( (v, indices+[i]) )

    super( NamedObject, s ).__setattr__( name, obj )

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
      return s._dsl.full_name
    except AttributeError:
      return super( NamedObject, s ).__repr__()

  #-----------------------------------------------------------------------
  # Public APIs
  #-----------------------------------------------------------------------

  def construct( s, *args, **kwargs ):
    pass

  def set_parameter( s, string, value ):
    assert not s._dsl.constructed

    strs = string.split( "." )

    assert strs[0] == "top", "The component should start at top"

    strs     = strs[1:]
    strs_len = len(strs)
    assert strs_len >= 1

    current_dict = s._dsl.param_dict

    for x in strs[:-1]:
      # TODO should we only allow * as regular expression to accelerate
      # the common case? or always store as regex no matterwhat?
      if "*" in x:
        # We lump all regex patterns into key=None
        if x not in current_dict[ None ]: # use name to index
          current_dict[ None ][ x ] = ( re.compile(x), {} )
        current_dict = current_dict[ None ][ x ][ 1 ]
        current_dict[ None ] = {}

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

  def elaborate( s ):
    if s._dsl.constructed:
      print "Don't elaborate the same model twice. \
             Use APIs to mutate the model."
      return

    # Initialize the top level

    s._dsl.parent_obj = None
    s._dsl.level     = 0
    s._dsl.my_name   = "s"
    s._dsl.full_name = "s"

    # Secret source for letting the child know the field name of itself
    # -- override setattr for elaboration, and remove it afterwards

    NamedObject.__setattr__ = NamedObject.__setattr_for_elaborate__

    try:
      s._construct()
    except Exception:
      # re-raise here after deleting __setattr__
      del NamedObject.__setattr__ # not harming the rest of execution
      raise

    del NamedObject.__setattr__

    s._dsl.all_named_objects = s._collect_all()
    for c in s._dsl.all_named_objects:
      c._dsl.elaborate_top = s

  # The following APIs can only be called after elaboration

  def is_component( s ):
    raise NotImplemented

  def is_signal( s ):
    raise NotImplemented

  def is_interface( s ):
    raise NotImplemented

  def get_field_name( s ):
    try:
      return s._dsl.my_name
    except AttributeError:
      raise NotElaboratedError()

  def get_parent_object( s ):
    try:
      return s._dsl.parent_obj
    except AttributeError:
      raise NotElaboratedError()

  def get_all_object_filter( s, filt ):
    assert callable( filt )
    return s._dsl.collect( filt )
