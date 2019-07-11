"""
========================================================================
NamedObject.py
========================================================================
This is the very base class of PyMTL objects. It enables all pymtl
components/signals to share the functionality of recursively collecting
objects and tagging objects with the full name.

We bookkeep name hierarchy for error message and other purposes.
For example, s.x[0][3].y[2].z[1:3] is stored as
( ["top","x","y","z"], [ [], [0,3], [2], [slice(1,3,0)] ] )
Note that len(name) == len(idx)-1 only when the variable ends with slice

We keep all metadata in inst._dsl.*. This is to create a namespace
to centralize all DSL-related metadata. Passes will create other
namespaces to put their created metadata.

Author : Shunning Jiang, Yanghui Ou
Date   : Nov 3, 2018
"""
from __future__ import absolute_import, division, print_function

import re

from .errors import NotElaboratedError

# from collections import OrderedDict as ord_dict


class DSLMetadata(object):
  pass

# NOTE: We found that the built-in OrderedDict slows down the elaboration
# time because much time was spent calling OrderedDict.__init__.
# The time for instantiating an OrderedDict is quite long compared
# to other primitive data structures such as list or dict. We have to
# implement our own ordered dictionary to mitigate this overhead.
# TODO: When we move to python3, we won't need this any more.
class ord_dict( object ):
  def __init__( self ):
    self.data = []

  def __getitem__( self, key ):
    for k, v in self.data:
      if key == k:
        return v
    raise KeyError( "Key error:{}".format( key ) )

  def __setitem__( self, key, value ):
    idx = 0
    for k, v in self.data:
      if key == k:
        self.data[ idx ] = ( k, value )
        return
      idx += 1
    self.data.append( ( key, value ) )

  def __iter__( self ):
    for k, _ in self.data:
      yield k

  def __str__( self ):
    return str( self.data )

  def pop( self, key ):
    idx = 0
    for k, v in self.data:
      if key == k:
        _, ret = self.data.pop( idx )
        return ret
      idx += 1
    raise KeyError( "Key error:{}".format( key ) )

  def iteritems( self ):
    for k, v in self.data:
      yield k, v

  items = iteritems

# Special data structure for constructing the parameter tree.
class ParamTreeNode(object):
  def __init__( self ):
    self.compiled_re = None
    self.children = None
    self.leaf = None

  def merge( self, other ):
    # Merge leaf
    if other.leaf is not None:
      # Lazily create leaf
      if self.leaf is None:
        self.leaf = {}
      for func_name, subdict in other.leaf.iteritems():
        if func_name not in self.leaf:
          self.leaf[ func_name ] = {}
        self.leaf[ func_name ].update( subdict )

    # Merge children
    if other.children is not None:
      # Lazily create children
      if self.children is None:
        self.children = ord_dict()
      for comp_name, node in other.children.iteritems():
        if comp_name in self.children:
          self.children[ comp_name ].merge( node )
        else:
          self.children[ comp_name ] = node

  def add_params( self, strs, func_name, **kwargs ):

    if self.leaf is None:
      self.leaf = {}
      self.children = ord_dict()

    # Traverse to the node
    cur_node = self
    idx = 1
    for comp_name in strs:
      # Lazily create children
      if cur_node.children is None:
        cur_node.children = ord_dict()
      if comp_name not in cur_node.children:
        new_node = ParamTreeNode()
        if '*' in comp_name:
          new_node.compiled_re = re.compile( comp_name )
          # Recursively update exisiting nodes that matches the regex
          for name, node in cur_node.children.iteritems():
            if node.compiled_re is None:
              if new_node.compiled_re.match( name ):
                node.add_params( strs[idx:], func_name, **kwargs )
        cur_node.children[ comp_name ] = new_node
        cur_node = new_node
      else:
        new_node = cur_node.children.pop( comp_name )
        cur_node.children[ comp_name ] = new_node
        cur_node = new_node
      idx += 1

    # Add parameters to leaf
    if cur_node.leaf is None:
      cur_node.leaf = {}
    if func_name not in cur_node.leaf:
      cur_node.leaf[ func_name ] = {}
    cur_node.leaf[ func_name].update( kwargs )

  def __repr__( self ):
    return "\nleaf:{}\nchildren:{}".format( self.leaf, self.children )

class NamedObject(object):

  def __new__( cls, *args, **kwargs ):

    inst = super( NamedObject, cls ).__new__( cls )
    inst._dsl = DSLMetadata() # TODO an actual object?

    # Save parameters for elaborate

    inst._dsl.args        = args
    inst._dsl.kwargs      = kwargs
    inst._dsl.constructed = False

    # A tree of parameters.
    inst._dsl.param_tree = None

    return inst

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def _construct( s ):

    if not s._dsl.constructed:

      # Merge the actual keyword args and those args set by set_parameter
      if s._dsl.param_tree is None:
        kwargs = s._dsl.kwargs
      elif s._dsl.param_tree.leaf is None:
        kwargs = s._dsl.kwargs
      else:
        kwargs = s._dsl.kwargs
        if "construct" in s._dsl.param_tree.leaf:
          more_args = s._dsl.param_tree.leaf[ "construct" ]
          kwargs.update( more_args )

      s.construct( *s._dsl.args, **kwargs )

      s._dsl.constructed = True

  def __setattr_for_elaborate__( s, name, obj ):

    # I use non-recursive traversal to reduce error message depth

    if not name.startswith("_"):
      stack = [ (obj, []) ]
      while stack:
        u, indices = stack.pop()

        if isinstance( u, NamedObject ):
          # try:
            u._dsl.parent_obj = s
            u._dsl.level      = s._dsl.level + 1
            u._dsl.my_name    = u_name = name + "".join( [ "[{}]".format(x)
                                                           for x in indices ] )

            # Iterate through the param_tree and update u
            if s._dsl.param_tree is not None:
              if s._dsl.param_tree.children is not None:
                for comp_name, node in s._dsl.param_tree.children.iteritems():
                  if comp_name == u_name:
                    # Lazily create the param tree
                    if u._dsl.param_tree is None:
                      u._dsl.param_tree = ParamTreeNode()
                    u._dsl.param_tree.merge( node )

                  elif node.compiled_re is not None:
                    if node.compiled_re.match( u_name ):
                      # Lazily create the param tree
                      if u._dsl.param_tree is None:
                        u._dsl.param_tree = ParamTreeNode()
                      u._dsl.param_tree.merge( node )

            s_name = s._dsl.full_name
            u._dsl.full_name = ( s_name + "." + u_name )

            # store the name/indices
            u._dsl._my_name     = name
            u._dsl._my_indices  = indices

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

  # It is possible to take multiple filters
  def _collect_all( s, filt=[ lambda x: isinstance( x, NamedObject ) ] ):
    ret = [ set() for _ in filt ]
    stack = [s]
    while stack:
      u = stack.pop()
      if   isinstance( u, NamedObject ):

        for i in range( len(filt) ):
          if filt[i]( u ): # Check if m satisfies the filter
            ret[i].add( u )

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
  # Construction time APIs
  #-----------------------------------------------------------------------

  def construct( s, *args, **kwargs ):
    pass

  def set_param( s, string, **kwargs ):
    # Assert no positional argumets
    # assert len( s._dsl.args ) == 0, \
    #   "Cannot use set_param because {} has positional arguments!".format(s._dsl.my_name)
    assert not s._dsl.constructed

    strs = string.split( "." )

    assert strs[0] == "top", "The component should start at top"
    assert '*' not in strs[-1], "We don't support * with function name!"

    assert len( strs ) >= 2
    func_name = strs[-1]
    strs = strs[1:-1]
    if s._dsl.param_tree is None:
      s._dsl.param_tree = ParamTreeNode()
    s._dsl.param_tree.add_params( strs, func_name, **kwargs )

  # There are two reason I refactored this function into two separate
  # functions. First of all in later levels of components, named objects
  # can be spawned after the previous monolithic elaborate and hence this
  # collect part won't capture them. Second, later levels can override
  # this function and simply call construct at the beginning and call
  # collect at the middle/end.

  #-----------------------------------------------------------------------
  # elaborate
  #-----------------------------------------------------------------------

  def _elaborate_construct( s ):

    if s._dsl.constructed:
      # Yanghui : Mute the warning for the isca tutorial.
      # warnings.warn( "Don't elaborate the same model twice. "
      #                "Use APIs to mutate the model." )
      return

    # Initialize the top level

    s._dsl.parent_obj = None
    s._dsl.level      = 0
    s._dsl.my_name    = "s"
    s._dsl.full_name  = "s"

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

  def _elaborate_collect_and_mark_all_named_objects( s ):
    s._dsl.all_named_objects = s._collect_all()[0]
    for c in s._dsl.all_named_objects:
      c._dsl.elaborate_top = s

  def elaborate( s ):
    s._elaborate_construct()
    s._elaborate_collect_and_mark_all_named_objects()

  #-----------------------------------------------------------------------
  # Post-elaborate public APIs (can only be called after elaboration)
  #-----------------------------------------------------------------------

  def is_component( s ):
    raise NotImplementedError

  def is_signal( s ):
    raise NotImplementedError

  def is_interface( s ):
    raise NotImplementedError

  # These two APIs are reused across Connectable and Component

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
