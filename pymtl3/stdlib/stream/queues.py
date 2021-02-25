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
# Dpath and Ctrl for NormalQueueRTL
#-------------------------------------------------------------------------

class NormalQueueDpathRTL( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.recv_msg = InPort( EntryType )
    s.send_msg = OutPort( EntryType )

    s.wen   = InPort()
    s.waddr = InPort( max( 1, clog2( num_entries ) ) )
    s.raddr = InPort( max( 1, clog2( num_entries ) ) )

    # Component

    s.rf = m = RegisterFile( EntryType, num_entries )
    m.raddr[0] //= s.raddr
    m.rdata[0] //= s.send_msg
    m.wen[0]   //= s.wen
    m.waddr[0] //= s.waddr
    m.wdata[0] //= s.recv_msg

class NormalQueueCtrlRTL( Component ):

  def construct( s, num_entries=2 ):

    # Constants

    addr_nbits    = max( 1, clog2( num_entries   ) )
    count_nbits   = max( 1, clog2( num_entries+1 ) )
    PtrType       = mk_bits  ( addr_nbits    )
    CountType     = mk_bits  ( count_nbits   )
    s.last_idx    = PtrType  ( num_entries-1 )
    s.num_entries = CountType( num_entries   )

    # Interface

    s.recv_val = InPort()
    s.recv_rdy = OutPort()
    s.send_val = OutPort()
    s.send_rdy = InPort()

    s.count = OutPort( CountType )
    s.wen   = OutPort()
    s.waddr = OutPort( PtrType )
    s.raddr = OutPort( PtrType )

    # Registers

    s.head = Wire( PtrType )
    s.tail = Wire( PtrType )

    # Wires

    s.recv_xfer  = Wire()
    s.send_xfer  = Wire()

    # Connections

    s.wen   //= s.recv_xfer
    s.waddr //= s.tail
    s.raddr //= s.head

    s.recv_rdy  //= lambda: s.count < s.num_entries
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
          s.tail <<= s.tail + 1 if s.tail < s.last_idx else 0

        if s.send_xfer:
          s.head <<= s.head + 1 if s.head < s.last_idx else 0

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
    s.count = OutPort( mk_bits( clog2( num_entries+1 ) ) )

    # Components

    assert num_entries > 0
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

    s.entry = Wire( EntryType )
    s.full  = Wire()

    # Logic

    s.count //= s.full

    s.send.msg //= s.entry

    s.enq.rdy //= lambda: ~s.reset & ( ~s.full | s.deq.en )
    s.deq.rdy //= lambda: s.full & ~s.reset

    @update_ff
    def ff_pipe1():
      if s.reset:
        s.full <<= 0
        s.recv.rdy <<= 0

      else:
        s.full <<= ( s.enq.en | s.full & ~s.deq.en )

      if s.enq.en:
        s.entry <<= s.enq.msg

  def line_trace( s ):
    return f"{s.enq}({s.full}){s.deq}"

#-------------------------------------------------------------------------
# Ctrl for PipeQueue
#-------------------------------------------------------------------------

class PipeQueueCtrlRTL( Component ):

  def construct( s, num_entries=2 ):

    # Constants

    addr_nbits    = clog2    ( num_entries   )
    count_nbits   = clog2    ( num_entries+1 )
    PtrType       = mk_bits  ( addr_nbits    )
    CountType     = mk_bits  ( count_nbits   )
    s.last_idx    = PtrType  ( num_entries-1 )
    s.num_entries = CountType( num_entries   )

    # Interface

    s.enq_en  = InPort ( Bits1     )
    s.enq_rdy = OutPort( Bits1     )
    s.deq_en  = InPort ( Bits1     )
    s.deq_rdy = OutPort( Bits1     )
    s.count   = OutPort( CountType )

    s.wen     = OutPort( Bits1   )
    s.waddr   = OutPort( PtrType )
    s.raddr   = OutPort( PtrType )

    # Registers

    s.head = Wire( PtrType )
    s.tail = Wire( PtrType )

    # Wires

    s.enq_xfer  = Wire( Bits1   )
    s.deq_xfer  = Wire( Bits1   )

    # Connections

    connect( s.wen,   s.enq_xfer )
    connect( s.waddr, s.tail     )
    connect( s.raddr, s.head     )

    s.deq_rdy //= lambda: ~s.reset & ( s.count > CountType(0) )
    s.enq_rdy //= lambda: ~s.reset & ( ( s.count < s.num_entries ) | s.deq_en )

    s.enq_xfer //= lambda: s.enq_en & s.enq_rdy
    s.deq_xfer //= lambda: s.deq_en & s.deq_rdy

    @update_ff
    def up_reg():

      if s.reset:
        s.head  <<= PtrType(0)
        s.tail  <<= PtrType(0)
        s.count <<= CountType(0)

      else:
        if s.deq_xfer:
          s.head <<= s.head + PtrType(1) if s.head < s.last_idx else PtrType(0)

        if s.enq_xfer:
          s.tail <<= s.tail + PtrType(1) if s.tail < s.last_idx else PtrType(0)

        if s.enq_xfer & ~s.deq_xfer:
          s.count <<= s.count + CountType(1)
        if ~s.enq_xfer & s.deq_xfer:
          s.count <<= s.count - CountType(1)

#-------------------------------------------------------------------------
# PipeQueueRTL
#-------------------------------------------------------------------------

class PipeQueueRTL( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.recv  = RecvIfcRTL( EntryType )
    s.send  = SendIfcRTL( EntryType )
    s.count = OutPort( mk_bits( clog2( num_entries+1 ) ) )

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
    return "{}({}){}".format( s.enq, s.count, s.deq )

#-------------------------------------------------------------------------
# Ctrl and Dpath for BypassQueue
#-------------------------------------------------------------------------

class BypassQueueDpathRTL( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.enq_msg = InPort( EntryType )
    s.deq_ret = OutPort( EntryType )

    s.wen     = InPort( Bits1 )
    s.waddr   = InPort( mk_bits( clog2( num_entries ) ) )
    s.raddr   = InPort( mk_bits( clog2( num_entries ) ) )
    s.mux_sel = InPort( Bits1 )

    # Component

    s.queue = m = RegisterFile( EntryType, num_entries )
    m.raddr[0] //= s.raddr
    m.wen[0]   //= s.wen
    m.waddr[0] //= s.waddr
    m.wdata[0] //= s.enq_msg

    s.mux = m = Mux( EntryType, 2 )
    m.sel    //= s.mux_sel
    m.in_[0] //= s.queue.rdata[0]
    m.in_[1] //= s.enq_msg
    m.out    //= s.deq_ret

class BypassQueueCtrlRTL( Component ):

  def construct( s, num_entries=2 ):

    # Constants

    addr_nbits    = clog2    ( num_entries   )
    count_nbits   = clog2    ( num_entries+1 )
    PtrType       = mk_bits  ( addr_nbits    )
    CountType     = mk_bits  ( count_nbits   )
    s.last_idx    = PtrType  ( num_entries-1 )
    s.num_entries = CountType( num_entries   )

    # Interface

    s.enq_en  = InPort ( Bits1     )
    s.enq_rdy = OutPort( Bits1     )
    s.deq_en  = InPort ( Bits1     )
    s.deq_rdy = OutPort( Bits1     )
    s.count   = OutPort( CountType )

    s.wen     = OutPort( Bits1   )
    s.waddr   = OutPort( PtrType )
    s.raddr   = OutPort( PtrType )
    s.mux_sel = OutPort( Bits1   )

    # Registers

    s.head = Wire( PtrType )
    s.tail = Wire( PtrType )

    # Wires

    s.enq_xfer  = Wire( Bits1   )
    s.deq_xfer  = Wire( Bits1   )

    # Connections

    connect( s.wen,   s.enq_xfer )
    connect( s.waddr, s.tail     )
    connect( s.raddr, s.head     )

    s.enq_rdy //= lambda: ~s.reset & ( s.count < s.num_entries )
    s.deq_rdy //= lambda: ~s.reset & ( (s.count > CountType(0) ) | s.enq_en )

    s.mux_sel //= lambda: s.count == CountType(0)

    s.enq_xfer //= lambda: s.enq_en & s.enq_rdy
    s.deq_xfer //= lambda: s.deq_en & s.deq_rdy

    @update_ff
    def up_reg():

      if s.reset:
        s.head  <<= PtrType(0)
        s.tail  <<= PtrType(0)
        s.count <<= CountType(0)

      else:
        if s.deq_xfer:
          s.head <<= s.head + PtrType(1) if s.head < s.last_idx else PtrType(0)

        if s.enq_xfer:
          s.tail <<= s.tail + PtrType(1) if s.tail < s.last_idx else PtrType(0)

        if s.enq_xfer & ~s.deq_xfer:
          s.count <<= s.count + CountType(1)
        if ~s.enq_xfer & s.deq_xfer:
          s.count <<= s.count - CountType(1)

#-------------------------------------------------------------------------
# BypassQueueRTL
#-------------------------------------------------------------------------

class BypassQueueRTL( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.enq   = RecvIfcRTL( EntryType )
    s.deq   = SendIfcRTL( EntryType )
    s.count = OutPort( mk_bits( clog2( num_entries+1 ) ) )

    # Components

    assert num_entries > 0
    if num_entries == 1:
      s.q = BypassQueue1EntryRTL( EntryType )
      connect( s.enq,   s.q.enq )
      connect( s.deq,   s.q.deq )
      connect( s.count, s.q.count )

    else:
      s.ctrl  = BypassQueueCtrlRTL ( num_entries )
      s.dpath = BypassQueueDpathRTL( EntryType, num_entries )

      # Connect ctrl to data path

      connect( s.ctrl.wen,     s.dpath.wen     )
      connect( s.ctrl.waddr,   s.dpath.waddr   )
      connect( s.ctrl.raddr,   s.dpath.raddr   )
      connect( s.ctrl.mux_sel, s.dpath.mux_sel )

      # Connect to interface

      connect( s.enq.en,  s.ctrl.enq_en   )
      connect( s.enq.rdy, s.ctrl.enq_rdy  )
      connect( s.deq.en,  s.ctrl.deq_en   )
      connect( s.deq.rdy, s.ctrl.deq_rdy  )
      connect( s.count,   s.ctrl.count    )
      connect( s.enq.msg, s.dpath.enq_msg )
      connect( s.deq.ret, s.dpath.deq_ret )

  # Line trace

  def line_trace( s ):
    return f"{s.enq}({s.count}){s.deq}"

