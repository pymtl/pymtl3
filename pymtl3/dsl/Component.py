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

from .NamedObject import NamedObject
from .ComponentLevel1 import ComponentLevel1
from .ComponentLevel7 import ComponentLevel7
from .Connectable import InPort, OutPort, Wire, Signal, Interface, MethodPort
from .errors import NotElaboratedError, InvalidAPICallError
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

      # We hook up the added clk and reset signals here.
      try:
        parent = s.get_parent_object()
        parent.connect( s.clk, parent.clk )
        parent.connect( s.reset, parent.reset )
      except AttributeError:
        pass

      # Same as parent class _construct
      s.construct( *s._dsl.args, **kwargs )

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

  def _flush_pending_connections( s ):
    if s._dsl._has_pending_connections:
      s._dsl.all_value_nets = s._resolve_value_connections()
      s._dsl.all_method_nets = s._resolve_method_connections()
      s._dsl._has_pending_connections = False

  # Override
  def _add_component( s, parent, name, indices, obj, provided_connections=[] ):
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
      # FIXME properly implement param_tree
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

    top = s._dsl.elaborate_top

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

    # assert False
    # Lazy -- to avoid resolve_connection call which takes non-trivial
    # time upon adding any connect, I just mark it here. Please make sure
    # to call s.get_all_value_nets() to flush all pending connections
    # whenever you want to get the nets
    connection_pairs = []
    for (x, y) in provided_connections:
      # top.add_connections( x, eval(y) )
      connection_pairs.append( x )
      connection_pairs.append( eval(y) )

    top.add_connections( *connection_pairs )

    s._dsl._has_pending_connections = True

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
    s.tick() # This tick propagates the reset signal
    s.reset = Bits1( 0 )
    s.tick()

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
      return set( [ x for x in s._dsl.all_named_objects if filt(x) ] )
    except AttributeError:
      return s._collect_all( [ filt ] )[0]

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
    s._flush_pending_connections()
    return s._dsl.all_method_nets

  # Override
  def get_all_value_nets( s ):
    s._check_called_at_elaborate_top( "get_all_value_nets" )
    s._flush_pending_connections()
    return s._dsl.all_value_nets

  def get_signal_adjacency_dict( s ):
    try:
      s._check_called_at_elaborate_top( "get_signal_adjacency_dict" )
    except AttributeError:
      raise NotElaboratedError()
    return s._dsl.all_adjacency

  """ Mutation APIs to add/delete components and connections"""

  # Shunning: These API implement replacing a placeholder with a real
  # module. This is the first mutation API we want to test thoroughly

  def delete_placeholder( top, foo, cls ):
    assert isinstance( foo, Placeholder ), foo.__class__
    assert foo._dsl.elaborate_top is top

    # First make sure we flush pending connections
    nets = top.get_all_value_nets()

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
      delattr( parent, foo._dsl.my_name )

    # Note that when we are deleting a placeholder foo, there is no other
    # components inside foo, nor constraints or update blocks. As a result
    # we don't need to uncollect vars. We just need to break the nets and
    # save the connections.

    removed_components, removed_signals, removed_method_ports = \
      foo._collect_all( [ lambda x: isinstance( x, Component ), \
                          lambda x: isinstance( x, Signal ), \
                          lambda x: isinstance( x, MethodPort ) ] )
    # print(removed_components, removed_signals, removed_method_ports)

    top._dsl.all_components    -= removed_components
    top._dsl.all_signals       -= removed_signals
    top._dsl.all_method_ports  -= removed_method_ports

    top._dsl.all_named_objects -= removed_components
    top._dsl.all_named_objects -= removed_signals
    top._dsl.all_named_objects -= removed_method_ports

    # No need to uncollect vars from a placeholder
    assert not foo._dsl.consts

    for x in removed_components | removed_signals | removed_method_ports:
      del x._dsl.parent_obj

    saved_connections = []

    for x in removed_signals:
      # Clean up all_adjancency at top
      if x in top._dsl.all_adjacency:
        for other in top._dsl.all_adjacency[x]:
          # other must be in the dict
          # If other will be removed, we don't need to remove it here ..
          if other not in removed_signals:
            top._dsl.all_adjacency[other].remove( x )
            saved_connections.append( (other, "top"+repr(x)[1:]) ) # other is from outside
        del top._dsl.all_adjacency[x]

      # Clean up adjacency at parent
      if x in parent._dsl.adjacency:
        for other in parent._dsl.adjacency[x]:
          # other must be in the dict
          if other not in removed_signals:
            parent._dsl.adjacency[other].remove( x )
        del parent._dsl.adjacency[x]

    # The following implementation of breaking nets is faster than a
    # full connection resolution.

    new_nets = []
    for writer, signals in nets:
      broken_nets = top._floodfill_nets( signals, top._dsl.all_adjacency )

      for net_signals in broken_nets:
        if len(net_signals) > 1:
          if writer in net_signals:
            new_nets.append( (writer, net_signals) )
          else:
            new_nets.append( (None, net_signals) )

    top._dsl.all_value_nets = new_nets

    # TODO break method nets too

    # FIXME the last task is to fix connect_order

    return saved_connections

  # Override
  # FIXME currently only support s.x = y. Should support s.x[10] = y
  def add_component_by_name( s, name, obj, provided_connections=[] ):
    raise NotImplementedError()

  def replace_placeholder( top, foo, cls, check=True ):
    top._check_called_at_elaborate_top( "replace_placeholder" )

    parent = foo.get_parent_object()
    foo_name    = foo._dsl._my_name
    foo_indices = foo._dsl._my_indices

    saved_connections = top.delete_placeholder( foo, cls )

    new_obj = cls( *foo._dsl.args, **foo._dsl.kwargs )

    # FIXME also merge the parameter from parameter tree

    top._add_component( parent, foo_name, foo_indices, new_obj, saved_connections )

    top._flush_pending_connections()
    if check:
      top.check()

  # TODO test everything below and figure out whether we need to delete
  # a normal component

  # Override
  def delete_component_by_name( s, name ):
    s._check_called_at_elaborate_top( "delete_component_by_name" )

    # This nested delete function is to create an extra layer to properly
    # call garbage collector. If we can make sure it is collected
    # automatically and fast enough, we might remove this extra layer
    #
    # EDIT: After experimented w/ and w/o gc.collect(), it seems like it
    # is eventually collected, but sometimes the intermediate memory
    # footprint might reach up to gigabytes, so let's keep the
    # gc.collect() for now

    def _delete_component_by_name( parent, name ):
      obj = getattr( parent, name )
      top = s._dsl.elaborate_top
      import timeit

      # First make sure we flush pending connections
      nets = top.get_all_value_nets()

      # Remove all components and uncollect metadata

      removed_components = obj.get_all_components()
      top._dsl.all_components -= removed_components

      removed_signals = obj._collect_all( lambda x: isinstance( x, Signal ) )
      top._dsl.all_signals -= removed_signals

      for x in removed_components:
        assert x._dsl.elaborate_top is top
        top._uncollect_vars( x )
        for y in x._dsl.consts:
          del y._dsl.parent_obj

      for x in obj._collect_all():
        del x._dsl.parent_obj

      # TODO somehow save the adjs for reconnection

      for x in removed_signals:
        for other in top._dsl.all_adjacency[x]:
          # If other will be removed, we don't need to remove it here ..
          if   other not in removed_signals:
            top._dsl.all_adjacency[other].remove( x )

        del top._dsl.all_adjacency[x]

      # The following implementation of breaking nets is faster than a
      # full connection resolution.

      new_nets = []
      for writer, signals in nets:
        broken_nets = s._floodfill_nets( signals, top._dsl.all_adjacency )

        for net_signals in broken_nets:
          if len(net_signals) > 1:
            if writer in net_signals:
              new_nets.append( (writer, net_signals) )
            else:
              new_nets.append( (None, net_signals) )
      t1 = timeit.default_timer()

      top._dsl.all_value_nets = new_nets

      delattr( s, name )

    _delete_component_by_name( s, name )
    # import gc
    # gc.collect() # this takes 0.1 seconds

  def add_connection( s, o1, o2 ):
    try:
      top = s._dsl.elaborate_top
    except AttributeError:
      raise NotElaboratedError()

    try:
      parent._connect_objects( o1, o2 )
    except AssertionError as e:
      raise InvalidConnectionError( "\n{}".format(e) )

    for x, adjs in parent._dsl.adjacency.iteritems():
      top._dsl.all_adjacency[x].update( adjs )

    top._dsl._has_pending_connections = True # Lazy

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

    top._dsl._has_pending_connections = True # Lazy

  def disconnect( s, o1, o2 ):
    # TODO support string arguments and non-top s
    s._check_called_at_elaborate_top( "disconnect" )


    if isinstance( o1, int ): # o1 is signal, o2 is int
      o1, o2 = o2, o1

    # First handle the case where a const is disconnected from the signal
    if isinstance( o2, int ):
      assert isinstance( o1, Signal ), "You can only disconnect a const from a signal."
      s._disconnect_signal_int( o1, o2 )

    # Disconnect two signals
    elif isinstance( o1, Signal ):
      assert isinstance( o2, Signal )
      s._disconnect_signal_signal( o1, o2 )

    elif isinstance( o1, Interface ):
      assert isinstance( o2, Interface )
      s._disconnect_interface_interface( o1, o2 )

    else:
      assert False, "what the hell?"

  def disconnect_pair( s, *args ):
    # TODO support string arguments and non-top s
    s._check_called_at_elaborate_top( "disconnect_pair" )

    if len(args) & 1 != 0:
       raise InvalidConnectionError( "Odd number ({}) of objects provided.".format( len(args) ) )

    for i in xrange(len(args)>>1):
      s.disconnect( args[ i<<1 ], args[ (i<<1)+1 ] )
