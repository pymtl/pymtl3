#=========================================================================
# ComponentLevel3.py
#=========================================================================

from ComponentLevel2 import ComponentLevel2
from Connectable import Connectable, Signal, InVPort, OutVPort, Wire, Const, _overlap
from errors      import InvalidConnectionError, SignalTypeError, NoWriterError, MultiWriterError
from collections import defaultdict, deque

import inspect, ast # for error message

class ComponentLevel3( ComponentLevel2 ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def _resolve_var_connections( s ):
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

    nets = s._all_nets = []

    visited = set()
    for obj in s._pymtl_objs:
      if isinstance( obj, Signal ) and obj._adjs and obj not in visited:
        net = []
        Q   = deque( [ obj ] )
        while Q:
          u = Q.popleft()
          visited.add( u )
          net.append( u )
          Q.extend( [ v for v in u._adjs if v not in visited ] )
        nets.append( net )

    # Then figure out writers: all writes in upblks and their nest objects

    writer_prop = {}

    for blk, writes in s._all_upblk_writes.iteritems():
      for obj in writes:
        writer_prop[ obj ] = True # propagatable

        obj = obj._nested
        while obj:
          writer_prop[ obj ] = False
          obj = obj._nested

    # Find the host object of every net signal
    # and then leverage the information to find out top level input port

    for net in nets:
      for member in net:
        host = member
        while not isinstance( host, ComponentLevel3 ):
          host = host._parent_obj # go to the component
        member._host = host

        if isinstance( member, InVPort ) and member._host == s:
          writer_prop[ member ] = True

    headless = nets
    headed   = [] # [ ( writer, [readers] ) ]

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
            obj = v._nested
            while obj:
              if obj in writer_prop and writer_prop[ obj ]:
                assert not has_writer
                has_writer, writer = True, v
                break
              obj = obj._nested

            # Check sibling slices
            if v._slice:
              for obj in v._nested._slices.values():
                if v is obj or not _overlap(obj._slice, v._slice):
                  continue # Skip the same slice or not overlapped

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

        readers = []

        # Child s.x.y of some propagatable s.x, or sibling of some
        # propagatable s[a:b].
        # This means that at least other variables are able to see s.x/s[a:b]
        # so it doesn't matter if s.x.y is not in writer_prop
        if writer not in writer_prop:
          pass

        for v in net:
          if v != writer:
            readers.append( v )
            writer_prop[ v ] = True # The reader becomes new writer

            obj = v._nested
            while obj:
              if obj not in writer_prop:
                writer_prop[ obj ] = False
              obj = obj._nested

        headed.append( (writer, readers) )

      if wcount == len(writer_prop): # no more new writers
        raise NoWriterError( headless )
      headless = new_headless

    s._all_nets = headed

  def _check_port_in_nets( s ):
    nets = s._all_nets

    # The case of connection is very tricky because we put a single upblk
    # in the lowest common ancestor node and the "output port" chain is
    # inverted. So we need to deal with it here ...
    #
    # The gist is that the data flows from deeper level writer to upper
    # level readers via output port, to the same level via wire, and from
    # upper level to deeper level via input port

    for writer, readers in nets:

      # We need to do DFS to check all connected port types
      # Each node is a writer when we expand it to other nodes

      S = deque( [ writer ] )
      visited = set( [ writer ] )

      while S:
        u = S.pop() # u is the writer
        whost = u._host

        for v in u._adjs: # v is the reader
          if v not in visited:
            visited.add( v )
            S.append( v )
            rhost = v._host

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
            elif rhost == whost._parent_obj:
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
            elif whost == rhost._parent_obj:
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
            elif whost._parent_obj == rhost._parent_obj:
              valid = isinstance( u, OutVPort ) and isinstance( v, InVPort )

              if not valid:
                raise SignalTypeError( \
"""[Type 8] Invalid port type detected when the drivers is the sibling of drivee:

- {} "{}" of {} (class {}) cannot be driven by {} "{}" of {} (class {}).

  Note: Looks like the connection is fulfilled in "{}".
        OutVPort/Wire x.y.z cannot be driven by x.a.b""" \
          .format(  type(v).__name__, repr(v), repr(rhost), type(rhost).__name__,
                    type(u).__name__, repr(u), repr(whost), type(whost).__name__,
                    repr(whost._parent_obj) ) )
            # 5. neither host is the other's parent nor the same.
            else:
              raise SignalTypeError("""[Type 9] "{}" and "{}" cannot be connected:

- host objects "{}" and "{}" are too far in the hierarchy.""" \
              .format( repr(u), repr(v), repr(whost), repr(rhost) ) )

  #-----------------------------------------------------------------------
  # Construction-time APIs
  #-----------------------------------------------------------------------

  def connect( s, o1, o2 ):
    """ Connect two objects. If one of them is integer, create a new Const
    that wraps around it in 's'. This is why connecting a constant should be
    done via this function in the component """

    try:
      if isinstance( o1, int ) or isinstance( o2, int ): # special case
        if isinstance( o1, int ):
          o1, o2 = o2, o1 # o1 is signal, o2 is int
          assert isinstance( o1, Connectable )

        const = Const( o1.Type, o2 )
        const._parent_obj = s
        o1._connect( const )

      else: # normal
        assert isinstance( o1, Connectable ) and isinstance( o2, Connectable )
        assert o1.Type == o2.Type
        o1._connect( o2 )

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

  def __call__( s, *args, **kwargs ):
    assert args == ()

    # The first loop checks if there is any invalid connection
    # TODO check if all list/tuple of objects are connected to output ports

    for (kw, item) in kwargs.iteritems():
      item_valid = True

      try:
        obj = getattr( s, kw )
      except AttributeError:
        raise InvalidConnectionError( "{} is not a member of class {}".format(kw, s.__class__) )

      if   isinstance( obj, list ): # out = {0:x, 1:y}
        if not isinstance( item, dict ):
          raise InvalidConnectionError( "We only support a dictionary when '{}' is an array.".format( kw ) )
        for idx in item:
          if isinstance( item[idx], int ):
            item_valid, error_idx = False, item[idx]
            break
      elif isinstance( item, tuple ) or isinstance( item, list ):
        for x in item:
          if isinstance( item, int ):
            item_valid, error_idx = False, x
            break
      elif isinstance( item, int ):
        item_valid, error_idx = False, item

      if not item_valid:
        raise InvalidConnectionError( "Connecting port {} to constant {} can only be done through \"s.connect\".".format( kw, error_idx ) )

    # Then do the connection

    try:
      for (kw, item) in kwargs.iteritems():
        obj = getattr( s, kw )

        if   isinstance( obj, list ):
          for idx in item:
            obj[idx]._connect( item[idx] )
        elif isinstance( item, tuple ) or isinstance( item, list ):
          for x in item:
            obj._connect( x )
        else:
          obj._connect( item )

    except AssertionError as e:
      raise InvalidConnectionError( "Invalid connection for {}:\n{}".format( kw, e ) )

    return s

  #-----------------------------------------------------------------------
  # elaborate
  #-----------------------------------------------------------------------

  # Override
  def elaborate( s ):
    s._declare_vars()

    s._tag_name_collect() # tag and collect first
    for obj in s._pymtl_objs:
      if isinstance( obj, ComponentLevel2 ):
        obj._elaborate_read_write_func() # this function is local to the object
      s._collect_vars( obj )
    s._tag_name_collect() # slicing will spawn extra objects

    s._resolve_var_connections()

    s._check_upblk_writes()
    s._check_port_in_upblk()
    s._check_port_in_nets()

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
      return s._all_nets
    except AttributeError:
      raise NotElaboratedError()
