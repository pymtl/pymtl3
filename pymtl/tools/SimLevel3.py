from SimLevel2 import SimLevel2
from pymtl.components import UpdateConnect
from pymtl.components import Connectable, Wire
from collections import defaultdict, deque

class SimLevel3( SimLevel2 ):

  def __init__( self, model, tick_mode='unroll' ):
    self.model = model

    self.recursive_tag_name( model )
    self.recursive_elaborate( model )
    self.recursive_tag_name( model ) # slicing will spawn extra objects

    nets = self.resolve_var_connections()

    # self.print_read_write()
    # self.print_nets( nets )
    # self.check_port_direction( nets ) # port type check

    self.compact_readers( nets ) # this is just for simulation
    # self.print_nets( nets )

    self.synthesize_var_constraints()
    serial, batch = self.schedule( self._blkid_upblk, self._constraints )

    self.print_schedule( serial, batch )
    self.tick = self.generate_tick_func( serial, tick_mode )

    self.cleanup_wires( self.model )

  # Override
  def _declare_vars( self ):
    super( SimLevel3, self )._declare_vars()
    self._varid_net = {}

  # Override
  def _collect_vars( self, m ):
    super( SimLevel3, self )._collect_vars( m )

    if isinstance( m, Connectable ):
      root = m._find_root()
      if len( root._connected ) > 1: # has actual connection
        if id(root) not in self._varid_net:
          self._varid_net[ id(root) ] = root._connected

  def resolve_var_connections( self ):

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
      obj = self._id_obj[ wid ]
      writer_prop[ wid ] = True # propagatable

      assert len(self._write_upblks[wid]) == 1, "Multiple update blocks write %s.\n - %s" % \
            ( obj.full_name(), "\n - ".join([ self._blkid_upblk[x].__name__  \
                                for x in self._write_upblks[ wid ] ]) )

      obj = obj._nested
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

      for net in headless:
        has_writer = False

        for v in net:
          if id(v) in writer_prop: # Check if itself is a writer
            has_writer, writer, from_sibling = True, v, False

          while obj: # Check if the parent is a propagatable writer
            oid = id(obj)
            if oid in writer_prop and writer_prop[ oid ]:
              assert not has_writer, \
                    "Two-writer conflict \"%s\" (overlap \"%s\"), \"%s\" in the following net:\n - %s" % \
                    (v.full_name(), obj.full_name(), writer.full_name(),"\n - ".join([x.full_name() for x in net]))
              has_writer, writer, from_sibling = True, v, False
              break
            obj = obj._nested

          if not v._slice:  continue

          # Similarly, if x[0:10] is written in update block, x[5:15] can
          # be a unpropagatable writer because we don't want x[5:15] to
          # propagate to x[12:17] later.

          for obj in v._nested._slices.values(): # Check sibling slices
            if v == obj or not overlap(obj._slice, v._slice):
              continue # Skip the same slice or not overlapped

            oid = id(obj)
            if oid in writer_prop and writer_prop[ oid ]:
              assert not has_writer, \
                    "Two-writer conflict \"%s\" (overlap \"%s\"), \"%s\" in the following net:\n - %s" % \
                    (v.full_name(), obj.full_name(), writer.full_name(),
                    "\n - ".join([ x.full_name() for x in net ]))
              has_writer, writer, from_sibling = True, v, True

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

      assert wcount < len(writer_prop), "The following nets need drivers.\nNet:\n - %s " % \
            ("\nNet:\n - ".join([ "\n - ".join([ x.full_name() for x in y ]) for y in headless ]))
      headless = new_headless

    return headed

  def generate_net_block( self, nets ):

    for net in nets:

      # find common ancestor

      ancestor.add_update_block( )

  def check_port_direction( self, nets ):
    pass

  def compact_readers( self, nets ):

    # Each net is an update block. Readers are actually "written" here.
    # def up_net_writer_to_readers():
    #   s.net_reader1 = s.net_writer
    #   s.net_reader2 = s.net_writer
    # Collect readers in normal update blocks plus the writers in nets.
    # s.x = s.y reads s.y and writes s.x

    all_reads = set()

    # First add normal update block reads
    for read in self._read_upblks:
      obj = self._id_obj[ read ]
      while obj:
        all_reads.add( id(obj) )
        obj = obj._nested

    # Then add net writers
    for writer, readers in nets:
      obj = writer
      while obj:
        all_reads.add( id(obj) )
        obj = obj._nested

    # Now figure out if a reader can be safely removed from the net
    # Check if the reader itself, its ancestors, or sibling slices are
    # read somewhere else. If not, the reader can be moved from the net.

    for i in xrange(len(nets)):
      writer, readers = nets[i]
      new_readers = []

      for x in readers:
        flag = False
        obj = x
        while obj:
          if id(obj) in all_reads:
            flag = True
            break
          obj = obj._nested

        if x._slice:
          for obj in x._nested._slices.values(): # Check sibling slices
            if x != obj and overlap(obj._slice, x._slice) and \
                id(obj) in all_reads:
              flag = True
              break

        if flag: new_readers.append( x )

      nets[i] = (writer, new_readers)

  @staticmethod
  def print_nets( nets ):
    for n in nets:
      writer, readers = n
      print
      print "writer: \n + {}\nreader:\n - {}".format( writer.full_name(), "\n - ".join([ v.full_name() for v in readers ]) )
