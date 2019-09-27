"""
-------------------------------------------------------------------------
Library of RTL queues
-------------------------------------------------------------------------

Author : Yanghui Ou
  Date : Mar 23, 2019
"""


from pymtl3 import *
from pymtl3.stdlib.ifcs import DeqIfcRTL, EnqIfcRTL
from pymtl3.stdlib.rtl import Mux, RegisterFile

#-------------------------------------------------------------------------
# Dpath and Ctrl for NormalQueueRTL
#-------------------------------------------------------------------------

class NormalQueueDpathRTL( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.enq_msg =  InPort( EntryType )
    s.deq_msg = OutPort( EntryType )

    s.wen   = InPort( Bits1 )
    s.waddr = InPort( mk_bits( clog2( num_entries ) ) )
    s.raddr = InPort( mk_bits( clog2( num_entries ) ) )

    # Component

    s.queue = RegisterFile( EntryType, num_entries )(
      raddr = { 0: s.raddr   },
      rdata = { 0: s.deq_msg },
      wen   = { 0: s.wen     },
      waddr = { 0: s.waddr   },
      wdata = { 0: s.enq_msg },
    )

class NormalQueueCtrlRTL( Component ):

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
    s.head_next = Wire( PtrType )
    s.tail_next = Wire( PtrType )

    # Connections

    connect( s.wen,   s.enq_xfer )
    connect( s.waddr, s.tail     )
    connect( s.raddr, s.head     )

    @s.update
    def up_rdy_signals():
        s.enq_rdy = ( s.count < s.num_entries ) & ~s.reset
        s.deq_rdy = ( s.count > CountType(0) ) & ~s.reset

    @s.update
    def up_xfer_signals():
      s.enq_xfer = s.enq_en & s.enq_rdy
      s.deq_xfer = s.deq_en & s.deq_rdy

    @s.update
    def up_next():
      s.head_next = s.head + PtrType(1) if s.head < s.last_idx else PtrType(0)
      s.tail_next = s.tail + PtrType(1) if s.tail < s.last_idx else PtrType(0)

    @s.update_ff
    def up_reg():

      if s.reset:
        s.head  <<= PtrType(0)
        s.tail  <<= PtrType(0)
        s.count <<= CountType(0)

      else:
        s.head  <<= s.head_next if s.deq_xfer else s.head
        s.tail  <<= s.tail_next if s.enq_xfer else s.tail
        s.count <<= s.count + CountType(1) if s.enq_xfer & ~s.deq_xfer else \
                    s.count - CountType(1) if s.deq_xfer & ~s.enq_xfer else \
                    s.count

#-------------------------------------------------------------------------
# NormalQueueRTL
#-------------------------------------------------------------------------

class NormalQueueRTL( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.enq   = EnqIfcRTL( EntryType )
    s.deq   = DeqIfcRTL( EntryType )
    s.count = OutPort( mk_bits( clog2( num_entries+1 ) ) )

    # Components

    assert num_entries > 0
    if num_entries == 1:
      s.q = NormalQueue1EntryRTL( EntryType )
      connect( s.enq,   s.q.enq )
      connect( s.deq,   s.q.deq )
      connect( s.count, s.q.count )

    else:
      s.ctrl  = NormalQueueCtrlRTL ( num_entries )
      s.dpath = NormalQueueDpathRTL( EntryType, num_entries )

      # Connect ctrl to data path

      connect( s.ctrl.wen,     s.dpath.wen     )
      connect( s.ctrl.waddr,   s.dpath.waddr   )
      connect( s.ctrl.raddr,   s.dpath.raddr   )

      # Connect to interface

      connect( s.enq.en,  s.ctrl.enq_en   )
      connect( s.enq.rdy, s.ctrl.enq_rdy  )
      connect( s.deq.en,  s.ctrl.deq_en   )
      connect( s.deq.rdy, s.ctrl.deq_rdy  )
      connect( s.count,   s.ctrl.count    )
      connect( s.enq.msg, s.dpath.enq_msg )
      connect( s.deq.msg, s.dpath.deq_msg )

  # Line trace

  def line_trace( s ):
    return "{}({}){}".format( s.enq, s.count, s.deq )

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
    s.head_next = Wire( PtrType )
    s.tail_next = Wire( PtrType )

    # Connections

    connect( s.wen,   s.enq_xfer )
    connect( s.waddr, s.tail     )
    connect( s.raddr, s.head     )

    @s.update
    def up_rdy_signals():
      s.deq_rdy = ( s.count > CountType(0) ) & ~s.reset

    @s.update
    def up_enq_rdy():
      if s.reset:
        s.enq_rdy = b1(0)
      else:
        s.enq_rdy = ( s.count < s.num_entries ) | s.deq_en


    @s.update
    def up_xfer_signals():
      s.enq_xfer  = s.enq_en & s.enq_rdy
      s.deq_xfer  = s.deq_en & s.deq_rdy

    @s.update
    def up_next():
      s.head_next = s.head + PtrType(1) if s.head < s.last_idx else PtrType(0)
      s.tail_next = s.tail + PtrType(1) if s.tail < s.last_idx else PtrType(0)

    @s.update_ff
    def up_reg():

      if s.reset:
        s.head  <<= PtrType(0)
        s.tail  <<= PtrType(0)
        s.count <<= CountType(0)

      else:
        s.head  <<= s.head_next if s.deq_xfer else s.head
        s.tail  <<= s.tail_next if s.enq_xfer else s.tail
        s.count <<= s.count + CountType(1) if s.enq_xfer & ~s.deq_xfer else \
                    s.count - CountType(1) if s.deq_xfer & ~s.enq_xfer else \
                    s.count

#-------------------------------------------------------------------------
# PipeQueueRTL
#-------------------------------------------------------------------------

class PipeQueueRTL( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.enq   = EnqIfcRTL( EntryType )
    s.deq   = DeqIfcRTL( EntryType )
    s.count = OutPort( mk_bits( clog2( num_entries+1 ) ) )

    # Components

    assert num_entries > 0
    if num_entries == 1:
      s.q = PipeQueue1EntryRTL( EntryType )
      connect( s.enq,   s.q.enq )
      connect( s.deq,   s.q.deq )
      connect( s.count, s.q.count )

    else:
      s.ctrl  = PipeQueueCtrlRTL ( num_entries )
      s.dpath = NormalQueueDpathRTL( EntryType, num_entries )

      # Connect ctrl to data path

      connect( s.ctrl.wen,     s.dpath.wen     )
      connect( s.ctrl.waddr,   s.dpath.waddr   )
      connect( s.ctrl.raddr,   s.dpath.raddr   )

      # Connect to interface

      connect( s.enq.en,  s.ctrl.enq_en   )
      connect( s.enq.rdy, s.ctrl.enq_rdy  )
      connect( s.deq.en,  s.ctrl.deq_en   )
      connect( s.deq.rdy, s.ctrl.deq_rdy  )
      connect( s.count,   s.ctrl.count    )
      connect( s.enq.msg, s.dpath.enq_msg )
      connect( s.deq.msg, s.dpath.deq_msg )

  # Line trace

  def line_trace( s ):
    return "{}({}){}".format( s.enq, s.count, s.deq )

#-------------------------------------------------------------------------
# Ctrl and Dpath for BypassQueue
#-------------------------------------------------------------------------

class BypassQueueDpathRTL( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.enq_msg =  InPort( EntryType )
    s.deq_msg = OutPort( EntryType )

    s.wen     = InPort( Bits1 )
    s.waddr   = InPort( mk_bits( clog2( num_entries ) ) )
    s.raddr   = InPort( mk_bits( clog2( num_entries ) ) )
    s.mux_sel = InPort( Bits1 )

    # Component

    s.queue = RegisterFile( EntryType, num_entries )(
      raddr = { 0: s.raddr   },
      wen   = { 0: s.wen     },
      waddr = { 0: s.waddr   },
      wdata = { 0: s.enq_msg },
    )

    s.mux = Mux( EntryType, 2 )(
      sel = s.mux_sel,
      in_ = { 0: s.queue.rdata[0], 1: s.enq_msg },
      out = s.deq_msg,
    )

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
    s.head_next = Wire( PtrType )
    s.tail_next = Wire( PtrType )

    # Connections

    connect( s.wen,   s.enq_xfer )
    connect( s.waddr, s.tail     )
    connect( s.raddr, s.head     )

    @s.update
    def up_enq_rdy():
      s.enq_rdy = ( s.count < s.num_entries ) & ~s.reset

    @s.update
    def up_deq_rdy():
      if s.reset:
        s.deq_rdy = b1(0)
      else:
        s.deq_rdy = ( s.count > CountType(0) ) | s.enq_en

    @s.update
    def up_mux_sel():
      s.mux_sel = s.count == CountType(0)

    @s.update
    def up_xfer_signals():
      s.enq_xfer  = s.enq_en & s.enq_rdy
      s.deq_xfer  = s.deq_en & s.deq_rdy

    @s.update
    def up_next():
      s.head_next = s.head + PtrType(1) if s.head < s.last_idx else PtrType(0)
      s.tail_next = s.tail + PtrType(1) if s.tail < s.last_idx else PtrType(0)

    @s.update_ff
    def up_reg():

      if s.reset:
        s.head  <<= PtrType(0)
        s.tail  <<= PtrType(0)
        s.count <<= CountType(0)

      else:
        s.head  <<= s.head_next if s.deq_xfer else s.head
        s.tail  <<= s.tail_next if s.enq_xfer else s.tail
        s.count <<= s.count + CountType(1) if s.enq_xfer & ~s.deq_xfer else \
                    s.count - CountType(1) if s.deq_xfer & ~s.enq_xfer else \
                    s.count

#-------------------------------------------------------------------------
# BypassQueueRTL
#-------------------------------------------------------------------------

class BypassQueueRTL( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.enq   = EnqIfcRTL( EntryType )
    s.deq   = DeqIfcRTL( EntryType )
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
      connect( s.deq.msg, s.dpath.deq_msg )

  # Line trace

  def line_trace( s ):
    return "{}({}){}".format( s.enq, s.count, s.deq )

#-------------------------------------------------------------------------
# NormalQueue1EntryRTL
#-------------------------------------------------------------------------

class NormalQueue1EntryRTL( Component ):

  def construct( s, EntryType ):

    # Interface

    s.enq   = EnqIfcRTL( EntryType )
    s.deq   = DeqIfcRTL( EntryType )
    s.count = OutPort  ( Bits1     )

    # Components

    s.entry = Wire( EntryType )
    s.full  = Wire( Bits1 )

    connect( s.count, s.full )

    # Logic

    @s.update_ff
    def up_full():
      if s.reset:
        s.full <<= b1(0)
      else:
        s.full <<= ~s.deq.en & (s.enq.en | s.full)

    @s.update_ff
    def up_entry():
      if s.enq.en:
        s.entry <<= s.enq.msg

    @s.update
    def up_enq_rdy():
      if s.reset:
        s.enq.rdy = b1(0)
      else:
        s.enq.rdy = ~s.full

    @s.update
    def up_deq_rdy():
      s.deq.rdy = s.full & ~s.reset

    connect( s.entry, s.deq.msg )

  def line_trace( s ):
    return "{}({}){}".format( s.enq, s.full, s.deq )

#-------------------------------------------------------------------------
# PipeQueue1EntryRTL
#-------------------------------------------------------------------------

class PipeQueue1EntryRTL( Component ):

  def construct( s, EntryType ):

    # Interface

    s.enq   = EnqIfcRTL( EntryType )
    s.deq   = DeqIfcRTL( EntryType )
    s.count = OutPort  ( Bits1     )

    # Components

    s.entry = Wire( EntryType )
    s.full  = Wire( Bits1 )

    connect( s.count, s.full )

    # Logic

    @s.update_ff
    def up_full():
      if s.reset:
        s.full <<= b1(0)
      else:
        s.full <<= s.enq.en | s.full & ~s.deq.en

    @s.update_ff
    def up_entry():
      if s.enq.en:
        s.entry <<= s.enq.msg

    @s.update
    def up_enq_rdy():
      s.enq.rdy = ( ~s.full | s.deq.en ) & ~s.reset

    @s.update
    def up_deq_rdy():
      s.deq.rdy = s.full & ~s.reset

    connect( s.entry, s.deq.msg )

  def line_trace( s ):
    return "{}({}){}".format( s.enq, s.full, s.deq )

#-------------------------------------------------------------------------
# BypassQueue1EntryRTL
#-------------------------------------------------------------------------

class BypassQueue1EntryRTL( Component ):

  def construct( s, EntryType ):

    # Interface

    s.enq   = EnqIfcRTL( EntryType )
    s.deq   = DeqIfcRTL( EntryType )
    s.count = OutPort  ( Bits1     )

    # Components

    s.entry = Wire( EntryType )
    s.full  = Wire( Bits1 )

    connect( s.count, s.full )

    # Logic

    @s.update_ff
    def up_full():
      if s.reset:
        s.full <<= b1(0)
      else:
        s.full <<= ~s.deq.en & (s.enq.en | s.full)

    @s.update_ff
    def up_entry():
      if s.enq.en & ~s.deq.en:
        s.entry <<= s.enq.msg

    @s.update
    def up_enq_rdy():
        s.enq.rdy = ~s.full & ~s.reset

    @s.update
    def up_deq_rdy():
      s.deq.rdy = ( s.full | s.enq.en ) & ~s.reset

    @s.update
    def up_deq_msg():
      s.deq.msg = s.entry if s.full else s.enq.msg

  def line_trace( s ):
    return "{}({}){}".format( s.enq, s.full, s.deq )
