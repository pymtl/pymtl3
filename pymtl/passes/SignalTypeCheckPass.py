#-------------------------------------------------------------------------
# SignalTypeCheckPass
#-------------------------------------------------------------------------

from pymtl import *
from pymtl.passes import BasePass

class SignalTypeCheckPass( BasePass ):

  def execute( self, m ):
    self.check_port_in_upblk( m )

  @staticmethod
  def check_port_in_upblk( m ):

    # Check read first
    for rd, blks in m._read_upblks.iteritems():
      obj = m._id_obj[ rd ]

      host = obj
      while not isinstance( host, UpdateWithVar ):
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
      while not isinstance( host, UpdateWithVar ):
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
