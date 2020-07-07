"""
========================================================================
Component.py
========================================================================
Add clk/reset signals.

Author : Yanghui Ou
  Date : Apr 6, 2019
"""

from .ComponentLevel1 import ComponentLevel1
from .ComponentLevel7 import ComponentLevel7
from .Connectable import (
    Connectable,
    Const,
    InPort,
    Interface,
    MethodPort,
    OutPort,
    Signal,
    Wire,
)
from .errors import (
    InvalidAPICallError,
    InvalidConnectionError,
    NotElaboratedError,
    UnsetMetadataError,
)
from .MetadataKey import MetadataKey
from .NamedObject import NamedObject
from .Placeholder import Placeholder


class Component( ComponentLevel7 ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def __new__( cls, *args, **kwargs ):
    inst = super().__new__( cls, *args, **kwargs )
    # Maps a MetadataKey instance to its value
    inst._metadata = {}
    return inst

  # Override
  def _construct( s ):

    if not s._dsl.constructed:

      # clk and reset signals are added here.
      s.clk   = InPort()
      s.reset = InPort()

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

      s._handle_decorated_methods()

      # Same as parent class _construct
      s.construct( *s._dsl.args, **kwargs )

      # We hook up the added clk and reset signals here. NOTE THAT if the
      # user overwrites clk/reset inside the component, we still get the
      # correct connection.
      parent = s.get_parent_object()
      if parent is not None:
        parent._connect_signal_signal( s.clk, parent.clk )
        parent._connect_signal_signal( s.reset, parent.reset )

      s._dsl.constructed = True

  # This function deduplicates those checks in each API
  def _check_called_at_elaborate_top( s, func_name ):
    try:
      if s._dsl.elaborate_top is not s:
        raise InvalidAPICallError( func_name, s, s._dsl.elaborate_top )
    except AttributeError:
      raise NotElaboratedError()

  def _collect_objects_local( s, filt, sort_key = None ):
    assert s._dsl.constructed
    ret = set()
    stack = []
    for (name, obj) in s.__dict__.items():
      if   isinstance( name, str ):
        if name[0] != '_': # filter private variables
          stack.append( obj )
    while stack:
      u = stack.pop()
      if filt( u ):
        ret.add( u )
      # ONLY LIST IS SUPPORTED
      elif isinstance( u, list ):
        stack.extend( u )
    if sort_key:
      return sorted( ret, key = sort_key )
    else:
      return list(ret)

  def _flush_pending_value_connections( s ):
    if s._dsl._has_pending_value_connections:
      s._dsl.all_value_nets = s._resolve_value_connections()
      s._dsl._has_pending_value_connections = False

  def _flush_pending_method_connections( s ):
    if s._dsl._has_pending_method_connections:
      s._dsl.all_method_nets = s._resolve_method_connections()
      s._dsl._has_pending_method_connections = False

  # These internal functions are implemented in a more generic way. The
  # public APIs should wrap around these functions.

  def _add_component( s, parent, name, indices, obj, provided_connections,
                      provided_upblk_reads, provided_upblk_writes, provided_upblk_calls,
                      provided_func_reads,  provided_func_writes, provided_func_calls ):
    try:
      top = s._dsl.elaborate_top
    except AttributeError:
      raise NotElaboratedError()

    NamedObject._elaborate_stack = [ parent ]

    # Check if we are adding obj to a list of to a component
    if not indices:
      # If we are adding field parent.x, we simply reuse the setattr hook
      assert not hasattr( parent, name ), f"Invalid add_component call: {parent} already has field {name}!"

      NamedObject.__setattr__ = NamedObject.__setattr_for_elaborate__
      setattr( parent, name, obj )
      del NamedObject.__setattr__

    else:
      assert hasattr( parent, name ), f"Invalid add_component call: Field '{name}' of {parent} should exist and be a list, but doesn't exist!"

      # We use the indices to get the list parent and set the element

      list_parent = getattr( parent, name )
      i = 0
      while i < len(indices) - 1:
        list_parent = list_parent[ indices[i] ]
        i += 1

      assert list_parent[ indices[i] ] is None, f"Invalid add_component call: {parent} already has field '{name}!'"
      list_parent[ indices[i] ] = obj

      # NOTE THAT we cannot use setattr hook for the top level metadata
      # because setting an element in the list doesn't call setattr.
      # As a result we have to copy some code from setattr hook and do it
      # manually here for the top level

      obj._dsl.parent_obj = parent
      obj._dsl.level      = parent._dsl.level + 1
      obj._dsl.my_name    = u_name = name + "".join( [ f"[{x}]" for x in indices ] )

      # Iterate through the param_tree and update u
      if parent._dsl.param_tree is not None:
        if parent._dsl.param_tree.children is not None:
          for comp_name, node in parent._dsl.param_tree.children.items():
            if comp_name == u_name:
              # Lazily create the param tree
              if obj._dsl.param_tree is None:
                obj._dsl.param_tree = ParamTreeNode()
              obj._dsl.param_tree.merge( node )

            elif node.compiled_re is not None:
              if node.compiled_re.match( u_name ):
                # Lazily create the param tree
                if obj._dsl.param_tree is None:
                  obj._dsl.param_tree = ParamTreeNode()
                obj._dsl.param_tree.merge( node )

      obj._dsl.full_name = ( parent._dsl.full_name + "." + u_name )

      # store the name/indices
      obj._dsl._my_name     = name
      obj._dsl._my_indices  = indices

      obj._dsl.elaborate_top = top
      obj._dsl.NamedObject_fields = set()

      NamedObject._elaborate_stack.append( obj )
      NamedObject.__setattr__ = NamedObject.__setattr_for_elaborate__
      obj._construct()
      del NamedObject.__setattr__

      NamedObject._elaborate_stack.pop()

    added_components = obj._collect_all_single( lambda x: isinstance( x, Component ) )

    # First elaborate all functions to spawn more named objects
    for c in added_components:
      c._elaborate_read_write_func()

    added_signals, added_method_ports = \
      obj._collect_all( [ lambda x: isinstance( x, Signal ), \
                          lambda x: isinstance( x, MethodPort ) ] )

    top._dsl.all_components    |= added_components
    top._dsl.all_signals       |= added_signals
    top._dsl.all_method_ports  |= added_method_ports

    top._dsl.all_named_objects |= added_components
    top._dsl.all_named_objects |= added_signals
    top._dsl.all_named_objects |= added_method_ports

    for c in added_components:
      top._collect_vars( c )

    # Lazy -- to avoid resolve_connection call which takes non-trivial
    # time upon adding any connect, I just mark pending here. Whenever you
    # call the right API which is get_all_value_nets()/get_method_nets(),
    # the API will batch flush all pending connections if the flag is
    # true. So please make sure to call the API whenever you want to get
    # the value/method nets.
    connection_pairs = []
    for (x, y) in provided_connections:
      connection_pairs.append( x )
      connection_pairs.append( eval(y) )
      if not top._dsl._has_pending_value_connections and isinstance( x, Signal ):
        top._dsl._has_pending_value_connections = True
      if not top._dsl._has_pending_method_connections and isinstance( x, MethodPort ):
        top._dsl._has_pending_method_connections = True

    # WE NEED TO ADD CONNECTIONS AT PARENT INSTEAD OF TOP
    parent.add_connections( *connection_pairs )

    # Now we put back the provided upblk metadata to parent and top
    for blk, obj_name in provided_upblk_reads:
      parent._dsl.upblk_reads[blk].add( eval(obj_name) )

    for blk, obj_name in provided_upblk_writes:
      parent._dsl.upblk_writes[blk].add( eval(obj_name) )

    for blk, obj_name in provided_upblk_calls:
      parent._dsl.upblk_calls[blk].add( eval(obj_name) )

    for func, obj_name in provided_func_reads:
      parent._dsl.func_reads[func].add( eval(obj_name) )

    for func, obj_name in provided_func_writes:
      parent._dsl.func_writes[func].add( eval(obj_name) )

    for func, obj_name in provided_func_calls:
      parent._dsl.func_calls[func].add( eval(obj_name) )

    del NamedObject._elaborate_stack

  def _delete_component( top, obj ):

    # This nested delete function is to create an extra layer to properly
    # call garbage collector. If we can make sure it is collected
    # automatically and fast enough, we might remove this extra layer
    #
    # EDIT: After experimented w/ and w/o gc.collect(), it seems like it
    # is eventually collected, but sometimes the intermediate memory
    # footprint might reach up to gigabytes, so let's keep the
    # gc.collect() for now

    def _delete_component_internal( top, foo ):
      assert obj._dsl.elaborate_top is top

      # First make sure we flush pending connections
      value_nets  = top.get_all_value_nets()
      method_nets = top.get_all_method_nets()

      # Delete the placeholder from parent. We need to see if we are
      # dealing with a list parent or a component parent.

      parent = foo.get_parent_object()

      if foo._dsl._my_indices:
        # We use the saved indices to get the list parent and set the index
        my_indices = foo._dsl._my_indices
        list_parent = getattr( parent, foo._dsl._my_name )
        i = 0
        while i < len(my_indices) - 1:
          list_parent = list_parent[ my_indices[i] ]
          i += 1
        list_parent[ my_indices[i] ] = None
      else:
        # Simply delete the attribute if it's merely a field
        delattr( parent, foo._dsl.my_name )
        parent._dsl.NamedObject_fields.remove( foo._dsl.my_name )

      # Remove all components, signals, and method ports
      removed_components, removed_signals, removed_method_ports = \
        foo._collect_all( [ lambda x: isinstance( x, Component ), \
                            lambda x: isinstance( x, Signal ), \
                            lambda x: isinstance( x, MethodPort ) ] )

      top._dsl.all_components    -= removed_components
      top._dsl.all_signals       -= removed_signals
      top._dsl.all_method_ports  -= removed_method_ports

      top._dsl.all_named_objects -= removed_components

      removed_connectables = removed_signals | removed_method_ports
      top._dsl.all_named_objects -= removed_connectables

      removed_consts = set()
      if isinstance( foo, Placeholder ):
        # No need to uncollect vars from a placeholder
        assert not foo._dsl.consts
      else:
        for x in removed_components:
          # remove consts
          removed_consts |= x._dsl.consts
          # uncollect variables
          top._uncollect_vars( x )

      saved_upblk_reads  = []
      saved_upblk_writes = []
      saved_upblk_calls  = []
      saved_func_reads   = []
      saved_func_writes  = []
      saved_func_calls   = []

      # If an update block/function in parent writes the inport or reads
      # the outport or calls a callee method of the deleted component, we
      # must save the information (upA reads B) to avoid bugs or
      # explicitly re-elaborating the parent.

      for blk, reads in parent._dsl.upblk_reads.items():
        assert blk in top._dsl.all_upblk_reads
        to_save = set()
        for x in reads:
          if x in removed_connectables:
            to_save.add( x )
            saved_upblk_reads.append( (blk, repr(x)) )
        parent._dsl.upblk_reads[blk] -= to_save

      for blk, writes in parent._dsl.upblk_writes.items():
        assert blk in top._dsl.all_upblk_writes
        to_save = set()
        for x in writes:
          if x in removed_connectables:
            to_save.add( x )
            saved_upblk_writes.append( (blk, repr(x)) )
        parent._dsl.upblk_writes[blk] -= to_save

      for blk, calls in parent._dsl.upblk_calls.items():
        assert blk in top._dsl.all_upblk_calls
        to_save = set()
        for x in calls:
          if x in removed_connectables:
            to_save.add( x )
            saved_upblk_calls.append( (blk, repr(x)) )
        parent._dsl.upblk_calls[blk] -= to_save

      # We need to save the information for funcs too
      for func, reads in parent._dsl.func_reads.items():
        to_save = set()
        for x in reads:
          if x in removed_connectables:
            to_save.add( x )
            saved_func_reads.append( (func, repr(x)) )
        parent._dsl.func_reads[func] -= to_save

      for func, writes in parent._dsl.func_writes.items():
        to_save = set()
        for x in writes:
          if x in removed_connectables:
            to_save.add( x )
            saved_func_writes.append( (func, repr(x)) )
        parent._dsl.func_writes[func] -= to_save

      for func, calls in parent._dsl.func_calls.items():
        to_save = set()
        for x in calls:
          if x in removed_connectables:
            to_save.add( x )
            saved_func_calls.append( (func, repr(x)) )
        parent._dsl.func_calls[func] -= to_save

      saved_connections = []

      for x in removed_connectables:
        # Clean up all_adjancency at top
        if x in top._dsl.all_adjacency:
          for other in top._dsl.all_adjacency[x]:
            # other must be in the dict
            # If other will be removed, we don't need to remove it here ..
            if other not in removed_connectables and other not in removed_consts:
              top._dsl.all_adjacency[other].remove( x )
              if isinstance( other, Const ):
                other = other._dsl.const
              saved_connections.append( (other, "top"+repr(x)[1:]) ) # other is from outside
          del top._dsl.all_adjacency[x]

        # Clean up adjacency at parent
        if x in parent._dsl.adjacency:
          for other in parent._dsl.adjacency[x]:
            # other must be in the dict
            if other not in removed_connectables:
              parent._dsl.adjacency[other].remove( x )
          del parent._dsl.adjacency[x]

      for x in removed_components:
        del x._dsl.parent_obj
        del x._dsl.elaborate_top
      for x in removed_connectables:
        del x._dsl.parent_obj
        del x._dsl.elaborate_top
        x._dsl.full_name = "<deleted>"+x._dsl.full_name
      for y in removed_consts:
        del y._dsl.parent_obj

      # We don't break nets anymore. Instead, we set the flags to true so
      # that the next get_xxx_net will immediately recollect nets.
      top._dsl._has_pending_value_connections = True
      top._dsl._has_pending_method_connections = True

      # We clean up the connect_order list. If we want to preserve the
      # original connect order, we can play some other tricks here such as
      # leaving the strings in there. However I don't think that's clean
      # enough. Thus I'm just removing them right now.
      new_connect_order = []
      for (x, y) in parent._dsl.connect_order:
        if x not in removed_signals and y not in removed_signals: # TODO method port
          new_connect_order.append( (x, y) )

      parent._dsl.connect_order = new_connect_order

      return saved_connections, saved_upblk_reads, saved_upblk_writes, saved_upblk_calls, \
             saved_func_reads, saved_func_writes, saved_func_calls

    return _delete_component_internal( top, obj )
    # import gc
    # gc.collect() # this takes 0.1 seconds

  # Override, add pypy hooks
  def elaborate( s ):
    try:
      import pypyjit
      pypyjit.set_param("off")
    except:
      pass

    super().elaborate()

    # try:
      # import pypyjit
      # pypyjit.set_param("default")
    # except:
      # pass

  #-----------------------------------------------------------------------
  # Public APIs (can be called either before or after elaboration)
  #-----------------------------------------------------------------------

  """ Metadata APIs """

  def set_metadata( s, key, value ):
    """Set the metadata ``key`` of the given component to be ``value``.

    Can be called before, during, or after elaboration.

    Args:
        key (MetadataKey): Key of the metadata.
        value (object): The metadata. Can be any object.
    """
    key.check_value( value )
    s._metadata[ key ] = value

  def has_metadata( s, key ):
    """Check if the component has metadata for ``key``.

    Can be called before, during, or after elaboration.

    Args:
        key (MetadataKey): Key of the metadata.

    Returns:
        bool: Whether or not the component has the metadata for ``key``.

    Raises:
        TypeError: Raised if ``key`` is not an instance of :class:`MetadataKey`.
    """
    if not isinstance( key, MetadataKey ):
      raise TypeError(f'the given object {key} is not a MetadataKey!')
    return key in s._metadata

  def get_metadata( s, key ):
    """Get the metadata ``key`` of the given component.

    Can be called before, during, or after elaboration.

    Args:
        key (MetadataKey): Key of the metadata.

    Returns:
        object: The metadata of the given ``key``.

    Raises:
        TypeError: Raised if ``key`` is not an instance of :class:`MetadataKey`.
        UnsetMetadataError: Raised if the component does not have metadata for
            the given ``key``.
    """
    if not s.has_metadata( key ):
      raise UnsetMetadataError( key, s )
    return s._metadata[ key ]

  #-----------------------------------------------------------------------
  # Post-elaborate public APIs (can only be called after elaboration)
  #-----------------------------------------------------------------------

  """ Convenience/utility APIs """

  def apply( s, pass_instance ):
    try:
      import pypyjit
      pypyjit.set_param("off")
    except:
      pass
    if not hasattr( s._dsl, "elaborate_top" ):
      s.elaborate()

    assert type(pass_instance) is not type, f"Should pass in a pass instance like " \
                                            f"'{pass_instance.__name__}()' instead of '{pass_instance.__name__}'"
    assert callable( pass_instance ), f"Should override __call__ of {pass_instance.__name__} for a valid pass"
    pass_instance( s )

  def check( s ):
    s._check_valid_dsl_code()

  """ APIs that provide local metadata of a component """

  def get_component_level( s ):
    try:
      return s._dsl.level
    except AttributeError:
      raise NotElaboratedError()

  def get_child_components( s, sort_key = None ):
    return s._collect_objects_local( lambda x: isinstance( x, Component ), sort_key )

  def get_input_value_ports( s, sort_key = None ):
    return s._collect_objects_local( lambda x: isinstance( x, InPort ), sort_key )

  def get_output_value_ports( s , sort_key = None ):
    return s._collect_objects_local( lambda x: isinstance( x, OutPort ), sort_key )

  def get_wires( s , sort_key = None ):
    return s._collect_objects_local( lambda x: isinstance( x, Wire ), sort_key )

  def get_update_blocks( s ):
    assert s._dsl.constructed
    return s._dsl.upblks

  def get_update_ff( s ):
    assert s._dsl.constructed
    return s._dsl.update_ff

  def get_upblk_metadata( s ):
    assert s._dsl.constructed
    return s._dsl.upblk_reads, s._dsl.upblk_writes, s._dsl.upblk_calls

  # These xxx_order APIs should be used when some pass wants to process
  # connections/upblks in the order that they are created

  def get_connect_order( s ):
    try:
      return s._dsl.connect_order
    except AttributeError:
      raise NotElaboratedError()

  def get_update_block_order( s ):
    try:
      return s._dsl.upblk_order
    except AttributeError:
      raise NotElaboratedError()

  """ Metadata APIs that should only be called at elaborated top"""

  def get_all_object_filter( s, filt ):
    assert callable( filt )
    try:
      return { x for x in s._dsl.all_named_objects if filt(x) }
    except AttributeError:
      return s._collect_all_single( filt )

  def get_local_object_filter( s, filt, sort_key = None ):
    assert callable( filt )
    return s._collect_objects_local( filt, sort_key )

  def get_all_components( s ):
    try:
      s._check_called_at_elaborate_top( "get_all_update_blocks" )
      return s._dsl.all_components
    except AttributeError:
      raise NotElaboratedError()

  def get_all_update_blocks( s ):
    try:
      s._check_called_at_elaborate_top( "get_all_update_blocks" )
      return s._dsl.all_upblks
    except AttributeError:
      raise NotElaboratedError()

  def get_all_update_ff( s ):
    try:
      s._check_called_at_elaborate_top( "get_all_update_ff" )
      return s._dsl.all_update_ff
    except AttributeError:
      raise NotElaboratedError()

  def get_all_update_once( s ):
    try:
      s._check_called_at_elaborate_top( "get_all_update_once" )
      return s._dsl.all_update_once
    except AttributeError:
      raise NotElaboratedError()

  def get_all_upblk_metadata( s ):
    try:
      s._check_called_at_elaborate_top( "get_all_upblk_metadata" )
      return s._dsl.all_upblk_reads, s._dsl.all_upblk_writes, s._dsl.all_upblk_calls
    except AttributeError:
      raise NotElaboratedError()

  def get_all_explicit_constraints( s ):
    try:
      s._check_called_at_elaborate_top( "get_all_explicit_constraints" )
      return s._dsl.all_U_U_constraints, s._dsl.all_RD_U_constraints, \
             s._dsl.all_WR_U_constraints, s._dsl.all_M_constraints
    except AttributeError:
      raise NotElaboratedError()

  # is_lambda?, src, line, filename, ast
  def get_update_block_info( s, blk ):
    try:
      name_info = s.__class__._name_info
    except AttributeError: # This component doesn't have update block
      return None

    return name_info[blk.__name__]

  def get_update_block_host_component( s, blk ):
    try:
      s._check_called_at_elaborate_top( "get_update_block_host_component" )
      return s._dsl.all_upblk_hostobj[ blk ]
    except AttributeError:
      raise NotElaboratedError()

  def get_all_method_nets( s ):
    s._check_called_at_elaborate_top( "get_all_method_nets" )
    s._flush_pending_method_connections()
    return s._dsl.all_method_nets

  # Override
  def get_all_value_nets( s ):
    s._check_called_at_elaborate_top( "get_all_value_nets" )
    s._flush_pending_value_connections()
    return s._dsl.all_value_nets

  def get_signal_adjacency_dict( s ):
    try:
      s._check_called_at_elaborate_top( "get_signal_adjacency_dict" )
    except AttributeError:
      raise NotElaboratedError()
    return s._dsl.all_adjacency

  """ Mutation APIs to add/delete components and connections"""

  # Shunning: These API implement replacing a component with another
  # module. This is the first mutation API we want to test thoroughly

  # TODO test everything below and figure out whether we need to delete
  # a normal component

  def replace_component( top, foo, cls, check=True ):
    top._check_called_at_elaborate_top( "replace_component" )

    parent = foo.get_parent_object()
    foo_name    = foo._dsl._my_name
    foo_indices = foo._dsl._my_indices

    saved_connections, saved_upblk_reads, saved_upblk_writes, saved_upblk_calls, \
      saved_func_reads, saved_func_writes, saved_func_calls = top._delete_component( foo )

    new_obj = cls( *foo._dsl.args, **foo._dsl.kwargs )

    # We actually don't need to merge param tree here because when we call
    # _add_component, the parameters stored in parent will be pushed down
    # to new_obj
    top._add_component( parent, foo_name, foo_indices, new_obj, saved_connections,
                        saved_upblk_reads, saved_upblk_writes, saved_upblk_calls,
                        saved_func_reads, saved_func_writes, saved_func_calls)

    top._flush_pending_value_connections()
    top._flush_pending_method_connections()
    if check:
      top.check()

  def replace_component_with_obj( top, foo, new_obj, check=True ):
    top._check_called_at_elaborate_top( "replace_component" )

    parent = foo.get_parent_object()
    foo_name    = foo._dsl._my_name
    foo_indices = foo._dsl._my_indices

    saved_connections, saved_upblk_reads, saved_upblk_writes, saved_upblk_calls, \
      saved_func_reads, saved_func_writes, saved_func_calls = top._delete_component( foo )

    # We actually don't need to merge param tree here because when we call
    # _add_component, the parameters stored in parent will be pushed down
    # to new_obj
    top._add_component( parent, foo_name, foo_indices, new_obj, saved_connections,
                        saved_upblk_reads, saved_upblk_writes, saved_upblk_calls,
                        saved_func_reads, saved_func_writes, saved_func_calls)

    top._flush_pending_value_connections()
    top._flush_pending_method_connections()
    if check:
      top.check()

  def add_value_port( top, parent, name, o ):
    top._check_called_at_elaborate_top( "add_port" )

    assert isinstance( o, (InPort, OutPort) )
    # If we are adding field parent.x, we simply reuse the setattr hook
    assert not hasattr( parent, name ), f"Invalid add_value_port call: {parent} already has field {name}!"

    NamedObject._elaborate_stack = [ parent ]
    NamedObject.__setattr__ = NamedObject.__setattr_for_elaborate__
    setattr( parent, name, o )
    del NamedObject.__setattr__
    del NamedObject._elaborate_stack

    top._dsl.all_signals.add( o )
    top._dsl.all_named_objects.add( o )

  def add_connection( top, o1, o2 ):

    # Currently only support connecting signals

    top._check_called_at_elaborate_top( "add_connection" )
    if isinstance( o2, Connectable ): o1, o2 = o2, o1

    assert isinstance( o1, Connectable ), "Cannot connect two non-connectable objects"

    assert isinstance( o1, Signal ), "Currently only support connecting signals/constants"

    assert o1._dsl.elaborate_top is top

    # Add the connection to the correct component
    host1   = o1.get_host_component()
    parent1 = host1.get_parent_object()

    real_host = host1

    if isinstance( o2, Signal ):
      assert o2._dsl.elaborate_top is top

      host2   = o2.get_host_component()
      parent2 = host2.get_parent_object()

      if isinstance( o1, InPort ):
        if isinstance( o2, InPort ):
          if host1 is parent2:
            host1._connect_signal_signal( o1, o2 )
          elif host2 is parent1:
            host2._connect_signal_signal( o1, o2 )
            real_host = host2
          else:
            assert False

        # OutPort-Wire -> same host or wire is out's parent
        elif isinstance( o2, Wire ):
          assert host1 is host2 or host2 is parent1
          host2._connect_signal_signal( o1, o2 )
          real_host = host2

        # InPort-OutPort: enforce same host. it doesn't make much sense
        # to have outport in inport's parent
        elif isinstance( o2, OutPort ):
          assert host1 is host2
          host1._connect_signal_signal( o1, o2 )

        else:
          assert False

      elif isinstance( o1, OutPort ):
        if isinstance( o2, OutPort ):
          if host1 is parent2:
            host1._connect_signal_signal( o1, o2 )
          elif host2 is parent1:
            host2._connect_signal_signal( o1, o2 )
            real_host = host2
          else:
            assert False

        # OutPort-InPort: enforce same host. it doesn't make much sense
        # to have outport in inport's parent
        elif isinstance( o2, InPort ):
          assert host1 is host2
          host1._connect_signal_signal( o1, o2 )

        # OutPort-Wire -> same host or wire is out's parent
        elif isinstance( o2, Wire ):
          assert host1 is host2 or host2 is parent1
          host2._connect_signal_signal( o1, o2 )
          real_host = host2

        else:
          assert False

      elif isinstance( o1, Wire ):
        # Wire-Wire -> same host
        if isinstance( o2, Wire ):
          assert host1 is host2
          host1._connect_signal_signal( o1, o2 )
        # Wire-InPort/OutPort -> same host or wire is in/out's parent
        else:
          assert host1 is host2 or host1 is parent2
          host1._connect_signal_signal( o1, o2 )

      else:
        assert False

      top._dsl.all_adjacency[o1].add(o2)
      top._dsl.all_adjacency[o2].add(o1)
      top._dsl._has_pending_value_connections = True

  def add_connections( s, *args ):
    try:
      top = s._dsl.elaborate_top
    except AttributeError:
      raise NotElaboratedError()

    if len(args) & 1 != 0:
       raise InvalidConnectionError( "Odd number ({}) of objects provided.".format( len(args) ) )

    for i in range(len(args)>>1):
      try:
        s._connect( args[ i<<1 ], args[ (i<<1)+1 ], internal=False )
      except InvalidConnectionError as e:
        raise InvalidConnectionError( "\n- In connect_pair, when connecting {}-th argument to {}-th argument\n{}\n " \
              .format( (i<<1)+1, (i<<1)+2 , e ) )

    for x, adjs in s._dsl.adjacency.items():
      top._dsl.all_adjacency[x].update( adjs )

  # TODO implement everything below and test them

  # Override
  def add_component_by_name( s, name, obj, provided_connections=[] ):
    raise NotImplementedError()

  # Override
  def delete_component( s, name ):
    raise NotImplementedError()

  # Do we still need disconnect and disconnect_pair?
