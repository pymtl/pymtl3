#-------------------------------------------------------------------------
# VarNetElaborationPass
#-------------------------------------------------------------------------

from pymtl.passes import TagNamePass, VarElaborationPass
from pymtl.components import Signal, Const, UpdateVarNet, _overlap
from collections import deque, defaultdict
from pymtl.components.errors import NoWriterError, MultiWriterError

class VarNetElaborationPass( VarElaborationPass ):
  def __init__( self, dump=True ):
    self.dump = dump

  def execute( self, m ):
    m = TagNamePass().execute( m ) # tag name first for error message
    self.recursive_elaborate( m )
    m = TagNamePass().execute( m ) # slicing will spawn extra objects
    self.check_upblk_writes( m )

    if self.dump:
      self.print_read_write()

    self.resolve_var_connections( m ) # after spawned objects get tagged

    if self.dump:
      self.print_nets()

    return m

  # Override
  def _declare_vars( self ):
    super( VarNetElaborationPass, self )._declare_vars()
    self._varid_net = {}

  # Override
  def _collect_vars( self, m ):
    super( VarNetElaborationPass, self )._collect_vars( m )

    if isinstance( m, Signal ):
      root = m._find_root()
      if len( root._connected ) > 1: # has actual connection
        if id(root) not in self._varid_net:
          self._varid_net[ id(root) ] = root._connected

  def resolve_var_connections( self, m ):

    # The case of nested data struct: the writer of a net can be one of
    # the three: signal itself (s.x.a), ancestor (s.x), descendant (s.x.b)
    #
    # An iterative algorithm is required to mark the writers. The example
    # is the following. Net 1's writer is s.x and one reader is s.y.
    # Net 2's writer is s.y.a (known ONLY after Net 1's writer is clear),
    # one reader is s.z. Net 3's writer is s.z.a (known ...), and so forth
    #
    # Note that s.x becomes writer when WR s.x.a or WR s.x.b, but s.x then
    # cannot propagate back to s.x.b or s.x.a.
    # The original state is all the writers from all update blocks.
    # writer_prop is a dict {x:y} that stores potential writers and
    # whether the writer can propagate to other nets. After a net is
    # resolved from headless condition, its readers become writers.

    # The case of slicing: slices of the same wire are only one level
    # deeper, so all of those parent/child relationship work easily.
    # However, unlike different fields of a data struct, different slices
    # may _intersect_, so they need to check sibling slices' write/read
    # status as well.

    writer_prop = {}

    for wid in self._write_upblks:
      writer_prop[ wid ] = True # propagatable

      obj = self._id_obj[ wid ]._nested
      while obj:
        writer_prop[ id(obj) ] = False
        obj = obj._nested

    headless = self._varid_net.values()
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
            if id(v) in writer_prop or isinstance( v, Const ): 
              assert not has_writer
              has_writer, writer, from_sibling = True, v, False

            # Check if an ancestor is a propagatable writer
            obj = v._nested
            while obj:
              oid = id(obj)
              if oid in writer_prop and writer_prop[ oid ]:
                assert not has_writer
                has_writer, writer, from_sibling = True, v, False
                break
              obj = obj._nested

            # Check sibling slices
            if v._slice:
              for obj in v._nested._slices.values():
                if v == obj or not _overlap(obj._slice, v._slice):
                  continue # Skip the same slice or not overlapped

                oid = id(obj)
                if oid in writer_prop and writer_prop[ oid ]:
                  assert not has_writer
                  has_writer, writer, from_sibling = True, v, True

          except AssertionError:
            raise MultiWriterError( \
            "Two-writer conflict \"{}\"{}, \"{}\" in the following net:\n - {}".format(
              repr(v), "" if not obj else "(as \"{}\" is written somewhere else)".format( repr(obj) ),
              repr(writer), "\n - ".join([repr(x) for x in net])) )

        if not has_writer:
          new_headless.append( net )
          continue

        readers = []

        # Child of some propagatable s.x, or sibling of some propagatable s[a:b]
        if id(writer) not in writer_prop:
          writer_prop[ id(writer) ] = not from_sibling # from sibling means cannot propagate

        for v in net:
          if v != writer:
            readers.append( v )
            writer_prop[ id(v) ] = True # The reader becomes new writer

            obj = v._nested
            while obj:
              oid = id(obj)
              if oid not in writer_prop:
                writer_prop[ oid ] = False
              obj = obj._nested

        headed.append( (writer, readers) )

      if wcount == len(writer_prop): # no more new writers
        raise NoWriterError( headless )
      headless = new_headless

    # Find the host object of every object in nets

    for writer, readers in headed:
      obj = writer
      while not isinstance( obj, UpdateVarNet ):
        obj = obj._parent # go to the component
      writer._host = obj

      for reader in readers:
        obj = reader
        while not isinstance( obj, UpdateVarNet ):
          obj = obj._parent # go to the component
        reader._host = obj

    m._nets = self._nets = headed

  def print_nets( self ):
    print
    print "+-------------------------------------------------------------"
    print "+ All connected nets"
    print "+-------------------------------------------------------------"
    print

    for n in self._nets:
      writer, readers = n
      print
      print "  * Writer:\n    + {}\n  * Reader(s):\n    - {}" \
            .format( repr(writer), "\n    - ".join([ repr(v) for v in readers ]) )
