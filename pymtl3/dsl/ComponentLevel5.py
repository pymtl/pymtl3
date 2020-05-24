"""
========================================================================
ComponentLevel5.py
========================================================================
We allow CallerPort to be connected to CalleePort

Author : Shunning Jiang
Date   : Dec 29, 2018
"""
from .ComponentLevel1 import ComponentLevel1
from .ComponentLevel2 import ComponentLevel2
from .ComponentLevel4 import ComponentLevel4
from .Connectable import CalleePort, CallerPort, Const, Interface, MethodPort, Signal
from .errors import InvalidConnectionError, MultiWriterError
from .NamedObject import NamedObject
from .Placeholder import Placeholder


# This method_port is a syntactic sugar to create a CalleePort
# Note that for a simple method port we currently don't care about type
def method_port( method ):
  method._callee_port = True
  return method

class ComponentLevel5( ComponentLevel4 ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def _handle_decorated_methods( s ):

    for x in s.__class__.__dict__:
      method = getattr( s, x )
      # We identify decorated method port here
      if hasattr( method, "_callee_port" ):
        setattr( s, x, CalleePort( method = method ) )

  # Override
  def _construct( s ):
    """ We override _construct here to add method binding. Basically
    we do this after the class is constructed but before the construct()
    elaboration happens."""

    if not s._dsl.constructed:

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

      s._dsl.constructed = True

  def _connect_method_ports( s, o1, o2 ):
    s._dsl.adjacency[o1].add( o2 )
    s._dsl.adjacency[o2].add( o1 )
    s._dsl.connect_order.append( (o1, o2) )

  # Override
  def _connect_dispatch( s, o1, o2, o1_connectable, o2_connectable ):

    if o1_connectable and o2_connectable:
      # if both connectable, dispatch signal-signal and interface-interface
      if isinstance( o1, Signal ) and isinstance(o2, Signal ):
        s._connect_signal_signal( o1, o2 )
      elif isinstance( o1, Interface ) and isinstance( o2, Interface ):
        s._connect_interfaces( o1, o2 )
      # Methodport added here
      elif isinstance( o1, MethodPort ) and isinstance( o2, MethodPort ):
        s._connect_method_ports( o1, o2 )
      else:
        raise InvalidConnectionError("{} cannot be connected to {}: {} != {}" \
              .format(repr(o1), repr(o2), type(o1), type(o2)) )
    else:
      # One is connectable, we make sure it's o1
      if o2_connectable:
        o1, o2 = o2, o1
      assert isinstance( o1, Signal ), f"Cannot connect {o2} to {o1!r} of {type(o1)}."

      s._connect_signal_const( o1, o2 )

  def _resolve_method_connections( s ):

    # First of all, bfs the "forest" to find out all nets

    nets = s._floodfill_nets( s._dsl.all_method_ports, s._dsl.all_adjacency )

    # All CalleePort are "writers" because they have actual methods

    ret = []

    for net in nets:
      writer = None

      for member in net:

        if isinstance( member, CalleePort ):
          if member.method is not None or \
             isinstance( member.get_host_component(), Placeholder ):
            if writer is None:
              writer = member
            else:
              raise MultiWriterError( \
                "Two-method conflict \"{}\", \"{}\" in the following net:\n - {}".format(
                repr(member), repr(writer),
                "\n - ".join([repr(x) for x in net])) )

        else:
          assert isinstance( member, CallerPort ), "We don't allow connecting method " \
                                                   "port to other ports of {} type".format( member.__class__ )
      assert writer is not None, "This method net has no actual method to call.\n- {}" \
                                  .format( '\n- '.join([ repr(x) for x in net]) )
      ret.append( (writer, net) )

    return ret

  # TODO Check if all method net port directions are correct

  #-----------------------------------------------------------------------
  # elaborate
  #-----------------------------------------------------------------------
  # We still reuse the elaborate template by adding functionalities to
  # sub-functions called by elaborate

  # Override
  def _elaborate_declare_vars( s ):
    super()._elaborate_declare_vars()

    s._dsl.all_method_ports = set()

  # However, we need to override the whole function here because we want
  # to add some fine-grained functionalities to avoid reduntant isinstance
  # Override
  def _elaborate_collect_all_vars( s ):
    for c in s._dsl.all_named_objects:
      if isinstance( c, Signal ):
        s._dsl.all_signals.add( c )
      elif isinstance( c, ComponentLevel1 ):
        s._dsl.all_components.add( c )
        s._collect_vars( c )
      # Added here
      elif isinstance( c, MethodPort ):
        s._dsl.all_method_ports.add( c )

    s._dsl.all_value_nets  = s._resolve_value_connections()
    # Added here
    s._dsl.all_method_nets = s._resolve_method_connections()
    s._dsl._has_pending_value_connections = False
    s._dsl._has_pending_method_connections = False
