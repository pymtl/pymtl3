from SimLevel2 import SimLevel2
from pymtl.components import UpdateConnect
from pymtl.components import Connectable, Signal, Wire, InVPort, OutVPort, _overlap
from collections import defaultdict, deque
import re, ast
p = re.compile('( *(@|def))')

class SimLevel3( SimLevel2 ):

  def __init__( self, model, tick_mode='unroll' ):
    self.model = model

    self.recursive_tag_name( model )  # tag name first for error message
    self.recursive_elaborate( model ) # turn "string" into objects
    self.recursive_tag_name( model )  # slicing will spawn extra objects
    self.check_port_in_upblk()        # in/out port check in all upblks
    # self.print_read_write()

    self.resolve_var_connections() # resolve connected nets
    self.check_port_in_net()       # in/out port check in all nets
    self.compact_net_readers()     # remove unread objs, for simulation
    # self.print_nets( self._nets )

    self.generate_net_block()

    expl, impl    = self.synthesize_var_constraints()
    serial, batch = self.schedule( self._blkid_upblk, self._constraints )
    # self.print_constraints( expl, impl )
    # self.print_schedule( serial, batch )

    self.tick = self.generate_tick_func( serial, tick_mode )

    self.cleanup_wires( self.model ) # getting ready for simulation

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
      #
      # Similarly, if x[0:10] is written in update block, x[5:15] can
      # be a unpropagatable writer because we don't want x[5:15] to
      # propagate to x[12:17] later.

      for net in headless:
        has_writer = False

        for v in net:
          obj = None
          try:
            if id(v) in writer_prop: # Check if itself is a writer
              assert not has_writer
              has_writer, writer, from_sibling = True, v, False

            obj = v._nested
            while obj: # Check if the parent is a propagatable writer
              oid = id(obj)
              if oid in writer_prop and writer_prop[ oid ]:
                assert not has_writer
                has_writer, writer, from_sibling = True, v, False
                break
              obj = obj._nested

            if v._slice: # Check sibling slices
              for obj in v._nested._slices.values(): # Check sibling slices
                if v == obj or not _overlap(obj._slice, v._slice):
                  continue # Skip the same slice or not overlapped

                oid = id(obj)
                if oid in writer_prop and writer_prop[ oid ]:
                  assert not has_writer
                  has_writer, writer, from_sibling = True, v, True
          except:
            assert False, "Two-writer conflict \"%s\"%s, \"%s\" in the following net:\n - %s" % \
                          (v.full_name(),
                          "" if not obj else "(overlap \"%s\")" % obj.full_name(),
                          writer.full_name(),"\n - ".join([x.full_name() for x in net]))

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

    # Find the host object of every object in nets

    for writer, readers in headed:
      obj = writer
      while not isinstance( obj, UpdateConnect ):
        obj = obj._parent # go to the component
      writer._host = obj

      for reader in readers:
        obj = reader
        while not isinstance( obj, UpdateConnect ):
          obj = obj._parent # go to the component
        reader._host = obj

    self._nets = headed

  def generate_net_block( self ):
    nets = self._nets

    for writer, readers in nets:
      if not readers:
        continue # Aha, the net is dummy
      wr_lca  = writer
      rd_lcas = readers[::]

      # Find common ancestor: iteratively go to parent level and check if
      # at the same level all objects' ancestor are the same

      mindep  = min( len( writer._name_idx[1] ),
                     min( [ len(x._name_idx[1]) for x in rd_lcas ] ) )

      # First navigate all objects to the same level deep

      for i in xrange( mindep, len(wr_lca._name_idx[1]) ):
        wr_lca = wr_lca._parent

      for i, x in enumerate( rd_lcas ):
        for j in xrange( mindep, len( x._name_idx[1] ) ):
          x = x._parent
        rd_lcas[i] = x

      # Then iteratively check if their ancestor is the same

      while wr_lca != self.model:
        succeed = True
        for x in rd_lcas:
          if x != wr_lca:
            succeed = False
            break
        if succeed: break

        wr_lca = wr_lca._parent
        for i in xrange( len(rd_lcas) ):
          rd_lcas[i] = rd_lcas[i]._parent

      lca     = wr_lca # this is the object we want to insert the block to
      lca_len = len( lca.full_name() )
      fanout  = len( readers )
      wstr    = "s." + writer.full_name()[lca_len+1:]
      rstrs   = [ "s." + x.full_name()[lca_len+1:] for x in readers]

      upblk_name = "{}_FANOUT_{}".format(writer.full_name(), fanout)\
                    .replace( ".", "_" ).replace( ":", "_" ) \
                    .replace( "[", "_" ).replace( "]", "_" )

      # TODO port common prefix optimization, currently only multi-writer

      # NO @s.update because I don't want to impair the original model
      if fanout == 1: # simple mode!
        gen_connection_src = """

def {0}():
  {1}
blk = {0}

        """.format( upblk_name,"{} = {}".format( rstrs[0], wstr ) )
      else:
        gen_connection_src = """

def {0}():
  common_writer = {1}
  {2}
blk = {0}
        """.format( upblk_name, wstr, "\n  ".join(
                    [ "{} = common_writer".format( x ) for x in rstrs] ) )

      # Collect block metadata

      blk         = lca._compile_update_block( gen_connection_src )
      blk.hostobj = lca
      blk.ast     = ast.parse( gen_connection_src )

      blk_id = id(blk)
      self._name_upblk[ upblk_name ] = blk
      self._blkid_upblk[ blk_id ] = blk

      # Collect read/writer metadata

      self._read_upblks[ id(writer) ].append( blk_id )
      self._id_obj[ id(writer) ] = writer
      for x in readers:
        self._write_upblks[ id(x) ].append( blk_id )
        self._id_obj[ id(x) ] = x

  def check_port_in_net( self ):
    nets = self._nets

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
      visited = set( [ id(writer) ] )

      while S:
        u = S.pop() # u is the writer
        whost = u._host

        for v in u._adjs: # v is the reader
          if id(v) not in visited:
            visited.add( id(v) )
            S.append( v )
            rhost = v._host

            # 1. have the same host: writer_host(x)/reader_host(x):
            # Hence, writer is anything, reader is wire or outport
            if   whost == rhost:
              assert    isinstance( u, Signal ) and \
                      ( isinstance( v, OutVPort) or isinstance( v, Wire ) ), \
"""[Type 1] Invalid port type detected at the same host component \"{}\" (class {})

- {} \"{}\" cannot be driven by {} \"{}\".

  Note: InVPort x.y cannot be driven by x.z""" \
          .format(  rhost.full_name(), type(rhost).__name__,
                    type(v).__name__, v.full_name(), type(u).__name__, u.full_name() )

            # 2. reader_host(x) is writer_host(x.y)'s parent:
            # Hence, writer is outport, reader is wire or outport
            elif rhost == whost._parent:
              assert  isinstance( u, OutVPort) and \
                    ( isinstance( v, OutVPort ) or isinstance( v, Wire ) ), \
"""[Type 2] Invalid port type detected when the driver lies deeper than drivee:

- {} \"{}\" of {} (class {}) cannot be driven by {} \"{}\" of {} (class {}).

  Note: InVPort x.y cannot be driven by x.z.a""" \
          .format(  type(v).__name__, v.full_name(), rhost.full_name(), type(rhost).__name__,
                    type(u).__name__, u.full_name(), whost.full_name(), type(whost).__name__ )

            # 3. writer_host(x) is reader_host(x.y)'s parent:
            # Hence, writer is inport or wire, reader is inport
            elif whost == rhost._parent:
              assert  ( isinstance( u, InVPort ) or isinstance( u, Wire ) ) and \
                        isinstance( v, InVPort ), \
"""[Type 3] Invalid port type detected when the driver lies shallower than drivee:

- {} \"{}\" of {} (class {}) cannot be driven by {} \"{}\" of {} (class {}).

  Note: OutVPort/Wire x.y.z cannot be driven by x.a""" \
          .format(  type(v).__name__, v.full_name(), rhost.full_name(), type(rhost).__name__,
                    type(u).__name__, u.full_name(), whost.full_name(), type(whost).__name__ )

            # 4. hosts have the same parent: writer_host(x.y)/reader_host(x.z)
            # This means that the connection is fulfilled in x
            # Hence, writer is outport and reader is inport
            elif whost._parent == rhost._parent:
              assert isinstance( u, OutVPort ) and isinstance( v, InVPort ), \
"""[Type 4] Invalid port type detected when the drivers is the sibling of drivee:

- {} \"{}\" of {} (class {}) cannot be driven by {} \"{}\" of {} (class {}).

  Note: Looks like the connection is fulfilled in \"{}\".
        OutVPort/Wire x.y.z cannot be driven by x.a.b""" \
          .format(  type(v).__name__, v.full_name(), rhost.full_name(), type(rhost).__name__,
                    type(u).__name__, u.full_name(), whost.full_name(), type(whost).__name__,
                    whost._parent.full_name() )
            # 5. neither host is the other's parent nor the same.
            else:
              assert False, \
"""[Type 5] \"{}\" and \"{}\" cannot be connected:

- host objects \"{}\" and \"{}\" are too far in the hierarchy.""" \
          .format( u.full_name(), v.full_name(), whost.full_name(), rhost.full_name() )

  def compact_net_readers( self ):
    nets = self._nets

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
            if x != obj and _overlap(obj._slice, x._slice) and \
                id(obj) in all_reads:
              flag = True
              break

        if flag: new_readers.append( x ) # is read somewhere else

      nets[i] = (writer, new_readers)

  @staticmethod
  def print_nets( nets ):
    for n in nets:
      writer, readers = n
      print
      print "writer: \n + {}\nreader:\n - {}".format( writer.full_name(), "\n - ".join([ v.full_name() for v in readers ]) )
