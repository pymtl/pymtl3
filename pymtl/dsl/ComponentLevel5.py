#=========================================================================
# ComponentLevel5.py
#=========================================================================
# We allow CallerPort to be connected to CalleePort
#
# Author : Shunning Jiang
# Date   : Dec 29, 2018


from NamedObject import NamedObject
from ComponentLevel1 import ComponentLevel1
from ComponentLevel2 import ComponentLevel2
from ComponentLevel4 import ComponentLevel4
from Connectable import Signal, MethodPort, CalleePort, CallerPort

from errors import MultiWriterError

class ComponentLevel5( ComponentLevel4 ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  # Override
  def _declare_vars( s ):
    super( ComponentLevel5, s )._declare_vars()

    s._dsl.all_method_ports = set()

  def _connect_method_ports( s, o1, o2 ):
    assert isinstance( o1, MethodPort ) and isinstance( o2, MethodPort )
    print o1, o2

    s._dsl.adjacency[o1].add( o2 )
    s._dsl.adjacency[o2].add( o1 )
    s._dsl.connect_order.append( (o1, o2) )

  # Override
  def _connect_objects( s, o1, o2 ):
    if isinstance( o1, MethodPort ) and isinstance( o2, MethodPort ):
      s._connect_method_ports( o1, o2 )
    else:
      super( ComponentLevel5, s )._connect_objects( o1, o2 )

  #-----------------------------------------------------------------------
  # elaborate
  #-----------------------------------------------------------------------

  # Override
  def elaborate( s ):

    NamedObject.elaborate( s )

    s._declare_vars()

    for c in s._dsl.all_named_objects:

      if isinstance( c, Signal ):
        s._dsl.all_signals.add( c )

      if isinstance( c, ComponentLevel2 ):
        c._elaborate_read_write_func()

      if isinstance( c, ComponentLevel1 ):
        s._collect_vars( c )

      if isinstance( c, MethodPort ):
        s._dsl.all_method_ports.add( c )

    s._dsl.all_value_nets  = s._resolve_value_connections()
    s._dsl.all_method_nets = s._resolve_method_connections()
    s._dsl.has_pending_connections = False

    s.check()

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
