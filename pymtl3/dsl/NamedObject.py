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
import re
from collections import deque

from .errors import FieldReassignError, NotElaboratedError


class DSLMetadata:
  pass

# Special data structure for constructing the parameter tree.
class ParamTreeNode:
  def __init__( self ):
    self.compiled_re = None
    self.children = None
    self.leaf = None

  # TODO do we still need to lazily create leaf?
  def merge( self, other ):
    # Merge leaf
    if other.leaf is not None:
      # Lazily create leaf
      if self.leaf is None:
        self.leaf = {}
      for func_name, subdict in other.leaf.items():
        if func_name not in self.leaf:
          self.leaf[ func_name ] = {}
        self.leaf[ func_name ].update( subdict )

    # Merge children
    if other.children is not None:
      # Lazily create children
      if self.children is None:
        self.children = {}
      for comp_name, node in other.children.items():
        if comp_name in self.children:
          self.children[ comp_name ].merge( node )
        else:
          self.children[ comp_name ] = node

  def add_params( self, strs, func_name, **kwargs ):

    if self.leaf is None:
      self.leaf = {}
      self.children = {}

    # Traverse to the node
    cur_node = self
    idx = 1
    for comp_name in strs:
      # Lazily create children
      if cur_node.children is None:
        cur_node.children = {}
      if comp_name not in cur_node.children:
        new_node = ParamTreeNode()
        if '*' in comp_name:
          new_node.compiled_re = re.compile( comp_name )
          # Recursively update exisiting nodes that matches the regex
          for name, node in cur_node.children.items():
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
    return f"\nleaf:{self.leaf}\nchildren:{self.children}"

class NamedObject:

  def __new__( cls, *args, **kwargs ):

    inst = super().__new__( cls )
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

    # I use non-recursive BFS to reduce error message depth

    if name[0] != '_': # filter private variables
      sd = s._dsl

      # Shunning: here I optimize for common cases where the object is a NamedObject.
      # I used to push the object directly to a stack to reuse the code across
      # both NamedObject and list cases. Now I basically avoid the stack overheads
      # for common cases.
      if isinstance( obj, NamedObject ):
        fields = sd.NamedObject_fields
        if name in fields:
          if getattr( s, name ) is obj:
            return
          raise FieldReassignError(f"The attempt to assign hardware construct to field {name} is illegal:\n"
                                   f" - top{repr(s)[1:]} already has field {name} with type {type(getattr( s, name ))}.")
        fields.add( name )

        ud = obj._dsl

        ud.parent_obj = s
        ud.level      = sd.level + 1

        ud._my_name  = ud.my_name = name
        ud.full_name = f"{sd.full_name}.{name}"

        ud._my_indices = None

        # Iterate through the param_tree and update u
        if sd.param_tree is not None:
          if sd.param_tree.children is not None:
            for comp_name, node in sd.param_tree.children.items():
              if comp_name == name:
                # Lazily create the param tree
                if ud.param_tree is None:
                  ud.param_tree = ParamTreeNode()
                ud.param_tree.merge( node )

              elif node.compiled_re is not None:
                if node.compiled_re.match( name ):
                  # Lazily create the param tree
                  if ud.param_tree is None:
                    ud.param_tree = ParamTreeNode()
                  ud.param_tree.merge( node )

        ud.NamedObject_fields = set()

        # Point u's top to my top
        top = ud.elaborate_top = sd.elaborate_top

        NamedObject._elaborate_stack.append( obj )
        obj._construct()
        NamedObject._elaborate_stack.pop()

      # ONLY LIST IS SUPPORTED, SORRY.
      # I don't want to support any iterable object because later "Wire"
      # can be infinitely iterated and cause infinite loop. Special
      # casing Wire will be a mess around everywhere.

      elif isinstance( obj, list ) and obj and isinstance( obj[0], (NamedObject, list) ):
        fields = sd.NamedObject_fields
        if name in fields:
          if getattr( s, name ) is obj:
            return
          raise FieldReassignError(f"The attempt to assign hardware construct to field {name} is illegal:\n"
                                   f" - top{repr(s)[1:]} already has field {name} with type {type(getattr( s, name ))}.")
        fields.add( name )

        Q = deque( (u, (i,)) for i, u in enumerate(obj) )

        while Q:
          u, indices = Q.popleft()

          if isinstance( u, NamedObject ):
            ud = u._dsl

            ud.parent_obj = s
            ud.level      = sd.level + 1

            ud._my_name  = name
            ud.my_name   = u_name = name + "".join( [ f"[{x}]" for x in indices ] )
            ud.full_name = f"{sd.full_name}.{u_name}"

            ud._my_indices = indices

            # Iterate through the param_tree and update u
            if sd.param_tree is not None:
              if sd.param_tree.children is not None:
                for comp_name, node in sd.param_tree.children.items():
                  if comp_name == u_name:
                    # Lazily create the param tree
                    if ud.param_tree is None:
                      ud.param_tree = ParamTreeNode()
                    ud.param_tree.merge( node )

                  elif node.compiled_re is not None:
                    if node.compiled_re.match( u_name ):
                      # Lazily create the param tree
                      if ud.param_tree is None:
                        ud.param_tree = ParamTreeNode()
                      ud.param_tree.merge( node )

            ud.NamedObject_fields = set()

            # Point u's top to my top
            top = ud.elaborate_top = sd.elaborate_top

            NamedObject._elaborate_stack.append( u )
            u._construct()
            NamedObject._elaborate_stack.pop()

          elif isinstance( u, list ):
            Q.extend( (v, indices+(i,)) for i, v in enumerate(u) )

    super().__setattr__( name, obj )

  def _collect_all_single( s, filt=lambda x: isinstance( x, NamedObject ) ):
    ret = set()
    stack = [s]
    while stack:
      u = stack.pop()

      if   isinstance( u, NamedObject ):
        if filt( u ): # Check if m satisfies the filter
          ret.add( u )

        for name, obj in u.__dict__.items():

          # If the id is string, it is a normal children field. Otherwise it
          # should be an tuple that represents a slice

          if   isinstance( name, str ):
            if name[0] != '_': # filter private variables
              stack.append( obj )

          elif isinstance( name, tuple ): # name = [1:3]
            stack.append( obj )

      # ONLY LIST IS SUPPORTED
      elif isinstance( u, list ):
        stack.extend( u )
    return ret

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

        for name, obj in u.__dict__.items():

          # If the id is string, it is a normal children field. Otherwise it
          # should be an tuple that represents a slice

          if   isinstance( name, str ):
            if name[0] != '_': # filter private variables
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
      return super().__repr__()

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

    s._dsl.parent_obj    = None
    s._dsl.level         = 0
    s._dsl.my_name       = "s"
    s._dsl.full_name     = "s"
    s._dsl.elaborate_top = s
    s._dsl.NamedObject_fields = set()

    # Secret sauce for letting the child know the field name of itself
    # -- override setattr for elaboration, and remove it afterwards
    # -- and the global elaborate to enable free function as decorator

    NamedObject.__setattr__ = NamedObject.__setattr_for_elaborate__
    NamedObject._elaborate_stack = [ s ]

    try:
      s._construct()
    except Exception:
      # re-raise here after deleting __setattr__
      del NamedObject.__setattr__ # not harming the rest of execution
      del NamedObject._elaborate_stack
      raise

    del NamedObject.__setattr__
    del NamedObject._elaborate_stack

  def _elaborate_collect_all_named_objects( s ):
    s._dsl.all_named_objects = s._collect_all_single()

  def elaborate( s ):
    s._elaborate_construct()
    s._elaborate_collect_all_named_objects()

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
