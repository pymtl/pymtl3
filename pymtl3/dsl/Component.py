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
from .ComponentLevel7 import ComponentLevel7
from .Connectable import InPort, OutPort, Wire, Signal, Interface


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

  def sim_reset( s ):
    assert s._dsl.elaborate_top is s # assert sim_reset is top

    s.reset = Bits1( 1 )
    s.tick() # This tick propagates the reset signal
    s.reset = Bits1( 0 )
    s.tick()

  def check( s ):
    s._check_valid_dsl_code()

  def get_component_level( s ):
    try:
      return s._dsl.level
    except AttributeError:
      raise NotElaboratedError()

  def get_child_components( s ):
    assert s._dsl.constructed
    ret = set()
    stack = []
    for (name, obj) in s.__dict__.iteritems():
      if   isinstance( name, basestring ): # python2 specific
        if not name.startswith("_"): # filter private variables
          stack.append( obj )
    while stack:
      u = stack.pop()
      if   isinstance( u, Component ):
        ret.add( u )
      # ONLY LIST IS SUPPORTED
      elif isinstance( u, list ):
        stack.extend( u )
    return ret

  def get_all_components( s ):
    try:
      return s._dsl.all_components
    except AttributeError:
      return s._collect_all( lambda x: isinstance( x, ComponentLevel1 ) )

  def apply( s, *args ):

    if isinstance(args[0], list):
      assert len(args) == 1
      for step in args[0]:
        step( s )

    elif len(args) == 1:
      assert callable( args[0] )
      args[0]( s )


  def get_update_block_host_component( s, blk ):
    try:
      assert s._dsl.elaborate_top is s, "Getting update block host component " \
                                    "is only allowed at top, but this API call " \
                                    "is on {}.".format( "top."+repr(s)[2:] )
      return s._dsl.all_upblk_hostobj[ blk ]
    except AttributeError:
      raise NotElaboratedError()

  def get_update_blocks( s ):
    return s._dsl.upblks

  def get_all_update_blocks( s ):
    try:
      assert s._dsl.elaborate_top is s, "Getting all update blocks " \
                                  "is only allowed at top, but this API call " \
                                  "is on {}.".format( "top."+repr(s)[2:] )
      return s._dsl.all_upblks
    except AttributeError:
      raise NotElaboratedError()

  def get_update_block_ast( s, blk ):
    try:
      name_ast = s.__class__._name_ast
    except AttributeError: # This component doesn't have update block
      return None

    return name_ast[blk.__name__]

  def get_astnode_obj_mapping( s ):
    try:
      return s._dsl.astnode_objs
    except AttributeError:
      raise NotElaboratedError()

  def get_all_update_on_edge( s ):
    try:
      assert s._dsl.elaborate_top is s, "Getting all update_on_edge blocks  " \
                                    "is only allowed at top, but this API call " \
                                    "is on {}.".format( "top."+repr(s)[2:] )
      return s._dsl.all_update_on_edge
    except AttributeError:
      raise NotElaboratedError()

  def get_update_on_edge( s ):
    assert s._dsl.constructed
    return s._dsl.update_on_edge

  def get_all_upblk_metadata( s ):
    try:
      assert s._dsl.elaborate_top is s, "Getting all update block metadata  " \
                                    "is only allowed at top, but this API call " \
                                    "is on {}.".format( "top."+repr(s)[2:] )
      return s._dsl.all_upblk_reads, s._dsl.all_upblk_writes, s._dsl.all_upblk_calls
    except AttributeError:
      raise NotElaboratedError()

  def get_upblk_metadata( s ):
    assert s._dsl.constructed
    return s._dsl.upblk_reads, s._dsl.upblk_writes, s._dsl.upblk_calls

  # Override
  def get_all_explicit_constraints( s ):
    try:
      assert s._dsl.elaborate_top is s, "Getting all explicit constraints " \
                                    "is only allowed at top, but this API call " \
                                    "is on {}.".format( "top."+repr(s)[2:] )
      return s._dsl.all_U_U_constraints, \
             s._dsl.RD_U_constraints, \
             s._dsl.WR_U_constraints
    except AttributeError:
      raise NotElaboratedError()

  def get_all_object_filter( s, filt ):
    assert callable( filt )
    try:
      return set( [ x for x in s._dsl.all_components | s._dsl.all_signals if filt(x) ] )
    except AttributeError:
      return s._collect_all( filt )

  def get_input_value_ports( s ):
    assert s._dsl.constructed
    ret = set()
    stack = [ obj for (name, obj) in s.__dict__.iteritems() \
                  if isinstance( name, basestring ) # python2 specific
                  if not name.startswith("_") ] # filter private variables
    while stack:
      u = stack.pop()
      if   isinstance( u, InPort ):
        ret.add( u )
      # ONLY LIST IS SUPPORTED
      elif isinstance( u, list ):
        stack.extend( u )

    return ret

  def get_output_value_ports( s ):
    assert s._dsl.constructed
    ret = set()
    stack = [ obj for (name, obj) in s.__dict__.iteritems() \
                  if isinstance( name, basestring ) # python2 specific
                  if not name.startswith("_") ] # filter private variables
    while stack:
      u = stack.pop()
      if   isinstance( u, OutPort ):
        ret.add( u )
      # ONLY LIST IS SUPPORTED
      elif isinstance( u, list ):
        stack.extend( u )
    return ret

  def get_wires( s ):
    assert s._dsl.constructed
    ret = set()
    stack = [ obj for (name, obj) in s.__dict__.iteritems() \
                  if isinstance( name, basestring ) # python2 specific
                  if not name.startswith("_") ] # filter private variables
    while stack:
      u = stack.pop()
      if   isinstance( u, Wire ):
        ret.add( u )
      # ONLY LIST IS SUPPORTED
      elif isinstance( u, list ):
        stack.extend( u )
    return ret
  def get_all_method_nets( s ):
    try:
      assert s._dsl.elaborate_top is s, "Getting all method nets " \
                                    "is only allowed at top, but this API call " \
                                    "is on {}.".format( "top."+repr(s)[2:] )
    except AttributeError:
      raise NotElaboratedError()

    if s._dsl.has_pending_connections:
      s._dsl.all_value_nets = s._resolve_value_connections()
      s._dsl.all_method_nets = s._resolve_method_connections()
      s._dsl.has_pending_connections = False

    return s._dsl.all_method_nets

  def get_all_value_nets( s ):
    try:
      assert s._dsl.elaborate_top is s, "Getting all nets " \
                                    "is only allowed at top, but this API call " \
                                    "is on {}.".format( "top."+repr(s)[2:] )
    except AttributeError:
      raise NotElaboratedError()

    if s._dsl.has_pending_connections:
      s._dsl.all_value_nets = s._resolve_value_connections()
      s._dsl.has_pending_connections = False

    return s._dsl.all_value_nets

  def get_connect_order( s ):
    try:
      return s._dsl.connect_order
    except AttributeError:
      raise NotElaboratedError()

  def get_signal_adjacency_dict( s ):
    try:
      assert s._dsl.elaborate_top is s, "Getting adjacency dictionary " \
                                    "is only allowed at top, but this API call " \
                                    "is on {}.".format( "top."+repr(s)[2:] )
    except AttributeError:
      raise NotElaboratedError()
    return s._dsl.all_adjacency

  # Override
  def delete_component_by_name( s, name ):

    # This nested delete function is to create an extra layer to properly
    # call garbage collector

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

  # Override
  # FIXME
  def add_component_by_name( s, name, obj ):
    assert not hasattr( s, name )
    NamedObject.__setattr__ = NamedObject.__setattr_for_elaborate__
    setattr( s, name, obj )
    del NamedObject.__setattr__

    top = s._dsl.elaborate_top

    added_components = obj.get_all_components()
    top._dsl.all_components |= added_components

    for c in added_components:
      c._dsl.elaborate_top = top
      c._elaborate_read_write_func()
      top._collect_vars( c )

    added_signals = obj._collect_all( lambda x: isinstance( x, Signal ) )
    top._dsl.all_signals |= added_signals

    # Lazy -- to avoid resolve_connection call which takes non-trivial
    # time upon adding any connect, I just mark it here. Please make sure
    # to call s.get_all_value_nets() to flush all pending connections
    # whenever you want to get the nets
    s._dsl.has_pending_connections = True

  def add_connection( s, o1, o2 ):
    # TODO support string arguments and non-top s
    assert s._dsl.elaborate_top is s, "Adding connection by passing objects " \
                                  "is only allowed at top, but this API call " \
                                  "is on {}.".format( "top."+repr(s)[2:] )

    added_adjacency = defaultdict(set)
    try:
      s._connect_objects( o1, o2, added_adjacency )
    except AssertionError as e:
      raise InvalidConnectionError( "\n{}".format(e) )

    for x, adjs in added_adjacency.iteritems():
      s._dsl.all_adjacency[x].update( adjs )

    s._dsl.has_pending_connections = True # Lazy

  def add_connections( s, *args ):
    # TODO support string arguments and non-top s
    assert s._dsl.elaborate_top is s, "Adding connection by passing objects " \
                                  "is only allowed at top, but this API call " \
                                  "is on {}.".format( "top."+repr(s)[2:] )

    if len(args) & 1 != 0:
       raise InvalidConnectionError( "Odd number ({}) of objects provided.".format( len(args) ) )

    last_adjacency = s._dsl.adjancency
    s._dsl.adjacency = defaultdict(set)

    for i in xrange(len(args)>>1) :
      try:
        s._connect_objects( args[ i<<1 ], args[ (i<<1)+1 ] )
      except InvalidConnectionError as e:
        raise InvalidConnectionError( "\n- In connect_pair, when connecting {}-th argument to {}-th argument\n{}\n " \
              .format( (i<<1)+1, (i<<1)+2 , e ) )

    for x, adjs in s._dsl.adjacency.iteritems():
      s._dsl.all_adjacency[x].update( adjs )

    s._dsl.has_pending_connections = True # Lazy

    s._dsl.adjancency = last_adjacency

  def disconnect( s, o1, o2 ):
    # TODO support string arguments and non-top s
    assert s._dsl.elaborate_top is s, "Disconnecting signals by passing objects " \
                                  "is only allowed at top, but this API call " \
                                  "is on {}.".format( "top."+repr(s)[2:] )


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
    assert s._elaborate_top is s, "Disconnecting signals by passing objects " \
                                  "is only allowed at top, but this API call " \
                                  "is on {}.".format( "top."+repr(s)[2:] )

    if len(args) & 1 != 0:
       raise InvalidConnectionError( "Odd number ({}) of objects provided.".format( len(args) ) )

    for i in xrange(len(args)>>1):
      s.disconnect( args[ i<<1 ], args[ (i<<1)+1 ] )


  def lock_in_simulation( s ):
    assert s._dsl.elaborate_top is s, "Locking in simulation " \
                                  "is only allowed at top, but this API call " \
                                  "is on {}.".format( "top."+repr(s)[2:] )
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
    assert s._dsl.elaborate_top is s, "Unlocking simulation " \
                                  "is only allowed at top, but this API call " \
                                  "is on {}.".format( "top."+repr(s)[2:] )
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
