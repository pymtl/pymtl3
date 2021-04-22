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
Date   : Jan 29, 2020
"""
import ast
import inspect
import linecache
from collections import defaultdict

from pymtl3.datatypes import Bits, is_bitstruct_inst
from pymtl3.extra.pypy import custom_exec

from .ComponentLevel1 import ComponentLevel1
from .ComponentLevel2 import ComponentLevel2, compiled_re
from .Connectable import (
    Connectable,
    Const,
    InPort,
    Interface,
    OutPort,
    Signal,
    Wire,
    _connect_check,
)
from .errors import (
    InvalidConnectionError,
    InvalidPlaceholderError,
    MultiWriterError,
    NotElaboratedError,
    NoWriterError,
    PyMTLDeprecationError,
    SignalTypeError,
)
from .NamedObject import NamedObject
from .Placeholder import Placeholder


def connect( o1, o2 ):
  host, o1_connectable, o2_connectable = _connect_check( o1, o2, internal=False )
  host._connect_dispatch( o1, o2, o1_connectable, o2_connectable )

class ComponentLevel3( ComponentLevel2 ):

  #-----------------------------------------------------------------------
  # Private methods
  #-----------------------------------------------------------------------

  def __new__( cls, *args, **kwargs ):
    inst = super().__new__( cls, *args, **kwargs )
    inst._dsl.adjacency     = defaultdict(set)
    inst._dsl.connect_order = []
    inst._dsl.consts        = set()

    return inst

  # Override
  def _collect_vars( s, m ):
    super()._collect_vars( m )
    if isinstance( m, ComponentLevel3 ):
      all_ajd = s._dsl.all_adjacency
      for k, v in m._dsl.adjacency.items():
        all_ajd[k] |= v

  # The following three methods should only be called when types are
  # already checked
  def _create_assign_lambda( s, o, lamb ):
    assert isinstance( o, Signal ), "You can only assign(//=) a lambda function to a Wire/InPort/OutPort."

    srcs, line = inspect.getsourcelines( lamb )

    src  = compiled_re.sub( r'\2', ''.join(srcs) ).lstrip(' ')
    root = ast.parse(src)
    assert isinstance( root, ast.Module ) and len(root.body) == 1, "We only support single-statement lambda."

    root = root.body[0]
    assert isinstance( root, ast.AugAssign ) and isinstance( root.op, ast.FloorDiv )

    # lhs, rhs = root.target, root.value
    # Shunning: here we need to use ast from repr(o), because root.target
    # can be "m.in_" in some cases where we actually know what m is but the
    # source code still captures "m"
    lhs, rhs = ast.parse( f"s{repr(o)[len(repr(s)):]}" ).body[0].value, root.value
    lhs.ctx = ast.Store()
    # We expect the lambda to have no argument:
    # {'args': [], 'vararg': None, 'kwonlyargs': [], 'kw_defaults': [], 'kwarg': None, 'defaults': []}
    assert isinstance( rhs, ast.Lambda ) and not rhs.args.args and rhs.args.vararg is None, \
      "The lambda shouldn't contain any argument."

    rhs = rhs.body

    # Compose a new and valid function based on the lambda's lhs and rhs
    # Note that we don't need to add those source code of closure var
    # assignment to linecache. To get the matching line number in the
    # error message, we set the line number of update block
    # Shunning: bugfix:

    blk_name = "_lambda__{}".format( repr(o).replace(".","_").replace("[", "_").replace("]", "_").replace(":", "_") )
    lambda_upblk = ast.FunctionDef(
      name=blk_name,
      args=ast.arguments(args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
      body=[ast.AugAssign(target=lhs, op=ast.MatMult(), value=rhs, lineno=2, col_offset=6)],
      decorator_list=[],
      returns=None,
      lineno=1, col_offset=4,
    )
    lambda_upblk_module = ast.Module(body=[ lambda_upblk ])

    # Manually wrap the lambda upblk with a closure function that adds the
    # desired variables to the closure of `_lambda__*`
    # We construct AST for the following function to add free variables in the
    # closure of the lambda function to the closure of the generated lambda
    # update block.
    #
    # def closure( lambda_closure ):
    #   <FreeVarName1> = lambda_closure[<Idx1>].cell_contents
    #   <FreeVarName2> = lambda_closure[<Idx2>].cell_contents
    #   ...
    #   <FreeVarNameN> = lambda_closure[<IdxN>].cell_contents
    #   def _lambda__<lambda_blk_name>():
    #     # the assignment statement appears here
    #   return _lambda__<lambda_blk_name>

    new_root = ast.Module( body=[
      ast.FunctionDef(
          name="closure",
          args=ast.arguments(args=[ast.arg(arg="lambda_closure", annotation=None, lineno=1, col_offset=12)],
                             vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]),
          body=[
            ast.Assign(
              targets=[ast.Name(id=var, ctx=ast.Store(), lineno=1+idx, col_offset=2)],
              value=ast.Attribute(
                value=ast.Subscript(
                  value=ast.Name(
                    id='lambda_closure',
                    ctx=ast.Load(),
                    lineno=1+idx, col_offset=5+len(var),
                  ),
                  slice=ast.Index(
                    value=ast.Num(
                      n=idx,
                      lineno=1+idx, col_offset=19+len(var),
                    ),
                  ),
                  ctx=ast.Load(),
                  lineno=1+idx, col_offset=5+len(var),
                ),
                attr='cell_contents',
                ctx=ast.Load(),
                lineno=1+idx, col_offset=5+len(var),
              ),
              lineno=1+idx, col_offset=2,
            ) for idx, var in enumerate(lamb.__code__.co_freevars)
          ] + [ lambda_upblk ] + [
            ast.Return(
              value=ast.Name(
                id=blk_name,
                ctx=ast.Load(),
                lineno=4+len(lamb.__code__.co_freevars), col_offset=9,
              ),
              lineno=4+len(lamb.__code__.co_freevars), col_offset=2,
            )
          ],
          decorator_list=[],
          returns=None,
          lineno=1, col_offset=0,
        )
    ] )

    # In Python 3 we need to supply a dict as local to get the newly
    # compiled function from closure.
    # Then `closure(lamb.__closure__)` returns the lambda update block with
    # the correct free variables in its closure.

    dict_local = {}
    custom_exec( compile(new_root, blk_name, "exec"), lamb.__globals__, dict_local )
    blk = dict_local[ 'closure' ]( lamb.__closure__ )

    # Add the source code to linecache for the compiled function

    new_src = "def {}():\n {}\n".format( blk_name, src.replace("//=", "@=") )
    linecache.cache[ blk_name ] = (len(new_src), None, new_src.splitlines(), blk_name)

    ComponentLevel1._update( s, blk )

    # This caching here does no caching because the block name contains
    # the signal name intentionally to avoid conflicts. With //= it is
    # more possible than normal update block to have conflicts:
    # if param == 1:  s.out //= s.in_ + 1
    # else:           s.out //= s.out + 100
    # Here these two blocks will implicity have the same name but they
    # have different contents based on different param.
    # So the cache call here is just to reuse the existing interface to
    # register the AST/src of the generated block for elaborate or passes
    # to use.
    s._cache_func_meta( blk, is_update_ff=False,
      given=("".join(srcs), lambda_upblk_module, line, inspect.getsourcefile( lamb )) )
    return blk

  def _connect_signal_const( s, o1, o2 ):
    Type = o1._dsl.Type
    if isinstance( o2, int ):
      if not issubclass( Type, (int, Bits) ):
        raise InvalidConnectionError( f"We don't support connecting an integer constant "
                                      f"to non-int/Bits type {Type}" )
      o2 = Const( Type, Type(o2), s )
    elif isinstance( o2, Bits ):
      Type2 = type(o2)
      if not issubclass( Type, Bits ):
        raise InvalidConnectionError( f"We don't support connecting a {Type2} constant "
                                      f"to non-Bits type {Type}" )
      # Both bits, check bitwidth
      # use object.nbits instead of Type.nbits to handle both cases: Bits32(2) and Bits(32,2)
      if Type.nbits != o2.nbits:
        raise InvalidConnectionError( f"Bitwidth mismatch when connecting a {Type2} constant "
                                      f"to signal {o1} with type {Type}." )
      o2 = Const( Type, o2, s )
    elif is_bitstruct_inst( o2 ):
      Type2 = type(o2)
      if Type is not Type2:
        raise InvalidConnectionError( f"We don't support connecting a {Type2} constant bitstruct"
                                      f"to non-bitstruct type {Type}" )
      o2 = Const( Type, o2, s )
    else:
      raise InvalidConnectionError(f"\n>>> {o2} of type {type(o2)} is not a const! \n"
                                   f">>> It cannot be connected to signal {o1} of type {o1._dsl.Type}!\n"
                                   f"Suggestion: fix the RHS of connection to be an instance of {o1._dsl.Type}.")

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
    if not (o1._dsl.Type is o2._dsl.Type):
      raise InvalidConnectionError( f"Bitwidth mismatch {o1._dsl.Type.__name__} != {o2._dsl.Type.__name__}\n"
                                    f"- In class {type(s)}\n- When connecting {o1} <-> {o2}\n"
                                    f"Suggestion: make sure both sides of connection have matching bitwidth")

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
          for i in range(len(this_obj)):
            # TODO add error message if other_obj is not a list
            recursive_connect( this_obj[i], other_obj[i] )
        else:
          s._connect( other_obj, this_obj, internal=True )

      # Sort the keys to always connect in a unique order
      for name in sorted(this.__dict__):
        if name[0] != '_': # filter private variables
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

  def _connect( s, o1, o2, internal ):
    """ Top level private method for connecting two objects. """
    host, o1_connectable, o2_connectable = _connect_check( o1, o2, internal )

    if host is None:
      # host is None only happens when internal = True
      assert internal

    else:
      assert s is host, "Please contact pymtl3 developer -- s:{} host:{}".format(s, host)
      s._connect_dispatch( o1, o2, o1_connectable, o2_connectable )

  def _connect_dispatch( s, o1, o2, o1_connectable, o2_connectable ):

    if o1_connectable and o2_connectable:
      # if both connectable, dispatch signal-signal and interface-interface
      if isinstance( o1, Signal ) and isinstance( o2, Signal ):
        s._connect_signal_signal( o1, o2 )
      elif isinstance( o1, Interface ) and isinstance( o2, Interface ):
        s._connect_interfaces( o1, o2 )
      else:
        raise InvalidConnectionError("{} cannot be connected to {}: {} != {}" \
              .format(repr(o1), repr(o2), type(o1), type(o2)) )
    else:
      # One is connectable, we make sure it's o1
      if o2_connectable:
        o1, o2 = o2, o1
      assert isinstance( o1, Signal ), f"Cannot connect {o1!r} to {o2!r}."

      s._connect_signal_const( o1, o2 )

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
        Q   = [ obj ]
        while Q:
          u = Q.pop()
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

    for blk, writes in s._dsl.all_upblk_writes.items():
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
        host = member.get_host_component()

        # Specialize two cases:
        # 1. A top-level input port is writer.
        # 2. An output port of a placeholder module is a writer
        if ( isinstance( member, InPort ) and host == s ) or \
           ( isinstance( member, OutPort ) and isinstance( host, Placeholder ) ):
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

      S = [ writer ]
      visited = { writer }

      while S:
        u = S.pop() # u is the writer
        whost = u.get_host_component()

        for v in s._dsl.all_adjacency[u]: # v is the reader
          if v not in visited:
            visited.add( v )
            S.append( v )
            rhost = v.get_host_component()

            # 1. have the same host: writer_host(x)/reader_host(x):
            # Hence, writer is anything, reader is wire or outport
            if   whost == rhost:
              valid = isinstance( u, (Signal, Const) ) and \
                      isinstance( v, (OutPort, Wire) )
              if not valid:
                # Check if it's an outport driving inport. If it is
                # connected at parent level, we permit this loopback from
                # parent level.
                if isinstance( u, OutPort ) and isinstance( v, InPort ):
                  u_connected_in_whost = v in whost._dsl.adjacency and u in whost._dsl.adjacency[v]
                  v_connected_in_whost = u in whost._dsl.adjacency and v in whost._dsl.adjacency[u]
                  assert u_connected_in_whost == v_connected_in_whost, "Please contact pymtl3 developers."

                  parent = whost.get_parent_object()
                  u_connected_in_parent = v in parent._dsl.adjacency and u in parent._dsl.adjacency[v]
                  v_connected_in_parent = u in parent._dsl.adjacency and v in parent._dsl.adjacency[u]
                  assert u_connected_in_parent == v_connected_in_parent, "Please contact pymtl3 developers."

                  assert u_connected_in_whost != u_connected_in_parent, "Please contact pymtl3 developers."

                  # We permit this loopback from parent level. Otherwise
                  # we throw an error
                  if not u_connected_in_parent:
                    raise InvalidConnectionError( \
"""InPort and OutPort loopback connection is only allowed at parent level:

- Unless the connection is fulfilled in parent "{}",
  {} "{}" of {} (class {}) cannot be driven by {} "{}" of {} (class {}).

  Note: Looks like the connection is fulfilled in "{}".""" \
          .format(  parent,
                    type(v).__name__, repr(v), repr(rhost), type(rhost).__name__,
                    type(u).__name__, repr(u), repr(whost), type(whost).__name__,
                    repr(whost) ) )

                else:
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
    raise PyMTLDeprecationError("\n__call__ connection has been deprecated! "
                                "\n- Please use free function connect(s.x,s.y) or "
                                "syntactic sugar s.x//=s.y instead.")

  def connect( s, *args, **kwargs ):
    raise PyMTLDeprecationError("\ns.connect method has been deprecated! "
                                "\n- Please use free function connect(s.x,s.y) or "
                                "syntactic sugar s.x//=s.y instead.")

  #-----------------------------------------------------------------------
  # elaborate
  #-----------------------------------------------------------------------
  # Since the spawned signals are handled by the updated elaborate
  # template in ComponentLevel2, we just need to add a bit more
  # functionalities to handle nets.

  # Override
  def _elaborate_declare_vars( s ):
    super()._elaborate_declare_vars()
    s._dsl.all_adjacency = defaultdict(set)

  # Override
  def _elaborate_collect_all_vars( s ):
    super()._elaborate_collect_all_vars()
    s._dsl.all_value_nets = s._resolve_value_connections()
    s._dsl._has_pending_value_connections = False

    s._check_valid_dsl_code()

  #-----------------------------------------------------------------------
  # Post-elaborate public APIs (can only be called after elaboration)
  #-----------------------------------------------------------------------
  # We have moved these implementations to Component.py because the
  # outside world should only use Component.py

  def get_all_value_nets( s ):

    if s._dsl._has_pending_value_connections:
      s._dsl.all_value_nets = s._resolve_value_connections()
      s._dsl._has_pending_value_connections = False

    return s._dsl.all_value_nets
