"""
-------------------------------------------------------------------------
Library of RTL queues
-------------------------------------------------------------------------

Author : Yanghui Ou
  Date : Feb 22, 2021
"""


from pymtl3 import *
from pymtl3.stdlib.basic_rtl import Mux, RegisterFile

from .ifcs import RecvIfcRTL, SendIfcRTL

#-------------------------------------------------------------------------
# NormalQueue1EntryRTL
#-------------------------------------------------------------------------

class NormalQueue1EntryRTL( Component ):

  def construct( s, EntryType ):

    # Interface

    s.recv  = RecvIfcRTL( EntryType )
    s.send  = SendIfcRTL( EntryType )
    s.count = OutPort()

    # Components

    s.full  = Wire()
    s.entry = Wire( EntryType )

    # Logic

    s.count //= s.full

    s.send.msg //= s.entry
    s.send.val //= s.full
    s.recv.rdy //= lambda: ~s.full

    @update_ff
    def ff_normal1():
      if s.reset:
        s.full <<= 0
      else:
        s.full <<= (s.recv.val & ~s.full) | (s.full & ~s.send.rdy)

      if s.recv.val & ~s.full:
        s.entry <<= s.recv.msg

  def line_trace( s ):
    return f"{s.recv}({s.full}){s.send}"

#-------------------------------------------------------------------------
# Dpath and Ctrl for NormalQueueRTL
#-------------------------------------------------------------------------

class NormalQueueDpathRTL( Component ):

  def construct( s, EntryType, num_entries=2 ):
    assert num_entries >= 2

    # Interface

    s.recv_msg = InPort( EntryType )
    s.send_msg = OutPort( EntryType )

    s.wen   = InPort()
    s.waddr = InPort( clog2( num_entries ) )
    s.raddr = InPort( clog2( num_entries ) )

    # Component

    s.rf = m = RegisterFile( EntryType, num_entries )
    m.raddr[0] //= s.raddr
    m.rdata[0] //= s.send_msg
    m.wen[0]   //= s.wen
    m.waddr[0] //= s.waddr
    m.wdata[0] //= s.recv_msg

class NormalQueueCtrlRTL( Component ):

  def construct( s, num_entries=2 ):
    assert num_entries >= 2

    # Constants

    addr_nbits  = clog2( num_entries   )
    count_nbits = clog2( num_entries+1 )

    # Interface

    s.recv_val = InPort()
    s.recv_rdy = OutPort()
    s.send_val = OutPort()
    s.send_rdy = InPort()

    s.count = OutPort( count_nbits )
    s.wen   = OutPort()
    s.waddr = OutPort( addr_nbits )
    s.raddr = OutPort( addr_nbits )

    # Registers

    s.head = Wire( addr_nbits )
    s.tail = Wire( addr_nbits )

    # Wires

    s.recv_xfer  = Wire()
    s.send_xfer  = Wire()

    # Connections

    s.wen   //= s.recv_xfer
    s.waddr //= s.tail
    s.raddr //= s.head

    s.recv_rdy  //= lambda: s.count < num_entries
    s.send_val  //= lambda: s.count > 0

    s.recv_xfer //= lambda: s.recv_val & s.recv_rdy
    s.send_xfer //= lambda: s.send_val & s.send_rdy

    @update_ff
    def up_reg():

      if s.reset:
        s.head  <<= 0
        s.tail  <<= 0
        s.count <<= 0

      else:
        if s.recv_xfer:
          s.tail <<= s.tail + 1 if ( s.tail < num_entries - 1 ) else 0

        if s.send_xfer:
          s.head <<= s.head + 1 if ( s.head < num_entries -1 ) else 0

        if s.recv_xfer & ~s.send_xfer:
          s.count <<= s.count + 1
        elif ~s.recv_xfer & s.send_xfer:
          s.count <<= s.count - 1

#-------------------------------------------------------------------------
# NormalQueueRTL
#-------------------------------------------------------------------------

class NormalQueueRTL( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.recv  = RecvIfcRTL( EntryType )
    s.send  = SendIfcRTL( EntryType )
    s.count = OutPort( clog2( num_entries+1 ) )

    # Components

    assert num_entries > 0

    if num_entries == 1:
      s.q = NormalQueue1EntryRTL( EntryType )
      s.recv  //= s.q.recv
      s.send  //= s.q.send
      s.count //= s.q.count

    else:
      s.ctrl  = NormalQueueCtrlRTL ( num_entries )
      s.dpath = NormalQueueDpathRTL( EntryType, num_entries )

      # Connect ctrl to data path

      s.ctrl.wen   //= s.dpath.wen
      s.ctrl.waddr //= s.dpath.waddr
      s.ctrl.raddr //= s.dpath.raddr

      # Connect to interface

      s.recv.val //= s.ctrl.recv_val
      s.recv.rdy //= s.ctrl.recv_rdy
      s.recv.msg //= s.dpath.recv_msg

      s.send.val //= s.ctrl.send_val
      s.send.rdy //= s.ctrl.send_rdy
      s.send.msg //= s.dpath.send_msg
      s.count   //= s.ctrl.count

  # Line trace

  def line_trace( s ):
    return f"{s.recv}({s.count}){s.send}"

#-------------------------------------------------------------------------
# PipeQueue1EntryRTL
#-------------------------------------------------------------------------

class PipeQueue1EntryRTL( Component ):

  def construct( s, EntryType ):

    # Interface

    s.recv  = RecvIfcRTL( EntryType )
    s.send  = SendIfcRTL( EntryType )
    s.count = OutPort()

    # Components

    s.full  = Wire()
    s.entry = Wire( EntryType )

    # Logic

    s.count //= s.full

    s.send.msg //= s.entry
    s.send.val //= s.full

    # If send is rdy, either the entry will be sent out to free up space
    # for recv, or entry is already available for send. Then if not full
    # entry can always buffer up a message. rdy path is elongated
    s.recv.rdy //= lambda: s.send.rdy | ~s.full

    @update_ff
    def ff_pipe1():
      if s.reset:
        s.full <<= 0
      else:
        # The pipe queue is full if in this cycle it cannot receive a
        # message due to back pressure and the entry is already full.
        # Otherwise it is not full and it becomes full only if there is
        # a valid incoming message.
        s.full <<= ~s.recv.rdy | s.recv.val

      # AND rdy and val to buffer the incoming message
      if s.recv.rdy & s.recv.val:
        s.entry <<= s.recv.msg

  def line_trace( s ):
    return f"{s.recv}({s.full}){s.send}"

#-------------------------------------------------------------------------
# Ctrl for PipeQueue
#-------------------------------------------------------------------------

class PipeQueueCtrlRTL( Component ):

  def construct( s, num_entries=2 ):
    assert num_entries >= 2

    # Constants

    addr_nbits  = clog2( num_entries   )
    count_nbits = clog2( num_entries+1 )

    # Interface

    s.recv_val = InPort ()
    s.recv_rdy = OutPort()
    s.send_val = OutPort()
    s.send_rdy = InPort ()
    s.count    = OutPort( count_nbits )

    s.wen      = OutPort()
    s.waddr    = OutPort( addr_nbits )
    s.raddr    = OutPort( addr_nbits )

    # Registers

    s.head = Wire( addr_nbits )
    s.tail = Wire( addr_nbits )

    # Wires

    s.recv_xfer  = Wire()
    s.send_xfer  = Wire()

    # Connections

    s.wen   //= s.recv_xfer
    s.waddr //= s.tail
    s.raddr //= s.head

    s.send_val //= lambda: s.count > 0
    s.recv_rdy //= lambda: ( s.count < num_entries ) | s.send_rdy

    s.recv_xfer //= lambda: s.recv_val & s.recv_rdy
    s.send_xfer //= lambda: s.send_val & s.send_rdy

    @update_ff
    def up_reg():

      if s.reset:
        s.head  <<= 0
        s.tail  <<= 0
        s.count <<= 0

      else:
        if s.recv_xfer:
          s.tail <<= s.tail + 1 if ( s.tail < num_entries - 1 ) else 0

        if s.send_xfer:
          s.head <<= s.head + 1 if ( s.head < num_entries -1 ) else 0

        if s.recv_xfer & ~s.send_xfer:
          s.count <<= s.count + 1
        elif ~s.recv_xfer & s.send_xfer:
          s.count <<= s.count - 1

#-------------------------------------------------------------------------
# PipeQueueRTL
#-------------------------------------------------------------------------

class PipeQueueRTL( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.recv  = RecvIfcRTL( EntryType )
    s.send  = SendIfcRTL( EntryType )
    s.count = OutPort( clog2( num_entries+1 ) )

    # Components

    assert num_entries > 0
    if num_entries == 1:
      s.q = PipeQueue1EntryRTL( EntryType )
      s.recv  //= s.q.recv
      s.send  //= s.q.send
      s.count //= s.q.count

    else:
      s.ctrl  = PipeQueueCtrlRTL ( num_entries )
      s.dpath = NormalQueueDpathRTL( EntryType, num_entries )

      # Connect ctrl to data path

      s.ctrl.wen   //= s.dpath.wen
      s.ctrl.waddr //= s.dpath.waddr
      s.ctrl.raddr //= s.dpath.raddr

      # Connect to interface

      s.recv.val //= s.ctrl.recv_val
      s.recv.rdy //= s.ctrl.recv_rdy
      s.send.val //= s.ctrl.send_val
      s.send.rdy //= s.ctrl.send_rdy
      s.count    //= s.ctrl.count
      s.recv.msg //= s.dpath.recv_msg
      s.send.msg //= s.dpath.send_msg

  # Line trace

  def line_trace( s ):
    return f"{s.recv}({s.count}){s.send}"

#-------------------------------------------------------------------------
# BypassQueue1EntryRTL
#-------------------------------------------------------------------------

class BypassQueue1EntryRTL( Component ):

  def construct( s, EntryType ):

    # Interface

    s.recv  = RecvIfcRTL( EntryType )
    s.send  = SendIfcRTL( EntryType )
    s.count = OutPort()

    # Components

    s.full  = Wire()
    s.entry = Wire( EntryType )

    s.bypass_mux = m = Mux( EntryType, 2 )
    m.in_[0] //= s.recv.msg
    m.in_[1] //= s.entry
    m.out    //= s.send.msg
    m.sel    //= s.full

    # Logic

    s.count //= s.full

    s.send.val //= lambda: s.full | s.recv.val
    s.recv.rdy //= lambda: ~s.full

    @update_ff
    def ff_bypass1():
      if s.reset:
        s.full <<= 0
      else:
        s.full <<= ~s.send.rdy & (s.full | s.recv.val)

      # buffer the incoming message if we cannot directly send it out
      if ~s.send.rdy & ~s.full & s.recv.val:
        s.entry <<= s.recv.msg

  def line_trace( s ):
    return f"{s.recv}({s.full}){s.send}"
#-------------------------------------------------------------------------
# Ctrl and Dpath for BypassQueue
#-------------------------------------------------------------------------

class BypassQueueDpathRTL( Component ):

  def construct( s, EntryType, num_entries=2 ):
    assert num_entries >= 2

    # Interface

    s.recv_msg = InPort( EntryType )
    s.send_msg = OutPort( EntryType )

    s.wen     = InPort()
    s.waddr   = InPort( clog2( num_entries ) )
    s.raddr   = InPort( clog2( num_entries ) )
    s.mux_sel = InPort()

    # Component

    s.rf = m = RegisterFile( EntryType, num_entries )
    m.raddr[0] //= s.raddr
    m.wen[0]   //= s.wen
    m.waddr[0] //= s.waddr
    m.wdata[0] //= s.recv_msg

    s.mux = m = Mux( EntryType, 2 )
    m.sel    //= s.mux_sel
    m.in_[0] //= s.rf.rdata[0]
    m.in_[1] //= s.recv_msg
    m.out    //= s.send_msg

class BypassQueueCtrlRTL( Component ):

  def construct( s, num_entries=2 ):
    assert num_entries >= 2

    # Constants

    addr_nbits  = clog2( num_entries   )
    count_nbits = clog2( num_entries+1 )

    last_idx = num_entries-1

    # Interface

    s.recv_val = InPort ()
    s.recv_rdy = OutPort()
    s.send_val = OutPort()
    s.send_rdy = InPort()
    s.count    = OutPort( count_nbits )

    s.wen     = OutPort()
    s.waddr   = OutPort( addr_nbits )
    s.raddr   = OutPort( addr_nbits )
    s.mux_sel = OutPort()

    # Registers

    s.head = Wire( addr_nbits )
    s.tail = Wire( addr_nbits )

    # Wires

    s.recv_xfer  = Wire()
    s.send_xfer  = Wire()

    # Connections

    s.wen   //= s.recv_xfer
    s.waddr //= s.tail
    s.raddr //= s.head

    s.recv_rdy //= lambda: s.count < num_entries
    s.send_val //= lambda: (s.count > 0) | s.recv_val

    s.mux_sel //= lambda: s.count == 0

    s.recv_xfer //= lambda: s.recv_val & s.recv_rdy
    s.send_xfer //= lambda: s.send_val & s.send_rdy

    @update_ff
    def up_reg():

      if s.reset:
        s.head  <<= 0
        s.tail  <<= 0
        s.count <<= 0

      else:
        if s.recv_xfer:
          s.tail <<= s.tail + 1 if ( s.tail < num_entries - 1 ) else 0

        if s.send_xfer:
          s.head <<= s.head + 1 if ( s.head < num_entries -1 ) else 0

        if s.recv_xfer & ~s.send_xfer:
          s.count <<= s.count + 1
        if ~s.recv_xfer & s.send_xfer:
          s.count <<= s.count - 1

#-------------------------------------------------------------------------
# BypassQueueRTL
#-------------------------------------------------------------------------

class BypassQueueRTL( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.recv  = RecvIfcRTL( EntryType )
    s.send  = SendIfcRTL( EntryType )
    s.count = OutPort( clog2( num_entries+1 ) )

    # Components

    assert num_entries > 0
    if num_entries == 1:
      s.q = BypassQueue1EntryRTL( EntryType )
      s.recv  //= s.q.recv
      s.send  //= s.q.send
      s.count //= s.q.count

    else:
      s.ctrl  = BypassQueueCtrlRTL ( num_entries )
      s.dpath = BypassQueueDpathRTL( EntryType, num_entries )

      # Connect ctrl to data path

      s.ctrl.wen     //= s.dpath.wen
      s.ctrl.waddr   //= s.dpath.waddr
      s.ctrl.raddr   //= s.dpath.raddr
      s.ctrl.mux_sel //= s.dpath.mux_sel

      # Connect to interface

      s.recv.val //= s.ctrl.recv_val
      s.recv.rdy //= s.ctrl.recv_rdy
      s.send.val //= s.ctrl.send_val
      s.send.rdy //= s.ctrl.send_rdy
      s.count    //= s.ctrl.count
      s.recv.msg //= s.dpath.recv_msg
      s.send.msg //= s.dpath.send_msg

  # Line trace

  def line_trace( s ):
    return f"{s.recv}({s.count}){s.send}"

