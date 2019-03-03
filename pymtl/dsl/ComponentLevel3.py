#=========================================================================
# ComponentLevel3.py
#=========================================================================
# We add wire/interface connections. Basically, a connected component in
# the whole graph should have the same value in the cycle where the value
# is from a unique "net writer" written in an update block. Then, the
# update block for a net is basically one writer writes to those readers.
# Interface connections are handled separately, and they should be
# revamped when adding method-based interfaces.
#
# Author : Shunning Jiang
# Date   : Apr 16, 2018

from NamedObject import NamedObject
from ComponentLevel1 import ComponentLevel1
from ComponentLevel2 import ComponentLevel2
from Connectable import Connectable, Signal, InVPort, OutVPort, Wire, Const, Interface
from errors      import InvalidConnectionError, SignalTypeError, NoWriterError, MultiWriterError, NotElaboratedError
from collections import defaultdict, deque

import inspect, ast # for error message

class ComponentLevel3( ComponentLevel2 ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def __new__( cls, *args, **kwargs ):
    inst = super( ComponentLevel3, cls ).__new__( cls, *args, **kwargs )
    inst._dsl.call_kwargs = None
    inst._dsl.adjacency   = defaultdict(set)
    inst._dsl.consts      = set()
    return inst

  # Override
  def _declare_vars( s ):
    super( ComponentLevel3, s )._declare_vars()
    s._dsl.all_adjacency = defaultdict(set)

  # Override
  def _collect_vars( s, m ):
    super( ComponentLevel3, s )._collect_vars( m )
    if isinstance( m, ComponentLevel3 ):
      for k in m._dsl.adjacency:
        s._dsl.all_adjacency[k] |= m._dsl.adjacency[k]

  # Override
  def _construct( s ):
    """ We override _construct here to finish the saved __call__
    connections right after constructing the model. The reason why we
    take this detour instead of connecting in __call__ directly, is that
    __call__ is done before setattr, and hence the child components don't
    know their name yet. _dsl.constructed is called in setattr after name
    tagging, so this is valid. (see NamedObject.py). """

    if not s._dsl.constructed:
      kwargs = s._dsl.kwargs.copy()
      if "elaborate" in s._dsl.param_dict:
        kwargs.update( { x: y for x, y in s._dsl.param_dict[ "elaborate" ].iteritems()
                              if x } )

      s.construct( *s._dsl.args, **kwargs )

      if s._dsl.call_kwargs is not None: # s.a = A()( b = s.b )
        s._continue_call_connect()

      s._dsl.constructed = True

  def _connect_objects( s, o1, o2, adjacency_dict ):
    """ Connect two objects. If one of them is integer, create a new Const
    that wraps around it in 's'. This method refactors will be called by other
    public APIs. """

    if isinstance( o1, int ) or isinstance( o2, int ): # special case
      if isinstance( o1, int ):
        o1, o2 = o2, o1 # o1 is signal, o2 is int
      assert isinstance( o1, Signal )

      o2   = Const( o1._dsl.Type, o2, s )
      host = o1.get_host_component()

      if isinstance( o1, InVPort ):
        # connecting constant to inport should be at the parent level
        host = host.get_parent_object()

      o2._dsl.parent_obj = host
      host._dsl.consts.add( o2 )

    o1_type = None
    o2_type = None

    try:  o1_type = o1._dsl.Type
    except AttributeError:  pass
    try:  o2_type = o2._dsl.Type
    except AttributeError:  pass

    if o1_type is None:
      if o2_type is None:
        o1._connect( o2, adjacency_dict )
        return
      else: # o2_type is not None
        raise TypeError( "lhs has no Type, but rhs has Type {}".format( o2_type ) )
    else: # o1_type is not None
      if o2_type is None:
        raise TypeError( "lhs has Type {}, but rhs has no Type".format( o1_type ) )

    # Here o1/o2 both have Type

    try:
      o1_nbits = o1_type.nbits
      o2_nbits = o2_type.nbits
      assert o1_nbits == o2_nbits, "Bitwidth mismatch {} != {}".format( o1_nbits, o2_nbits )
    except AttributeError: # at least one of them is not Bits
      assert o1_type == o2_type, "Type mismatch {} != {}".format( o1_type, o2_type )

    o1._connect( o2, adjacency_dict )

  def _continue_call_connect( s ):
    """ Here we continue to establish the connections from signals of the
    parent object, to signals in the current object. Since it is the
    parent that connects a constant integer to a signal, we should point
    the Const object back to the parent object by setting _parent_obj to
    s._parent_obj."""

    try: # Catch AssertionError from _connect

      # Process saved __call__ kwargs
      for (kw, target) in s._dsl.call_kwargs.iteritems():
        try:
          obj = getattr( s, kw )
        except AttributeError:
          raise InvalidConnectionError( "{} is not a member of class {}".format(kw, s.__class__) )

        # Obj is a list of signals
        if   isinstance( obj, list ):
          # Make sure the connection target is a dictionary {idx: obj}
          if not isinstance( target, dict ):
            raise InvalidConnectionError( "We only support a dictionary when '{}' is an array.".format( kw ) )
          for idx, item in target.iteritems():
            s._connect_objects( obj[idx], item, s._dsl.adjacency )

        # Obj is a single signal
        # If the target is a list, it's fanout connection
        elif isinstance( target, tuple ) or isinstance( target, list ):
          for item in target:
            s._connect_objects( obj, item, s._dsl.adjacency )
        # Target is a single object
        else:
          s._connect_objects( obj, target, s._dsl.adjacency )

    except AssertionError as e:
      raise InvalidConnectionError( "Invalid connection for {}:\n{}".format( kw, e ) )

  @staticmethod
  def _floodfill_nets( signal_list, adjacency ):
    """ Floodfill to find out connected nets. Return a list of sets. """

    nets = []
    visited = set()
    pred    = {} # detect cycle that has >=3 nodes
    for obj in signal_list:
      # If obj has adjacent signals
      if adjacency[obj] and obj not in visited:
        net = set()
        Q   = deque( [ obj ] )
        while Q:
          u = Q.popleft()
          visited.add( u )
          net.add( u )
          for v in adjacency[u]:
            if v not in visited:
              pred[v] = u
              Q.append( v )
            elif v is not pred[u]:
              raise InvalidConnectionError(repr(v)+" is in a connection loop.")
        assert len(net) > 1, "what the hell?"
        nets.append( net )
    return nets

  def _resolve_var_connections( s, signal_list ):
    """ The case of nested data struct: the writer of a net can be one of
    the three: signal itself (s.x.a), ancestor (s.x), descendant (s.x.b)

    An iterative algorithm is required to mark the writers. The example
    is the following. Net 1's writer is s.x and one reader is s.y.
    Net 2's writer is s.y.a (known ONLY after Net 1's writer is clear),
    one reader is s.z. Net 3's writer is s.z.a (known ...), and so forth

    Note that s.x becomes writer when WR s.x.a or WR s.x.b, but s.x then
    cannot propagate back to s.x.b or s.x.a.

    The original state is all the writers from all update blocks.
    writer_prop is a dict {x:y} that stores potential writers and
    whether the writer can propagate to other nets. After a net is
    resolved from headless condition, its readers become writers.

    The case of slicing: slices of the same wire are only one level
    deeper, so all of those parent/child relationship work easily.
    However, unlike different fields of a data struct, different slices
    may _intersect_, so they need to check sibling slices' write/read
    status as well. """

    # First of all, bfs the "forest" to find out all nets

    nets = s._floodfill_nets( s._dsl.all_signals, s._dsl.all_adjacency )

    # Then figure out writers: all writes in upblks and their nest objects

    writer_prop = {}

    for blk, writes in s._dsl.all_upblk_writes.iteritems():
      for obj in writes:
        writer_prop[ obj ] = True # propagatable

        obj = obj.get_parent_object()
        while obj.is_signal():
          writer_prop[ obj ] = False
          obj = obj.get_parent_object()

    # Find the host object of every net signal
    # and then leverage the information to find out top level input port

    for net in nets:
      for member in net:
        host = member
        while not isinstance( host, ComponentLevel3 ):
          host = host.get_parent_object() # go to the component
        member._dsl.host = host

        if isinstance( member, InVPort ) and member._dsl.host == s:
          writer_prop[ member ] = True

    headless = nets
    headed   = []

    # Convention: we store a net in a tuple ( writer, set([readers]) )
    # The first element is writer; it should be None if there is no
    # writer. The second element is a set of signals including the writer.

    while headless:
      new_headless = []
      wcount = len(writer_prop)

      # For each net, figure out the writer among all vars and their
      # ancestors. Moreover, if x's ancestor has a writer in another net,
      # x should be the writer of this net.
      #
      # If there is a writer, propagate writer information to all readers
      # and readers' ancestors. The propagation is tricky: assume s.x.a
      # is in net, and s.x.b is written in upblk, s.x.b will mark s.x as
      # an unpropagatable writer because later s.x.a shouldn't be marked
      # as writer by s.x.
      #
      # Similarly, if x[0:10] is written in update block, x[5:15] can
      # be a unpropagatable writer because we don't want x[5:15] to
      # propagate to x[12:17] later.

      for net in headless:
        has_writer = False

        for v in net:
          obj = None
          try:
            # Check if itself is a writer or a constant
            if v in writer_prop or isinstance( v, Const ):
              assert not has_writer
              has_writer, writer = True, v

            # Check if an ancestor is a propagatable writer
            obj = v.get_parent_object()
            while obj.is_signal():
              if obj in writer_prop and writer_prop[ obj ]:
                assert not has_writer
                has_writer, writer = True, v
                break
              obj = obj.get_parent_object()

            # Check sibling slices
            for obj in v.get_sibling_slices():
              if obj.slice_overlap( v ):
                if obj in writer_prop and writer_prop[ obj ]:
                  assert not has_writer
                  has_writer, writer = True, v

          except AssertionError:
            raise MultiWriterError( \
            "Two-writer conflict \"{}\"{}, \"{}\" in the following net:\n - {}".format(
              repr(v), "" if not obj else "(as \"{}\" is written somewhere else)".format( repr(obj) ),
              repr(writer), "\n - ".join([repr(x) for x in net])) )

        if not has_writer:
          new_headless.append( net )
          continue

        # Child s.x.y of some propagatable s.x, or sibling of some
        # propagatable s[a:b].
        # This means that at least other variables are able to see s.x/s[a:b]
        # so it doesn't matter if s.x.y is not in writer_prop
        if writer not in writer_prop:
          pass

        for v in net:
          if v != writer:
            writer_prop[ v ] = True # The reader becomes new writer

            obj = v.get_parent_object()
            while obj.is_signal():
              if obj not in writer_prop:
                writer_prop[ obj ] = False
              obj = obj.get_parent_object()

        headed.append( (writer, net) )

      if wcount == len(writer_prop): # no more new writers
        break
      headless = new_headless

    return headed + [ (None, x) for x in headless ]

  def _check_port_in_nets( s ):
    nets = s.get_all_nets()

    # The case of connection is very tricky because we put a single upblk
    # in the lowest common ancestor node and the "output port" chain is
    # inverted. So we need to deal with it here ...
    #
    # The gist is that the data flows from deeper level writer to upper
    # level readers via output port, to the same level via wire, and from
    # upper level to deeper level via input port

    headless = [ signals for writer, signals in nets if writer is None ] # remove None
    if headless:
      raise NoWriterError( headless )

    for writer, _ in nets:

      # We need to do DFS to check all connected port types
      # Each node is a writer when we expand it to other nodes

      S = deque( [ writer ] )
      visited = set( [ writer ] )

      while S:
        u = S.pop() # u is the writer
        whost = u._dsl.host

        for v in s._dsl.all_adjacency[u]: # v is the reader
          if v not in visited:
            visited.add( v )
            S.append( v )
            rhost = v._dsl.host

            # 1. have the same host: writer_host(x)/reader_host(x):
            # Hence, writer is anything, reader is wire or outport
            if   whost == rhost:
              valid = ( isinstance( u, Signal )  or isinstance( u, Const) ) and \
                      ( isinstance( v, OutVPort) or isinstance( v, Wire ) )
              if not valid:
                raise SignalTypeError( \
"""[Type 5] Invalid port type detected at the same host component "{}" (class {})

- {} "{}" cannot be driven by {} "{}".

  Note: InVPort x.y cannot be driven by x.z""" \
          .format(  repr(rhost), type(rhost).__name__,
                    type(v).__name__, repr(v), type(u).__name__, repr(u) ) )

            # 2. reader_host(x) is writer_host(x.y)'s parent:
            # Hence, writer is outport, reader is wire or outport
            # writer cannot be constant
            elif rhost == whost.get_parent_object():
              valid = isinstance( u, OutVPort) and \
                    ( isinstance( v, OutVPort ) or isinstance( v, Wire ) )

              if not valid:
                raise SignalTypeError( \
"""[Type 6] Invalid port type detected when the driver lies deeper than drivee:

- {} "{}" of {} (class {}) cannot be driven by {} "{}" of {} (class {}).

  Note: InVPort x.y cannot be driven by x.z.a""" \
          .format(  type(v).__name__, repr(v), repr(rhost), type(rhost).__name__,
                    type(u).__name__, repr(u), repr(whost), type(whost).__name__ ) )

            # 3. writer_host(x) is reader_host(x.y)'s parent:
            # Hence, writer is inport or wire, reader is inport
            # writer can be constant
            elif whost == rhost.get_parent_object():
              # valid = ( isinstance( u, InVPort ) or isinstance( u, Wire ) \
                                                 # or isinstance( u, Const)) and \
                         # isinstance( v, InVPort )

              # if not valid:
                # raise SignalTypeError( \
# """[Type 7] Invalid port type detected when the driver lies shallower than drivee:

# - {} "{}" of {} (class {}) cannot be driven by {} "{}" of {} (class {}).

  # Note: OutVPort/Wire x.y.z cannot be driven by x.a""" \
          # .format(  type(v).__name__, repr(v), repr(rhost), type(rhost).__name__,
                    # type(u).__name__, repr(u), repr(whost), type(whost).__name__ ) )

            # Shunning 9/12/2017: Actually in this case writer can be outport
              valid = ( isinstance( u, Signal ) or isinstance( u, Const )) and \
                        isinstance( v, InVPort )

              if not valid:
                raise SignalTypeError( \
"""[Type 7] Invalid port type detected when the driver lies shallower than drivee:

- {} "{}" of {} (class {}) cannot be driven by {} "{}" of {} (class {}).

  Note: OutVPort/Wire x.y.z cannot be driven by x.a""" \
          .format(  type(v).__name__, repr(v), repr(rhost), type(rhost).__name__,
                    type(u).__name__, repr(u), repr(whost), type(whost).__name__ ) )

            # 4. hosts have the same parent: writer_host(x.y)/reader_host(x.z)
            # This means that the connection is fulfilled in x
            # Hence, writer is outport and reader is inport
            # writer cannot be constant
            elif whost.get_parent_object() == rhost.get_parent_object():
              valid = isinstance( u, OutVPort ) and isinstance( v, InVPort )

              if not valid:
                raise SignalTypeError( \
"""[Type 8] Invalid port type detected when the drivers is the sibling of drivee:

- {} "{}" of {} (class {}) cannot be driven by {} "{}" of {} (class {}).

  Note: Looks like the connection is fulfilled in "{}".
        OutVPort/Wire x.y.z cannot be driven by x.a.b""" \
          .format(  type(v).__name__, repr(v), repr(rhost), type(rhost).__name__,
                    type(u).__name__, repr(u), repr(whost), type(whost).__name__,
                    repr(whost.get_parent_object()) ) )
            # 5. neither host is the other's parent nor the same.
            else:
              raise SignalTypeError("""[Type 9] "{}" and "{}" cannot be connected:

- host objects "{}" and "{}" are too far in the hierarchy.""" \
              .format( repr(u), repr(v), repr(whost), repr(rhost) ) )

  def _disconnect_signal_int( s, o1, o2 ):

    nets = s.get_all_nets()

    for i, net in enumerate( nets ):
      writer, signals = net

      if o1 in signals: # Find the net that contains o1
        # If we're disconnecting a constant from a port, the constant
        # should be the only writer in this net and is equal to o2
        assert isinstance( writer, Const ), "what the hell?"
        assert writer._dsl.const == o2, "Disconnecting the wrong const {} " \
                                        "-- should be {}.".format( o2, writer.const )
        o2 = writer

        # I don't remove it from m._adjacency since they are not used later
        assert o1 in s._dsl.all_adjacency[o2] and o2 in s._dsl.all_adjacency[o1]
        s._dsl.all_adjacency[o2].remove( o1 )
        s._dsl.all_adjacency[o1].remove( o2 )

        # Disconnect a const from a signal just removes the writer in the net
        signals.remove( writer )
        nets[i] = ( None, signals )
        return

  def _disconnect_signal_signal( s, o1, o2 ):

    nets = s.get_all_nets()

    assert o1 in s._dsl.all_adjacency[o2] and o2 in s._dsl.all_adjacency[o1]
    # I don't remove it from m._adjacency since they are not used later
    s._dsl.all_adjacency[o2].remove( o1 )
    s._dsl.all_adjacency[o1].remove( o2 )

    for i, net in enumerate( nets ):
      writer, signals = net

      if o1 in signals: # Find the net that contains o1
        assert o2 in signals, signals

        broken_nets = s._floodfill_nets( signals, s._dsl.all_adjacency )

        # disconnect the only two vertices in the net
        if len(broken_nets) == 0:
          nets[i] = nets.pop() # squeeze in the last net

        # the removed edge results in an isolated vertex and a connected component
        elif len(broken_nets) == 1:
          net0 = broken_nets[0]
          if writer in net0:
            nets[i] = ( writer, net0 )
          else:
            assert writer is o1 or writer is o2
            nets[i] = ( None, net0 )

        elif len(broken_nets) == 2:
          net0, net1 = broken_nets[0], broken_nets[1]
          if writer in net0:
            nets[i] = ( writer, net0 ) # replace in-place
            nets.append( (None, net1) )
          else:
            assert writer in net1
            nets[i] = ( None, net0 ) # replace in-place
            nets.append( (writer, net1) )

        else:
          assert False, "what the hell?"

        return

  def _disconnect_interface_interface( s, o1, o2 ):

    # Here we call connect to get the mock adjacency dictionary because
    # o1 and o2 might be signal bundles and we need signal connections
    mock_adjacency = defaultdict(set)
    s._connect_objects( o1, o2, mock_adjacency )

    visited = set()
    for u, vs in mock_adjacency.iteritems():
      for v in vs:
        if (u, v) not in visited:
          s._disconnect_signal_signal( u, v )
          visited.add( (u, v) )
          visited.add( (v, u) )

  #-----------------------------------------------------------------------
  # Construction-time APIs
  #-----------------------------------------------------------------------

  def __call__( s, *args, **kwargs ):
    """ This syntactic sugar supports the following one-liner:
      >>> s.x = SomeReg(Bits1)( in_ = s.in_ )
    It connects s.in_ to s.x.in_ in the same line as model construction.
    """
    assert args == ()
    if s._dsl.constructed:
      raise InvalidConnectionError("Connection using __call__, "
                                   "i.e. s.x( a = s.a ), is illegal "
                                   "after constructing s.x")
    s._dsl.call_kwargs = kwargs
    return s

  def connect( s, o1, o2 ):
    try:
      s._connect_objects( o1, o2, s._dsl.adjacency )
    except AssertionError as e:
      raise InvalidConnectionError( "\n{}".format(e) )

  def connect_pairs( s, *args ):
    if len(args) & 1 != 0:
       raise InvalidConnectionError( "Odd number ({}) of objects provided.".format( len(args) ) )

    for i in xrange(len(args)>>1) :
      try:
        s.connect( args[ i<<1 ], args[ (i<<1)+1 ] )
      except InvalidConnectionError as e:
        raise InvalidConnectionError( "\n- In connect_pair, when connecting {}-th argument to {}-th argument\n{}\n " \
              .format( (i<<1)+1, (i<<1)+2 , e ) )

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

    s._dsl.all_signals = s._collect_all( lambda x: isinstance( x, Signal ) )
    s._dsl.all_nets    = s._resolve_var_connections( s._dsl.all_signals )
    s._dsl.has_pending_connections = False

    s.check()

  #-----------------------------------------------------------------------
  # Public APIs (only can be called after elaboration)
  #-----------------------------------------------------------------------

  # Override
  def check( s ):
    s._check_upblk_writes()
    s._check_port_in_upblk()
    s._check_port_in_nets()

  def get_all_nets( s ):
    try:
      assert s._dsl.elaborate_top is s, "Getting all nets " \
                                    "is only allowed at top, but this API call " \
                                    "is on {}.".format( "top."+repr(s)[2:] )
    except AttributeError:
      raise NotElaboratedError()

    if s._dsl.has_pending_connections:
      s._dsl.all_nets = s._resolve_var_connections( s._dsl.all_signals )
      s._dsl.has_pending_connections = False

    return s._dsl.all_nets

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
      nets = top.get_all_nets()

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

      top._all_nets = new_nets

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
    # to call s.get_all_nets() to flush all pending connections whenever
    # you want to get the nets
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

    added_adjacency = defaultdict(set)

    for i in xrange(len(args)>>1) :
      try:
        s._connect_objects( args[ i<<1 ], args[ (i<<1)+1 ], added_adjacency )
      except InvalidConnectionError as e:
        raise InvalidConnectionError( "\n- In connect_pair, when connecting {}-th argument to {}-th argument\n{}\n " \
              .format( (i<<1)+1, (i<<1)+2 , e ) )

    for x, adjs in added_adjacency.iteritems():
      s._dsl.all_adjacency[x].update( adjs )

    s._dsl.has_pending_connections = True # Lazy

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
