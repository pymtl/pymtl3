"""
========================================================================
ComponentLevel5.py
========================================================================
We allow CallerPort to be connected to CalleePort

Author : Shunning Jiang
Date   : Dec 29, 2018
"""
from __future__ import absolute_import, division, print_function

from .ComponentLevel1 import ComponentLevel1
from .ComponentLevel2 import ComponentLevel2
from .ComponentLevel4 import ComponentLevel4
from .Connectable import CalleePort, CallerPort, MethodPort, Signal
from .errors import MultiWriterError
from .NamedObject import NamedObject


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

    cls_dict = s.__class__.__dict__
    for x in cls_dict:
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

      kwargs = s._dsl.kwargs.copy()
      if "elaborate" in s._dsl.param_dict:
        kwargs.update( { x: y for x, y in s._dsl.param_dict[ "elaborate" ].iteritems()
                              if x } )

      s._handle_decorated_methods()

      # Same as parent class _construct
      s.construct( *s._dsl.args, **kwargs )

      if s._dsl.call_kwargs is not None: # s.a = A()( b = s.b )
        s._continue_call_connect()

      s._dsl.constructed = True

  def _connect_method_ports( s, o1, o2 ):
    assert isinstance( o1, MethodPort ) and isinstance( o2, MethodPort )

    s._dsl.adjacency[o1].add( o2 )
    s._dsl.adjacency[o2].add( o1 )
    s._dsl.connect_order.append( (o1, o2) )

  # Override
  def _connect_objects( s, o1, o2, internal=False ):
    if isinstance( o1, MethodPort ) and isinstance( o2, MethodPort ):
      s._connect_method_ports( o1, o2 )
    else:
      super( ComponentLevel5, s )._connect_objects( o1, o2, internal )

  #-----------------------------------------------------------------------
  # elaborate
  #-----------------------------------------------------------------------

  # We still reuse the elaborate template by adding functionalities to
  # sub-functions called by elaborate
  # Override
  def _elaborate_declare_vars( s ):
    super( ComponentLevel5, s )._elaborate_declare_vars()

    s._dsl.all_method_ports = set()

  # However, we need to override the whole function here because we want
  # to add some fine-grained functionalities to avoid reduntant isinstance
  # Override
  def _elaborate_collect_all_vars( s ):
    for c in s._dsl.all_named_objects:

      if isinstance( c, Signal ):
        s._dsl.all_signals.add( c )
      elif isinstance( c, ComponentLevel1 ):
        s._collect_vars( c )
      # Added here
      elif isinstance( c, MethodPort ):
        s._dsl.all_method_ports.add( c )

    s._dsl.all_value_nets  = s._resolve_value_connections()
    # Added here
    s._dsl.all_method_nets = s._resolve_method_connections()
    s._dsl.has_pending_connections = False

  def _resolve_method_connections( s ):

    # First of all, bfs the "forest" to find out all nets

    nets = s._floodfill_nets( s._dsl.all_method_ports, s._dsl.all_adjacency )

    # All CalleePort are "writers" because they have actual methods

    ret = []

    for net in nets:
      writer = None

      for member in net:

        if isinstance( member, CalleePort ):
          if member.method is not None:
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
      ret.append( (writer, net) )

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
