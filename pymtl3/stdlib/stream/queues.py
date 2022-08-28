"""
-------------------------------------------------------------------------
Stream queue, stream pipeline queue, and stream bypass queue
-------------------------------------------------------------------------
Queues with stream interface.

Author : Yanghui Ou, Peitian Pan
  Date : Aug 26, 2022
"""


from pymtl3 import *
from pymtl3.stdlib.primitive import Mux, RegisterFile

from .ifcs import IStreamIfc, OStreamIfc

#-------------------------------------------------------------------------
# StreamNormalQueue1Entry
#-------------------------------------------------------------------------

class StreamNormalQueue1Entry( Component ):

  def construct( s, EntryType ):

    # Interface

    s.istream  = IStreamIfc( EntryType )
    s.ostream  = OStreamIfc( EntryType )
    s.count = OutPort()

    # Components

    s.full  = Wire()
    s.entry = Wire( EntryType )

    # Logic

    s.count //= s.full

    s.ostream.msg //= s.entry
    s.ostream.val //= s.full
    s.istream.rdy //= lambda: ~s.full

    @update_ff
    def ff_normal1():
      if s.reset:
        s.full <<= 0
      else:
        s.full <<= (s.istream.val & ~s.full) | (s.full & ~s.ostream.rdy)

      if s.istream.val & ~s.full:
        s.entry <<= s.istream.msg

  def line_trace( s ):
    return f"{s.istream}({s.full}){s.ostream}"

#-------------------------------------------------------------------------
# Dpath and Ctrl for StreamNormalQueue
#-------------------------------------------------------------------------

class StreamNormalQueueDpath( Component ):

  def construct( s, EntryType, num_entries=2 ):
    assert num_entries >= 2

    # Interface

    s.istream_msg = InPort( EntryType )
    s.ostream_msg = OutPort( EntryType )

    s.wen   = InPort()
    s.waddr = InPort( clog2( num_entries ) )
    s.raddr = InPort( clog2( num_entries ) )

    # Component

    s.rf = m = RegisterFile( EntryType, num_entries )
    m.raddr[0] //= s.raddr
    m.rdata[0] //= s.ostream_msg
    m.wen[0]   //= s.wen
    m.waddr[0] //= s.waddr
    m.wdata[0] //= s.istream_msg

class StreamNormalQueueCtrl( Component ):

  def construct( s, num_entries=2 ):
    assert num_entries >= 2

    # Constants

    addr_nbits  = clog2( num_entries   )
    count_nbits = clog2( num_entries+1 )

    # Interface

    s.istream_val = InPort()
    s.istream_rdy = OutPort()
    s.ostream_val = OutPort()
    s.ostream_rdy = InPort()

    s.count = OutPort( count_nbits )
    s.wen   = OutPort()
    s.waddr = OutPort( addr_nbits )
    s.raddr = OutPort( addr_nbits )

    # Registers

    s.head = Wire( addr_nbits )
    s.tail = Wire( addr_nbits )

    # Wires

    s.istream_xfer  = Wire()
    s.ostream_xfer  = Wire()

    # Connections

    s.wen   //= s.istream_xfer
    s.waddr //= s.tail
    s.raddr //= s.head

    s.istream_rdy  //= lambda: s.count < num_entries
    s.ostream_val  //= lambda: s.count > 0

    s.istream_xfer //= lambda: s.istream_val & s.istream_rdy
    s.ostream_xfer //= lambda: s.ostream_val & s.ostream_rdy

    @update_ff
    def up_reg():

      if s.reset:
        s.head  <<= 0
        s.tail  <<= 0
        s.count <<= 0

      else:
        if s.istream_xfer:
          s.tail <<= s.tail + 1 if ( s.tail < num_entries - 1 ) else 0

        if s.ostream_xfer:
          s.head <<= s.head + 1 if ( s.head < num_entries -1 ) else 0

        if s.istream_xfer & ~s.ostream_xfer:
          s.count <<= s.count + 1
        elif ~s.istream_xfer & s.ostream_xfer:
          s.count <<= s.count - 1

#-------------------------------------------------------------------------
# StreamNormalQueue
#-------------------------------------------------------------------------

class StreamNormalQueue( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.istream  = IStreamIfc( EntryType )
    s.ostream  = OStreamIfc( EntryType )
    s.count = OutPort( clog2( num_entries+1 ) )

    # Components

    assert num_entries > 0

    if num_entries == 1:
      s.q = StreamNormalQueue1Entry( EntryType )
      s.istream  //= s.q.istream
      s.ostream  //= s.q.ostream
      s.count //= s.q.count

    else:
      s.ctrl  = StreamNormalQueueCtrl ( num_entries )
      s.dpath = StreamNormalQueueDpath( EntryType, num_entries )

      # Connect ctrl to data path

      s.ctrl.wen   //= s.dpath.wen
      s.ctrl.waddr //= s.dpath.waddr
      s.ctrl.raddr //= s.dpath.raddr

      # Connect to interface

      s.istream.val //= s.ctrl.istream_val
      s.istream.rdy //= s.ctrl.istream_rdy
      s.istream.msg //= s.dpath.istream_msg

      s.ostream.val //= s.ctrl.ostream_val
      s.ostream.rdy //= s.ctrl.ostream_rdy
      s.ostream.msg //= s.dpath.ostream_msg
      s.count   //= s.ctrl.count

  # Line trace

  def line_trace( s ):
    return f"{s.istream}({s.count}){s.ostream}"

#-------------------------------------------------------------------------
# StreamPipeQueue1Entry
#-------------------------------------------------------------------------

class StreamPipeQueue1Entry( Component ):

  def construct( s, EntryType ):

    # Interface

    s.istream  = IStreamIfc( EntryType )
    s.ostream  = OStreamIfc( EntryType )
    s.count = OutPort()

    # Components

    s.full  = Wire()
    s.entry = Wire( EntryType )

    # Logic

    s.count //= s.full

    s.ostream.msg //= s.entry
    s.ostream.val //= s.full

    # If send is rdy, either the entry will be sent out to free up space
    # for recv, or entry is already available for send. Then if not full
    # entry can always buffer up a message. rdy path is elongated
    s.istream.rdy //= lambda: s.ostream.rdy | ~s.full

    @update_ff
    def ff_pipe1():
      if s.reset:
        s.full <<= 0
      else:
        # The pipe queue is full if in this cycle it cannot receive a
        # message due to back pressure and the entry is already full.
        # Otherwise it is not full and it becomes full only if there is
        # a valid incoming message.
        s.full <<= ~s.istream.rdy | s.istream.val

      # AND rdy and val to buffer the incoming message
      if s.istream.rdy & s.istream.val:
        s.entry <<= s.istream.msg

  def line_trace( s ):
    return f"{s.istream}({s.full}){s.ostream}"

#-------------------------------------------------------------------------
# Ctrl for StreamPipeQueue
#-------------------------------------------------------------------------

class StreamPipeQueueCtrl( Component ):

  def construct( s, num_entries=2 ):
    assert num_entries >= 2

    # Constants

    addr_nbits  = clog2( num_entries   )
    count_nbits = clog2( num_entries+1 )

    # Interface

    s.istream_val = InPort ()
    s.istream_rdy = OutPort()
    s.ostream_val = OutPort()
    s.ostream_rdy = InPort ()
    s.count    = OutPort( count_nbits )

    s.wen      = OutPort()
    s.waddr    = OutPort( addr_nbits )
    s.raddr    = OutPort( addr_nbits )

    # Registers

    s.head = Wire( addr_nbits )
    s.tail = Wire( addr_nbits )

    # Wires

    s.istream_xfer  = Wire()
    s.ostream_xfer  = Wire()

    # Connections

    s.wen   //= s.istream_xfer
    s.waddr //= s.tail
    s.raddr //= s.head

    s.ostream_val //= lambda: s.count > 0
    s.istream_rdy //= lambda: ( s.count < num_entries ) | s.ostream_rdy

    s.istream_xfer //= lambda: s.istream_val & s.istream_rdy
    s.ostream_xfer //= lambda: s.ostream_val & s.ostream_rdy

    @update_ff
    def up_reg():

      if s.reset:
        s.head  <<= 0
        s.tail  <<= 0
        s.count <<= 0

      else:
        if s.istream_xfer:
          s.tail <<= s.tail + 1 if ( s.tail < num_entries - 1 ) else 0

        if s.ostream_xfer:
          s.head <<= s.head + 1 if ( s.head < num_entries -1 ) else 0

        if s.istream_xfer & ~s.ostream_xfer:
          s.count <<= s.count + 1
        elif ~s.istream_xfer & s.ostream_xfer:
          s.count <<= s.count - 1

#-------------------------------------------------------------------------
# StreamPipeQueue
#-------------------------------------------------------------------------

class StreamPipeQueue( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.istream  = IStreamIfc( EntryType )
    s.ostream  = OStreamIfc( EntryType )
    s.count = OutPort( clog2( num_entries+1 ) )

    # Components

    assert num_entries > 0
    if num_entries == 1:
      s.q = StreamPipeQueue1Entry( EntryType )
      s.istream  //= s.q.istream
      s.ostream  //= s.q.ostream
      s.count //= s.q.count

    else:
      s.ctrl  = StreamPipeQueueCtrl ( num_entries )
      s.dpath = StreamNormalQueueDpath( EntryType, num_entries )

      # Connect ctrl to data path

      s.ctrl.wen   //= s.dpath.wen
      s.ctrl.waddr //= s.dpath.waddr
      s.ctrl.raddr //= s.dpath.raddr

      # Connect to interface

      s.istream.val //= s.ctrl.istream_val
      s.istream.rdy //= s.ctrl.istream_rdy
      s.ostream.val //= s.ctrl.ostream_val
      s.ostream.rdy //= s.ctrl.ostream_rdy
      s.count    //= s.ctrl.count
      s.istream.msg //= s.dpath.istream_msg
      s.ostream.msg //= s.dpath.ostream_msg

  # Line trace

  def line_trace( s ):
    return f"{s.istream}({s.count}){s.ostream}"

#-------------------------------------------------------------------------
# StreamBypassQueue1Entry
#-------------------------------------------------------------------------

class StreamBypassQueue1Entry( Component ):

  def construct( s, EntryType ):

    # Interface

    s.istream  = IStreamIfc( EntryType )
    s.ostream  = OStreamIfc( EntryType )
    s.count = OutPort()

    # Components

    s.full  = Wire()
    s.entry = Wire( EntryType )

    s.bypass_mux = m = Mux( EntryType, 2 )
    m.in_[0] //= s.istream.msg
    m.in_[1] //= s.entry
    m.out    //= s.ostream.msg
    m.sel    //= s.full

    # Logic

    s.count //= s.full

    s.ostream.val //= lambda: s.full | s.istream.val
    s.istream.rdy //= lambda: ~s.full

    @update_ff
    def ff_bypass1():
      if s.reset:
        s.full <<= 0
      else:
        s.full <<= ~s.ostream.rdy & (s.full | s.istream.val)

      # buffer the incoming message if we cannot directly send it out
      if ~s.ostream.rdy & ~s.full & s.istream.val:
        s.entry <<= s.istream.msg

  def line_trace( s ):
    return f"{s.istream}({s.full}){s.ostream}"

#-------------------------------------------------------------------------
# Ctrl and Dpath for StreamBypassQueue
#-------------------------------------------------------------------------

class StreamBypassQueueDpath( Component ):

  def construct( s, EntryType, num_entries=2 ):
    assert num_entries >= 2

    # Interface

    s.istream_msg = InPort( EntryType )
    s.ostream_msg = OutPort( EntryType )

    s.wen     = InPort()
    s.waddr   = InPort( clog2( num_entries ) )
    s.raddr   = InPort( clog2( num_entries ) )
    s.mux_sel = InPort()

    # Component

    s.rf = m = RegisterFile( EntryType, num_entries )
    m.raddr[0] //= s.raddr
    m.wen[0]   //= s.wen
    m.waddr[0] //= s.waddr
    m.wdata[0] //= s.istream_msg

    s.mux = m = Mux( EntryType, 2 )
    m.sel    //= s.mux_sel
    m.in_[0] //= s.rf.rdata[0]
    m.in_[1] //= s.istream_msg
    m.out    //= s.ostream_msg

class StreamBypassQueueCtrl( Component ):

  def construct( s, num_entries=2 ):
    assert num_entries >= 2

    # Constants

    addr_nbits  = clog2( num_entries   )
    count_nbits = clog2( num_entries+1 )

    last_idx = num_entries-1

    # Interface

    s.istream_val = InPort ()
    s.istream_rdy = OutPort()
    s.ostream_val = OutPort()
    s.ostream_rdy = InPort()
    s.count    = OutPort( count_nbits )

    s.wen     = OutPort()
    s.waddr   = OutPort( addr_nbits )
    s.raddr   = OutPort( addr_nbits )
    s.mux_sel = OutPort()

    # Registers

    s.head = Wire( addr_nbits )
    s.tail = Wire( addr_nbits )

    # Wires

    s.istream_xfer  = Wire()
    s.ostream_xfer  = Wire()

    # Connections

    s.wen   //= s.istream_xfer
    s.waddr //= s.tail
    s.raddr //= s.head

    s.istream_rdy //= lambda: s.count < num_entries
    s.ostream_val //= lambda: (s.count > 0) | s.istream_val

    s.mux_sel //= lambda: s.count == 0

    s.istream_xfer //= lambda: s.istream_val & s.istream_rdy
    s.ostream_xfer //= lambda: s.ostream_val & s.ostream_rdy

    @update_ff
    def up_reg():

      if s.reset:
        s.head  <<= 0
        s.tail  <<= 0
        s.count <<= 0

      else:
        if s.istream_xfer:
          s.tail <<= s.tail + 1 if ( s.tail < num_entries - 1 ) else 0

        if s.ostream_xfer:
          s.head <<= s.head + 1 if ( s.head < num_entries -1 ) else 0

        if s.istream_xfer & ~s.ostream_xfer:
          s.count <<= s.count + 1
        if ~s.istream_xfer & s.ostream_xfer:
          s.count <<= s.count - 1

#-------------------------------------------------------------------------
# StreamBypassQueue
#-------------------------------------------------------------------------

class StreamBypassQueue( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.istream  = IStreamIfc( EntryType )
    s.ostream  = OStreamIfc( EntryType )
    s.count = OutPort( clog2( num_entries+1 ) )

    # Components

    assert num_entries > 0
    if num_entries == 1:
      s.q = StreamBypassQueue1Entry( EntryType )
      s.istream  //= s.q.istream
      s.ostream  //= s.q.ostream
      s.count //= s.q.count

    else:
      s.ctrl  = StreamBypassQueueCtrl ( num_entries )
      s.dpath = StreamBypassQueueDpath( EntryType, num_entries )

      # Connect ctrl to data path

      s.ctrl.wen     //= s.dpath.wen
      s.ctrl.waddr   //= s.dpath.waddr
      s.ctrl.raddr   //= s.dpath.raddr
      s.ctrl.mux_sel //= s.dpath.mux_sel

      # Connect to interface

      s.istream.val //= s.ctrl.istream_val
      s.istream.rdy //= s.ctrl.istream_rdy
      s.ostream.val //= s.ctrl.ostream_val
      s.ostream.rdy //= s.ctrl.ostream_rdy
      s.count    //= s.ctrl.count
      s.istream.msg //= s.dpath.istream_msg
      s.ostream.msg //= s.dpath.ostream_msg

  # Line trace

  def line_trace( s ):
    return f"{s.istream}({s.count}){s.ostream}"
