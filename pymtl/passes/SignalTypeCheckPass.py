#-------------------------------------------------------------------------
# SignalTypeCheckPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.components import UpdateVar, UpdateVarNet, Signal
from pymtl.passes import BasePass
from collections import deque
from errors import SignalTypeError, PassOrderError

class SignalTypeCheckPass( BasePass ):

  def execute( self, m ):

    if isinstance( m, UpdateVar ):
      if not hasattr( m, "_write_upblks" ):
        raise PassOrderError( "_write_upblk" )
      self.check_port_in_upblk( m )

    if isinstance( m, UpdateVarNet ):
      if not hasattr( m, "_nets" ):
        raise PassOrderError( "_nets" )
      self.check_port_in_nets( m )

    return m

  @staticmethod
  def check_port_in_upblk( m ):

    # Check read first
    for rd, blks in m._read_upblks.iteritems():
      obj = m._id_obj[ rd ]

      host = obj
      while not isinstance( host, UpdateVar ):
        host = host._parent # go to the component

      if   isinstance( obj, InVPort ):  pass
      elif isinstance( obj, OutVPort ): pass
      elif isinstance( obj, Wire ):
        for blkid in blks:
          blk = m._blkid_upblk[ blkid ]

          assert blk.hostobj == host, \
"""Invalid read to Wire:

- Wire \"{}\" of {} (class {}) is read in update block
       \"{}\" of {} (class {}).

  Note: Please only read Wire \"x.wire\" in x's update block.
        (Or did you intend to declare it as an OutVPort?)""" \
          .format(  repr(obj), repr(host), type(host).__name__,
                    blk.__name__, repr(blk.hostobj), type(blk.hostobj).__name__ )

    # Then check write

    for wr, blks in m._write_upblks.iteritems():
      obj = m._id_obj[ wr ]

      host = obj
      while not isinstance( host, UpdateVar ):
        host = host._parent # go to the component

      # A continuous assignment is implied when a variable is connected to
      # an input port declaration. This makes assignments to a variable
      # declared as an input port illegal. -- IEEE

      if   isinstance( obj, InVPort ):
        for blkid in blks:
          blk = m._blkid_upblk[ blkid ]

          assert host._parent == blk.hostobj, \
"""Invalid write to input port:

- InVPort \"{}\" of {} (class {}) is written in update block
          \"{}\" of {} (class {}).

  Note: Please only write to InVPort \"x.y.in\" in x's update block.""" \
          .format(  repr(obj), repr(host), type(host).__name__,
                    blk.__name__, repr(host), type(host).__name__ )

      # A continuous assignment is implied when a variable is connected to
      # the output port of an instance. This makes procedural or
      # continuous assignments to a variable connected to the output port
      # of an instance illegal. -- IEEE

      elif isinstance( obj, OutVPort ):
        for blkid in blks:
          blk = m._blkid_upblk[ blkid ]

          assert blk.hostobj == host, \
"""Invalid write to output port:

- OutVPort \"{}\" of {} (class {}) is written in update block
           \"{}\" of {} (class {}).

  Note: Please only write to OutVPort \"x.out\" in x's update block.""" \
          .format(  repr(obj), repr(host), type(host).__name__,
                    blk.__name__, repr(blk.hostobj), type(blk.hostobj).__name__, )

      # The case of wire is special. We only allow Wire to be written in
      # the same object. One cannot write this from outside

      elif isinstance( obj, Wire ):
        for blkid in blks:
          blk = m._blkid_upblk[ blkid ]

          assert blk.hostobj == host, \
"""Invalid write to Wire:

- Wire \"{}\" of {} (class {}) is written in update block
       \"{}\" of {} (class {}).

  Note: Please only write to Wire \"x.wire\" in x's update block.
        (Or did you intend to declare it as an InVPort?)""" \
          .format(  repr(obj), repr(host), type(host).__name__,
                    blk.__name__, repr(blk.hostobj), type(blk.hostobj).__name__ )

  @staticmethod
  def check_port_in_nets( m ):
    nets = m._nets

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
          .format(  repr(rhost), type(rhost).__name__,
                    type(v).__name__, repr(v), type(u).__name__, repr(u) )

            # 2. reader_host(x) is writer_host(x.y)'s parent:
            # Hence, writer is outport, reader is wire or outport
            elif rhost == whost._parent:
              assert  isinstance( u, OutVPort) and \
                    ( isinstance( v, OutVPort ) or isinstance( v, Wire ) ), \
"""[Type 2] Invalid port type detected when the driver lies deeper than drivee:

- {} \"{}\" of {} (class {}) cannot be driven by {} \"{}\" of {} (class {}).

  Note: InVPort x.y cannot be driven by x.z.a""" \
          .format(  type(v).__name__, repr(v), repr(rhost), type(rhost).__name__,
                    type(u).__name__, repr(u), repr(whost), type(whost).__name__ )

            # 3. writer_host(x) is reader_host(x.y)'s parent:
            # Hence, writer is inport or wire, reader is inport
            elif whost == rhost._parent:
              assert  ( isinstance( u, InVPort ) or isinstance( u, Wire ) ) and \
                        isinstance( v, InVPort ), \
"""[Type 3] Invalid port type detected when the driver lies shallower than drivee:

- {} \"{}\" of {} (class {}) cannot be driven by {} \"{}\" of {} (class {}).

  Note: OutVPort/Wire x.y.z cannot be driven by x.a""" \
          .format(  type(v).__name__, repr(v), repr(rhost), type(rhost).__name__,
                    type(u).__name__, repr(u), repr(whost), type(whost).__name__ )

            # 4. hosts have the same parent: writer_host(x.y)/reader_host(x.z)
            # This means that the connection is fulfilled in x
            # Hence, writer is outport and reader is inport
            elif whost._parent == rhost._parent:
              assert isinstance( u, OutVPort ) and isinstance( v, InVPort ), \
"""[Type 4] Invalid port type detected when the drivers is the sibling of drivee:

- {} \"{}\" of {} (class {}) cannot be driven by {} \"{}\" of {} (class {}).

  Note: Looks like the connection is fulfilled in \"{}\".
        OutVPort/Wire x.y.z cannot be driven by x.a.b""" \
          .format(  type(v).__name__, repr(v), repr(rhost), type(rhost).__name__,
                    type(u).__name__, repr(u), repr(whost), type(whost).__name__,
                    repr(whost._parent) )
            # 5. neither host is the other's parent nor the same.
            else:
              assert False, \
"""[Type 5] \"{}\" and \"{}\" cannot be connected:

- host objects \"{}\" and \"{}\" are too far in the hierarchy.""" \
          .format( repr(u), repr(v), repr(whost), repr(rhost) )
