"""
========================================================================
Component.py
========================================================================
Add clk/reset signals.

Author : Yanghui Ou
  Date : Apr 6, 2019
"""
from __future__ import absolute_import, division, print_function

from collections import defaultdict

from pymtl3.datatypes import Bits1

from .ComponentLevel1 import ComponentLevel1
from .ComponentLevel7 import ComponentLevel7
from .Connectable import Const, InPort, Interface, MethodPort, OutPort, Signal, Wire
from .errors import InvalidAPICallError, InvalidConnectionError, NotElaboratedError
from .NamedObject import NamedObject
from .Placeholder import Placeholder


class Component( ComponentLevel7 ):

  # Override
  def _construct( s ):

    if not s._dsl.constructed:

      # clk and reset signals are added here.
      s.clk   = InPort( Bits1 )
      s.reset = InPort( Bits1 )

      # Merge the actual keyword args and those args set by set_parameter
      if s._dsl.param_tree is None:
        kwargs = s._dsl.kwargs
      elif s._dsl.param_tree.leaf is None:
        kwargs = s._dsl.kwargs
      else:
        kwargs = s._dsl.kwargs.copy()
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
        parent.connect( s.clk, parent.clk )
        parent.connect( s.reset, parent.reset )

      if s._dsl.call_kwargs is not None: # s.a = A()( b = s.b )
        s._continue_call_connect()

      s._dsl.constructed = True

  # This function deduplicates those checks in each API
  def _check_called_at_elaborate_top( s, func_name ):
    try:
      if s._dsl.elaborate_top is not s:
        raise InvalidAPICallError( func_name, s, s._dsl.elaborate_top )
    except AttributeError:
      raise NotElaboratedError()

  def _collect_objects_local( s, filt ):
    assert s._dsl.constructed
    ret = set()
    stack = []
    for (name, obj) in s.__dict__.iteritems():
      if   isinstance( name, basestring ): # python2 specific
        if not name.startswith("_"): # filter private variables
          stack.append( obj )
    while stack:
      u = stack.pop()
      if filt( u ):
        ret.add( u )
      # ONLY LIST IS SUPPORTED
      elif isinstance( u, list ):
        stack.extend( u )
    return ret

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

    # Check if we are adding obj to a list of to a component
    if not indices:
      # If we are adding field s.x, we simply reuse the setattr hook
      assert not hasattr( s, name )
      NamedObject.__setattr__ = NamedObject.__setattr_for_elaborate__
      setattr( parent, name, obj )
      del NamedObject.__setattr__

    else:
      assert hasattr( s, name )

      # We use the indices to get the list parent and set the element

      list_parent = getattr( parent, name )
      i = 0
      while i < len(indices) - 1:
        list_parent = list_parent[ indices[i] ]
        i += 1
      list_parent[ indices[i] ] = obj

      # NOTE THAT we cannot use setattr hook for the top level metadata
      # because setting an element in the list doesn't call setattr.
      # As a result we have to copy some code from setattr hook and do it
      # manually here for the top level

      obj._dsl.parent_obj = parent
      obj._dsl.level      = parent._dsl.level + 1
      obj._dsl.my_name    = u_name = name + "".join( [ "[{}]".format(x)
                                                     for x in indices ] )

      # Iterate through the param_tree and update u
      if parent._dsl.param_tree is not None:
        if parent._dsl.param_tree.children is not None:
          for comp_name, node in parent._dsl.param_tree.children.iteritems():
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

      NamedObject.__setattr__ = NamedObject.__setattr_for_elaborate__
      obj._construct()
      del NamedObject.__setattr__

    added_components = obj._collect_all( [ lambda x: isinstance( x, Component ) ] )[0]

    # First elaborate all functions to spawn more named objects
    for c in added_components:
      c._dsl.elaborate_top = top
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

    for c in added_signals | added_method_ports:
      c._dsl.elaborate_top = top

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
      for x in removed_connectables:
        del x._dsl.parent_obj
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

  #-----------------------------------------------------------------------
  # Post-elaborate public APIs (can only be called after elaboration)
  #-----------------------------------------------------------------------

  """ Convenience/utility APIs """

  def apply( s, *args ):

    if isinstance(args[0], list):
      assert len(args) == 1
      for step in args[0]:
        step( s )

    elif len(args) == 1:
      assert callable( args[0] )
      args[0]( s )

  # Simulation related APIs
  def sim_reset( s ):
    s._check_called_at_elaborate_top( "sim_reset" )

    s.reset = Bits1( 1 )
    s.tick() # Tick twice to propagate the reset signal
    s.tick()
    s.reset = Bits1( 0 )

  def check( s ):
    s._check_valid_dsl_code()

  # TODO maybe we should implement these two lock/unlock APIs as passes?
  # They expose kernel implementation details though ...
  def lock_in_simulation( s ):
    s._check_called_at_elaborate_top( "lock_in_simulation" )

    s._dsl.swapped_signals = defaultdict(list)
    s._dsl.swapped_values  = defaultdict(list)

    def cleanup_connectables( current_obj, host_component ):

      # Deduplicate code. Choose operation based on type of current_obj
      if isinstance( current_obj, list ):
        iterable = enumerate( current_obj )
        is_list = True
      elif isinstance( current_obj, NamedObject ):
        iterable = current_obj.__dict__.iteritems()
        is_list = False
      else:
        return

      for i, obj in iterable:
        if not is_list and i.startswith("_"): # impossible to have tuple
          continue

        if   isinstance( obj, Component ):
          cleanup_connectables( obj, obj )

        elif isinstance( obj, (Interface, list) ):
          cleanup_connectables( obj, host_component )

        elif isinstance( obj, Signal ):
          try:
            if is_list: current_obj[i] = obj.default_value()
            else:       setattr( current_obj, i, obj.default_value() )
          except Exception as err:
            err.message = repr(obj) + " -- " + err.message
            err.args = (err.message,)
            raise err
          s._dsl.swapped_signals[ host_component ].append( (current_obj, i, obj, is_list) )

    cleanup_connectables( s, s )
    s._dsl.locked_simulation = True

  def unlock_simulation( s ):
    s._check_called_at_elaborate_top( "unlock_simulation" )
    try:
      assert s._dsl.locked_simulation
    except:
      raise AttributeError("Cannot unlock an unlocked/never locked model.")

    for component, records in s._dsl.swapped_signals.iteritems():
      for current_obj, i, obj, is_list in records:
        if is_list:
          s._dsl.swapped_values[ component ] = ( current_obj, i, current_obj[i], is_list )
          current_obj[i] = obj
        else:
          s._dsl.swapped_values[ component ] = ( current_obj, i, getattr(current_obj, i), is_list )
          setattr( current_obj, i, obj )

    s._dsl.locked_simulation = False

  """ APIs that provide local metadata of a component """

  def get_component_level( s ):
    try:
      return s._dsl.level
    except AttributeError:
      raise NotElaboratedError()

  def get_child_components( s ):
    return s._collect_objects_local( lambda x: isinstance( x, Component ) )

  def get_input_value_ports( s ):
    return s._collect_objects_local( lambda x: isinstance( x, InPort ) )

  def get_output_value_ports( s ):
    return s._collect_objects_local( lambda x: isinstance( x, OutPort ) )

  def get_wires( s ):
    return s._collect_objects_local( lambda x: isinstance( x, Wire ) )

  def get_update_blocks( s ):
    assert s._dsl.constructed
    return s._dsl.upblks

  def get_update_on_edge( s ):
    assert s._dsl.constructed
    return s._dsl.update_on_edge

  def get_upblk_metadata( s ):
    assert s._dsl.constructed
    return s._dsl.upblk_reads, s._dsl.upblk_writes, s._dsl.upblk_calls

  def get_connect_order( s ):
    try:
      return s._dsl.connect_order
    except AttributeError:
      raise NotElaboratedError()

  """ Metadata APIs that should only be called at elaborated top"""

  def get_all_object_filter( s, filt ):
    assert callable( filt )
    try:
      return { x for x in s._dsl.all_named_objects if filt(x) }
    except AttributeError:
      return s._collect_all( [ filt ] )[0]

  def get_local_object_filter( s, filt ):
    assert callable( filt )
    return s._collect_objects_local( filt )

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

  def get_all_update_on_edge( s ):
    try:
      s._check_called_at_elaborate_top( "get_all_update_on_edge" )
      return s._dsl.all_update_on_edge
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

  def get_update_block_ast( s, blk ):
    try:
      name_ast = s.__class__._name_ast
    except AttributeError: # This component doesn't have update block
      return None

    return name_ast[blk.__name__]

  def get_update_block_host_component( s, blk ):
    try:
      s._check_called_at_elaborate_top( "get_update_block_host_component" )
      return s._dsl.all_upblk_hostobj[ blk ]
    except AttributeError:
      raise NotElaboratedError()

  def get_astnode_obj_mapping( s ):
    try:
      return s._dsl.astnode_objs
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

  def add_connection( s, o1, o2 ):
    try:
      top = s._dsl.elaborate_top
    except AttributeError:
      raise NotElaboratedError()

    try:
      s._connect_objects( o1, o2 )
    except AssertionError as e:
      raise InvalidConnectionError( "\n{}".format(e) )

    for x, adjs in s._dsl.adjacency.iteritems():
      top._dsl.all_adjacency[x].update( adjs )

  def add_connections( s, *args ):
    try:
      top = s._dsl.elaborate_top
    except AttributeError:
      raise NotElaboratedError()

    if len(args) & 1 != 0:
       raise InvalidConnectionError( "Odd number ({}) of objects provided.".format( len(args) ) )

    for i in xrange(len(args)>>1):
      try:
        s._connect_objects( args[ i<<1 ], args[ (i<<1)+1 ] )
      except InvalidConnectionError as e:
        raise InvalidConnectionError( "\n- In connect_pair, when connecting {}-th argument to {}-th argument\n{}\n " \
              .format( (i<<1)+1, (i<<1)+2 , e ) )

    for x, adjs in s._dsl.adjacency.iteritems():
      top._dsl.all_adjacency[x].update( adjs )

  # TODO implement everything below and test them

  # Override
  def add_component_by_name( s, name, obj, provided_connections=[] ):
    raise NotImplementedError()

  # Override
  def delete_component( s, name ):
    raise NotImplementedError()

  # Do we still need disconnect and disconnect_pair?
