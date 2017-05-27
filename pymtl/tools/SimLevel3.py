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

    self.print_nets( nets )

    # self.check_port_direction_check( nets )

    # self.mark_readers( nets )

    self.synthesize_var_constraints()
    serial, batch = self.schedule( self._blkid_upblk, self._constraints )

    self.print_schedule( serial, batch )
    self.tick = self.generate_tick_func( serial, tick_mode )

    self.cleanup_wires( self.model )

  @staticmethod
  def print_nets( nets ):
    for n in nets:
      writer, readers = n
      print 
      print "writer: \n + {}\nreader:\n - {}".format( writer.full_name(), "\n - ".join([ v.full_name() for v in readers ]) )

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

    # A writer of a net is one of the three: some signal itself, ancestor
    # of some signal, or descendant of some signal.
    #
    # We need to use an iterative algorithm to figure out the writer of
    # each net. The example is the following. Net 1's writer is s.x
    # and one of the reader is s.y. Net 2's writer is s.y.a but we know it
    # only after we figure out Net 1's writer, and one of the reader is
    # s.z. Net 3's writer is s.z.a but we only know it after we figure out
    # Net 2's writer, and so forth.

    # s.x will be propagated by WR s.x.a or WR s.x.b, but the propagated
    # s.x cannot propagate back to s.x.a or s.x.b
    # The original state is all the writers from all update blocks.
    # writer_prop is a dict {x:y} that stores potential writers and
    # whether the writer can propagate to other nets. After a net is
    # resolved from headless condition, its readers become the writer.

    # The case of slicing is slightly different from data struct. Slices
    # of the same wire are one level deeper than the original wire, so
    # all of those parent/child relationship will work in a simpler way.
    # However, unlike different fields of a data struct, different slices
    # may intersect, so they need to check sibling slices' write/read
    # status as well.

    writer_prop = {}

    for wid in self._write_upblks:
      obj = self._id_obj[ wid ]
      writer_prop[ wid ] = True # propagatable

      assert len( self._write_upblks[wid] ) == 1, "Multiple update blocks write %s.\n - %s" % \
            ( obj.full_name(), "\n - ".join([ self._blkid_upblk[x].__name__ \
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
      # an unpropagatable writer because later s.x.c shouldn't be marked
      # as writer by s.x.

      for net in headless:
        has_writer, writer = False, None
        from_sibling = False

        for v in net:
          if id(v) in writer_prop: # Check if itself is a writer 
            has_writer, writer = True, v

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
            # Skip the same slice or not overlap
            if v == obj or not overlap(obj._slice, v._slice): continue

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
