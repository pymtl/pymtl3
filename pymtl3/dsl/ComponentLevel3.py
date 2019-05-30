"""
========================================================================
ComponentLevel3.py
========================================================================
We add value wire/interface connections. Basically, all connected
value signal in the whole graph should have the same value of the unique
"net writer" written in an update block.
Then, the update block for a net is basically one writer writes to those
readers. Interface connections are handled separately, and they should
be revamped when adding method-based interfaces.

Author : Shunning Jiang
Date   : Apr 16, 2018
"""
from __future__ import absolute_import, division, print_function

from collections import defaultdict, deque

from pymtl3.datatypes import Bits

from .ComponentLevel1 import ComponentLevel1
from .ComponentLevel2 import ComponentLevel2
from .Connectable import Connectable, Const, InPort, Interface, OutPort, Signal, Wire
from .errors import (
    InvalidConnectionError,
    InvalidPlaceholderError,
    MultiWriterError,
    NotElaboratedError,
    NoWriterError,
    SignalTypeError,
)
from .NamedObject import NamedObject
from .Placeholder import Placeholder


class ComponentLevel3( ComponentLevel2 ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def __new__( cls, *args, **kwargs ):
    inst = super( ComponentLevel3, cls ).__new__( cls, *args, **kwargs )
    inst._dsl.call_kwargs   = None
    inst._dsl.adjacency     = defaultdict(set)
    inst._dsl.connect_order = []
    inst._dsl.consts        = set()
    return inst

  # Override
  def _collect_vars( s, m ):
    super( ComponentLevel3, s )._collect_vars( m )
    if isinstance( m, ComponentLevel3 ):
      all_ajd = s._dsl.all_adjacency
      for k, v in m._dsl.adjacency.items():
        all_ajd[k] |= v

  # Override
  def _construct( s ):
    """ We override _construct here to finish the saved __call__
    connections right after constructing the model. The reason why we
    take this detour instead of connecting in __call__ directly, is that
    __call__ is done before setattr, and hence the child components don't
    know their name yet. _dsl.constructed is called in setattr after name
    tagging, so this is valid. (see NamedObject.py). """

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

      s.construct( *s._dsl.args, **kwargs )

      if s._dsl.call_kwargs is not None: # s.a = A()( b = s.b )
        s._continue_call_connect()

      s._dsl.constructed = True

  # The following three methods should only be called when types are
  # already checked

  def _connect_signal_const( s, o1, o2 ):
    if isinstance( o2, int ):
      if not issubclass( o1._dsl.Type, (int, Bits) ):
        raise InvalidConnectionError( "We don't support connecting an integer constant "
                                       "to non-int/Bits type {}".format( o1._dsl.Type ) )
      o2 = Const( o1._dsl.Type, o2, s )
    elif isinstance( o2, Bits ):
      if not issubclass( o1._dsl.Type, Bits ):
        raise InvalidConnectionError( "We don't support connecting a Bits{} constant "
                                      "to non-Bits type {}".format( o2.nbits, o1._dsl.Type ) )
      if o1._dsl.Type.nbits != o2.nbits:
        raise InvalidConnectionError( "Bitwidth mismatch when connecting a Bits{} constant "
                                      "to signal {} with type Bits{}.".format( o2.nbits, o1, o1._dsl.Type.nbits ) )
      o2 = Const( o1._dsl.Type, o2, s )

  # TODO implement connecting a const struct

    host = o1.get_host_component()

    if isinstance( o1, InPort ):
      # connecting constant to inport should be at the parent level
      host = host.get_parent_object()

    o2._dsl.parent_obj = s
    s._dsl.consts.add( o2 )

    # o2 should be a new object

    s._dsl.adjacency[o1].add( o2 )
    s._dsl.adjacency[o2].add( o1 )

    s._dsl.connect_order.append( (o1, o2) )

  def _connect_signal_signal( s, o1, o2 ):
    o1_type = None
    o2_type = None

    try:  o1_type = o1._dsl.Type
    except AttributeError:  pass
    try:  o2_type = o2._dsl.Type
    except AttributeError:  pass

    if o1_type is None:
      if o2_type is None:
        if o1 not in s._dsl.adjacency[o2]:
          assert o2 not in s._dsl.adjacency[o1]
          s._dsl.adjacency[o1].add( o2 )
          s._dsl.adjacency[o2].add( o1 )
          s._dsl.connect_order.append( (o1, o2) )
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
      assert o1_nbits == o2_nbits, "Bitwidth mismatch {} != {} " \
      "({}-bit {} <> {}-bit {})".format( o1_nbits, o2_nbits, o1_nbits, repr(o1), o2_nbits, repr(o2) )
    except AttributeError: # at least one of them is not Bits
      assert o1_type == o2_type, "Type mismatch {} != {}".format( o1_type, o2_type )

    if o1 not in s._dsl.adjacency[o2]:
      assert o2 not in s._dsl.adjacency[o1]
      s._dsl.adjacency[o1].add( o2 )
      s._dsl.adjacency[o2].add( o1 )

      s._dsl.connect_order.append( (o1, o2) )

  def _connect_interfaces( s, o1, o2 ):
    # When we connect two interfaces, we first try to use o1's and o2's
    # connect. If failed, we fall back to by-name connection

    def connect_by_name( this, other ):
      def recursive_connect( this_obj, other_obj ):
        if isinstance( this_obj, list ):
          for i in xrange(len(this_obj)):
            # TODO add error message if other_obj is not a list
            recursive_connect( this_obj[i], other_obj[i] )
        else:
          s._connect_objects( other_obj, this_obj, internal=True )

      # Sort the keys to always connect in a unique order
      for name in sorted(this.__dict__):
        if not name.startswith("_"):
          obj = this.__dict__[ name ]
          if hasattr( other, name ):
            # other has the corresponding field, connect recursively
            recursive_connect( obj, getattr( other, name ) )

          else:
            # other doesn't have the corresponding field, raise error
            # if obj is connectable.
            if isinstance( obj, Connectable ):
              raise InvalidConnectionError("There is no \"{}\" field in {} "
              "to connect to {} during by-name connection\n"
              "Suggestion: check the implementation of \n"
              "          - {} (class {})\n"
              "          - {} (class {})".format( name, other, obj,
                repr(this), type(this), repr(other), type(other) ) )

    if hasattr( o1, "connect" ):
      if not o1.connect( o2, s ): # o1.connect fail
        if hasattr( o2, "connect" ):
          if not o2.connect( o1, s ):
            connect_by_name( o1, o2 )
        else:
          connect_by_name( o1, o2 )

    else: # o1 has no "connect"
      if hasattr( o2, "connect" ):
        if not o2.connect( o1, s ):
          connect_by_name( o1, o2 )
      else:
        connect_by_name( o1, o2 ) # capture s

  def _connect_objects( s, o1, o2, internal=False ):
    """ Top level private method for connecting two objects. We do
        the function dispatch based on type here. Note that internal=False
        means we are just calling this API internally so that we don't
        connect other unconnectable fields by name in the interface."""

    o1_connectable = isinstance( o1, Connectable )
    o2_connectable = isinstance( o2, Connectable )

    if not o1_connectable and not o2_connectable:
      if internal:
        return
      raise InvalidConnectionError("class {} and class {} are both not connectable.\n"
          "  (when connecting {} to {})" \
                .format( type(o1), type(o2), repr(o1), repr(o2)) )

    # Deal with Signal <-> const
    # TODO implement connecting a signal to a struct

    if isinstance( o1, (int, Bits) ) or isinstance( o2, (int, Bits)  ): # special case
      if isinstance( o1, (int, Bits)  ):
        o1, o2 = o2, o1 # o1 is signal, o2 is int
      assert isinstance( o1, Signal )
      s._connect_signal_const( o1, o2 )

    # Deal with Signal <-> Signal

    elif isinstance( o1, Signal ) and isinstance( o2, Signal ):
      s._connect_signal_signal( o1, o2 )

    # Deal with Interface <-> Interface

    elif isinstance( o1, Interface ) and isinstance( o2, Interface ):
      s._connect_interfaces( o1, o2 )
      # s._dsl.connect_order.append( (o1, o2) )

    else:
      raise InvalidConnectionError("{} cannot be connected to {}: {} != {}" \
              .format(repr(o1), repr(o2), type(o1), type(o2)) )

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
            s._dsl.parent_obj._connect_objects( obj[idx], item )

        # Obj is a single signal
        # If the target is a list, it's fanout connection
        elif isinstance( target, (tuple, list) ):
          for item in target:
            s._dsl.parent_obj._connect_objects( obj, item )
        # Target is a single object
        else:
          s._dsl.parent_obj._connect_objects( obj, target )

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
      if obj in adjacency and obj not in visited:
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
        if len(net) == 1:
          continue
        nets.append( net )
    return nets

  def _resolve_value_connections( s ):
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

        # Specialize two cases:
        # 1. A top-level input port is writer.
        # 2. An output port of a placeholder module is a writer
        if ( isinstance( member, InPort ) and member._dsl.host == s ) or \
           ( isinstance( member, OutPort ) and isinstance( member._dsl.host, Placeholder ) ):
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

            else:
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
                    # Shunning: is breaking out of here enough? If we
                    # don't break the loop, we might a list here storing
                    # "why the writer became writer" and do some sibling
                    # overlap checks when we enter the loop body later
                    break

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
    nets = s._dsl.all_value_nets

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
      visited = {  writer  }

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
              valid = isinstance( u, (Signal, Const) ) and \
                      isinstance( v, (OutPort, Wire) )
              if not valid:
                raise SignalTypeError( \
"""[Type 5] Invalid port type detected at the same host component "{}" (class {})

- {} "{}" cannot be driven by {} "{}".

  Note: InPort x.y cannot be driven by x.z""" \
          .format(  repr(rhost), type(rhost).__name__,
                    type(v).__name__, repr(v), type(u).__name__, repr(u) ) )

            # 2. reader_host(x) is writer_host(x.y)'s parent:
            # Hence, writer is outport, reader is wire or outport
            # writer cannot be constant
            elif rhost == whost.get_parent_object():
              valid = isinstance( u, OutPort ) and \
                      isinstance( v, (OutPort, Wire) )

              if not valid:
                raise SignalTypeError( \
"""[Type 6] Invalid port type detected when the driver lies deeper than drivee:

- {} "{}" of {} (class {}) cannot be driven by {} "{}" of {} (class {}).

  Note: InPort x.y cannot be driven by x.z.a""" \
          .format(  type(v).__name__, repr(v), repr(rhost), type(rhost).__name__,
                    type(u).__name__, repr(u), repr(whost), type(whost).__name__ ) )

            # 3. writer_host(x) is reader_host(x.y)'s parent:
            # Hence, writer is inport or wire, reader is inport
            # writer can be constant
            elif whost == rhost.get_parent_object():
              # valid = ( isinstance( u, InPort ) or isinstance( u, Wire ) \
                                                 # or isinstance( u, Const)) and \
                         # isinstance( v, InPort )

              # if not valid:
                # raise SignalTypeError( \
# """[Type 7] Invalid port type detected when the driver lies shallower than drivee:

# - {} "{}" of {} (class {}) cannot be driven by {} "{}" of {} (class {}).

  # Note: OutPort/Wire x.y.z cannot be driven by x.a""" \
          # .format(  type(v).__name__, repr(v), repr(rhost), type(rhost).__name__,
                    # type(u).__name__, repr(u), repr(whost), type(whost).__name__ ) )

            # Shunning 9/12/2017: Actually in this case writer can be outport
              valid = isinstance( u, (Signal, Const) ) and isinstance( v, InPort )

              if not valid:
                raise SignalTypeError( \
"""[Type 7] Invalid port type detected when the driver lies shallower than drivee:

- {} "{}" of {} (class {}) cannot be driven by {} "{}" of {} (class {}).

  Note: OutPort/Wire x.y.z cannot be driven by x.a""" \
          .format(  type(v).__name__, repr(v), repr(rhost), type(rhost).__name__,
                    type(u).__name__, repr(u), repr(whost), type(whost).__name__ ) )

            # 4. hosts have the same parent: writer_host(x.y)/reader_host(x.z)
            # This means that the connection is fulfilled in x
            # Hence, writer is outport and reader is inport
            # writer cannot be constant
            elif whost.get_parent_object() == rhost.get_parent_object():
              valid = isinstance( u, OutPort ) and isinstance( v, InPort )

              if not valid:
                raise SignalTypeError( \
"""[Type 8] Invalid port type detected when the drivers is the sibling of drivee:

- {} "{}" of {} (class {}) cannot be driven by {} "{}" of {} (class {}).

  Note: Looks like the connection is fulfilled in "{}".
        OutPort/Wire x.y.z cannot be driven by x.a.b""" \
          .format(  type(v).__name__, repr(v), repr(rhost), type(rhost).__name__,
                    type(u).__name__, repr(u), repr(whost), type(whost).__name__,
                    repr(whost.get_parent_object()) ) )
            # 5. neither host is the other's parent nor the same.
            else:
              raise SignalTypeError("""[Type 9] "{}" and "{}" cannot be connected:

- host objects "{}" and "{}" are too far in the hierarchy.""" \
              .format( repr(u), repr(v), repr(whost), repr(rhost) ) )

  def _disconnect_signal_int( s, o1, o2 ):

    nets = s.get_all_value_nets()

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

    nets = s.get_all_value_nets()

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
    last_adjacency = s._dsl.adjacency
    s._dsl.adjacency = defaultdict(set)
    s._connect_objects( o1, o2 )

    visited = set()
    for u, vs in s._dsl.adjacency.iteritems():
      for v in vs:
        if (u, v) not in visited:
          s._disconnect_signal_signal( u, v )
          visited.add( (u, v) )
          visited.add( (v, u) )

    s._dsl.adjacency = last_adjancency

  # Override
  def _check_valid_dsl_code( s ):
    s._check_upblk_writes()
    s._check_port_in_upblk()
    s._check_port_in_nets()

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
    if isinstance( s, Placeholder ):
      raise InvalidPlaceholderError( "Cannot call connect "
            "in a placeholder component.".format( blk.__name__ ) )
    try:
      s._connect_objects( o1, o2 )
    except InvalidConnectionError:
      raise
    except Exception as e:
      raise InvalidConnectionError( "\n{}".format(e) )

  def connect_pairs( s, *args ):
    if isinstance( s, Placeholder ):
      raise InvalidPlaceholderError( "Cannot call connect_pairs "
            "in a placeholder component.".format( blk.__name__ ) )
    if len(args) & 1 != 0:
       raise InvalidConnectionError( "Odd number ({}) of objects provided.".format( len(args) ) )

    for i in xrange(len(args)>>1) :
      try:
        s._connect_objects( args[ i<<1 ], args[ (i<<1)+1 ] )
      except InvalidConnectionError:
        raise
      except Exception as e:
        raise InvalidConnectionError( "\n- In connect_pair, when connecting {}-th argument to {}-th argument\n\n{}\n " \
              .format( (i<<1)+1, (i<<1)+2 , e ) )

  def get_all_value_nets( s ):

    if s._dsl._has_pending_value_connections:
      s._dsl.all_value_nets = s._resolve_value_connections()
      s._dsl._has_pending_value_connections = False

    return s._dsl.all_value_nets

  #-----------------------------------------------------------------------
  # elaborate
  #-----------------------------------------------------------------------
  # Since the spawned signals are handled by the updated elaborate
  # template in ComponentLevel2, we just need to add a bit more
  # functionalities to handle nets.

  # Override
  def _elaborate_declare_vars( s ):
    super( ComponentLevel3, s )._elaborate_declare_vars()
    s._dsl.all_adjacency = defaultdict(set)

  # Override
  def _elaborate_collect_all_vars( s ):
    super( ComponentLevel3, s )._elaborate_collect_all_vars()
    s._dsl.all_value_nets = s._resolve_value_connections()
    s._dsl._has_pending_value_connections = False

    s._check_valid_dsl_code()

  #-----------------------------------------------------------------------
  # Post-elaborate public APIs (can only be called after elaboration)
  #-----------------------------------------------------------------------
  # We have moved these implementations to Component.py because the
  # outside world should only use Component.py
