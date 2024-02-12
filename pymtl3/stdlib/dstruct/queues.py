"""
-------------------------------------------------------------------------
Queues
-------------------------------------------------------------------------
Common queue data structures.

Author : Yanghui Ou, Peitian Pan
  Date : Aug 26, 2022
"""


from pymtl3 import *
from pymtl3.stdlib.primitive import Mux, RegisterFile

def enrdy_to_str( msg, en, rdy, trace_len=15 ):
  if     en and not rdy: return "X".ljust( trace_len ) # Not allowed!
  if not en and     rdy: return " ".ljust( trace_len ) # Idle
  if not en and not rdy: return "#".ljust( trace_len ) # Stalled
  return f"{msg}".ljust( trace_len ) # en and rdy

#-------------------------------------------------------------------------
# Dpath and Ctrl for NormalQueue
#-------------------------------------------------------------------------

class NormalQueueDpath( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.enq_msg =  InPort( EntryType )
    s.deq_msg = OutPort( EntryType )

    s.wen   = InPort()
    s.waddr = InPort( clog2( num_entries ) )
    s.raddr = InPort( clog2( num_entries ) )

    # Component

    s.queue = m = RegisterFile( EntryType, num_entries )
    m.raddr[0] //= s.raddr
    m.rdata[0] //= s.deq_msg
    m.wen[0]   //= s.wen
    m.waddr[0] //= s.waddr
    m.wdata[0] //= s.enq_msg

class NormalQueueCtrl( Component ):

  def construct( s, num_entries=2 ):

    # Constants

    addr_nbits    = clog2    ( num_entries   )
    count_nbits   = clog2    ( num_entries+1 )
    PtrType       = mk_bits  ( addr_nbits    )
    CountType     = mk_bits  ( count_nbits   )
    s.last_idx    = PtrType  ( num_entries-1 )
    s.num_entries = CountType( num_entries   )

    # Interface

    s.enq_en  = InPort ()
    s.enq_rdy = OutPort()
    s.deq_en  = InPort ()
    s.deq_rdy = OutPort()
    s.count   = OutPort( CountType )

    s.wen     = OutPort()
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

    s.enq_rdy //= lambda: ~s.reset & ( s.count < s.num_entries )
    s.deq_rdy //= lambda: ~s.reset & ( s.count > CountType(0) )

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
# NormalQueue
#-------------------------------------------------------------------------

class NormalQueue( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.enq_en = InPort()
    s.enq_rdy = OutPort()
    s.enq_msg = InPort( EntryType )
    s.deq_en = InPort()
    s.deq_rdy = OutPort()
    s.deq_msg = OutPort( EntryType )
    s.count = OutPort( mk_bits( clog2( num_entries+1 ) ) )

    # Components

    assert num_entries > 0
    if num_entries == 1:
      s.q = NormalQueue1Entry( EntryType )
      connect( s.enq_en,   s.q.enq_en )
      connect( s.enq_rdy,   s.q.enq_rdy )
      connect( s.enq_msg,   s.q.enq_msg )
      connect( s.deq_en,   s.q.deq_en )
      connect( s.deq_rdy,   s.q.deq_rdy )
      connect( s.deq_msg,   s.q.deq_msg )
      connect( s.count, s.q.count )

    else:
      s.ctrl  = NormalQueueCtrl ( num_entries )
      s.dpath = NormalQueueDpath( EntryType, num_entries )

      # Connect ctrl to data path

      connect( s.ctrl.wen,     s.dpath.wen     )
      connect( s.ctrl.waddr,   s.dpath.waddr   )
      connect( s.ctrl.raddr,   s.dpath.raddr   )

      # Connect to interface

      connect( s.enq_en,  s.ctrl.enq_en   )
      connect( s.enq_rdy, s.ctrl.enq_rdy  )
      connect( s.deq_en,  s.ctrl.deq_en   )
      connect( s.deq_rdy, s.ctrl.deq_rdy  )
      connect( s.count,   s.ctrl.count    )
      connect( s.enq_msg, s.dpath.enq_msg )
      connect( s.deq_msg, s.dpath.deq_msg )

  # Line trace

  def line_trace( s ):
    enq_str = enrdy_to_str( s.enq_msg, s.enq_en, s.enq_rdy )
    deq_str = enrdy_to_str( s.deq_msg, s.deq_en, s.deq_rdy )
    return f"{enq_str}({s.count}){deq_str}"

#-------------------------------------------------------------------------
# Ctrl for PipeQueue
#-------------------------------------------------------------------------

class PipeQueueCtrl( Component ):

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
# PipeQueue
#-------------------------------------------------------------------------

class PipeQueue( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.enq_en = InPort()
    s.enq_rdy = OutPort()
    s.enq_msg = InPort( EntryType )
    s.deq_en = InPort()
    s.deq_rdy = OutPort()
    s.deq_msg = OutPort( EntryType )
    s.count = OutPort( mk_bits( clog2( num_entries+1 ) ) )

    # Components

    assert num_entries > 0
    if num_entries == 1:
      s.q = PipeQueue1Entry( EntryType )
      connect( s.enq_en,   s.q.enq_en )
      connect( s.enq_rdy,   s.q.enq_rdy )
      connect( s.enq_msg,   s.q.enq_msg )
      connect( s.deq_en,   s.q.deq_en )
      connect( s.deq_rdy,   s.q.deq_rdy )
      connect( s.deq_msg,   s.q.deq_msg )
      connect( s.count, s.q.count )

    else:
      s.ctrl  = PipeQueueCtrl ( num_entries )
      s.dpath = NormalQueueDpath( EntryType, num_entries )

      # Connect ctrl to data path

      connect( s.ctrl.wen,     s.dpath.wen     )
      connect( s.ctrl.waddr,   s.dpath.waddr   )
      connect( s.ctrl.raddr,   s.dpath.raddr   )

      # Connect to interface

      connect( s.enq_en,  s.ctrl.enq_en   )
      connect( s.enq_rdy, s.ctrl.enq_rdy  )
      connect( s.deq_en,  s.ctrl.deq_en   )
      connect( s.deq_rdy, s.ctrl.deq_rdy  )
      connect( s.count,   s.ctrl.count    )
      connect( s.enq_msg, s.dpath.enq_msg )
      connect( s.deq_msg, s.dpath.deq_msg )

  # Line trace

  def line_trace( s ):
    enq_str = enrdy_to_str( s.enq_msg, s.enq_en, s.enq_rdy )
    deq_str = enrdy_to_str( s.deq_msg, s.deq_en, s.deq_rdy )
    return f"{enq_str}({s.count}){deq_str}"

#-------------------------------------------------------------------------
# Ctrl and Dpath for BypassQueue
#-------------------------------------------------------------------------

class BypassQueueDpath( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.enq_msg =  InPort( EntryType )
    s.deq_msg = OutPort( EntryType )

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
    m.out    //= s.deq_msg

class BypassQueueCtrl( Component ):

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
# BypassQueue
#-------------------------------------------------------------------------

class BypassQueue( Component ):

  def construct( s, EntryType, num_entries=2 ):

    # Interface

    s.enq_en = InPort()
    s.enq_rdy = OutPort()
    s.enq_msg = InPort( EntryType )
    s.deq_en = InPort()
    s.deq_rdy = OutPort()
    s.deq_msg = OutPort( EntryType )
    s.count = OutPort( mk_bits( clog2( num_entries+1 ) ) )

    # Components

    assert num_entries > 0
    if num_entries == 1:
      s.q = BypassQueue1Entry( EntryType )
      connect( s.enq_en,   s.q.enq_en )
      connect( s.enq_rdy,   s.q.enq_rdy )
      connect( s.enq_msg,   s.q.enq_msg )
      connect( s.deq_en,   s.q.deq_en )
      connect( s.deq_rdy,   s.q.deq_rdy )
      connect( s.deq_msg,   s.q.deq_msg )
      connect( s.count, s.q.count )

    else:
      s.ctrl  = BypassQueueCtrl ( num_entries )
      s.dpath = BypassQueueDpath( EntryType, num_entries )

      # Connect ctrl to data path

      connect( s.ctrl.wen,     s.dpath.wen     )
      connect( s.ctrl.waddr,   s.dpath.waddr   )
      connect( s.ctrl.raddr,   s.dpath.raddr   )
      connect( s.ctrl.mux_sel, s.dpath.mux_sel )

      # Connect to interface

      connect( s.enq_en,  s.ctrl.enq_en   )
      connect( s.enq_rdy, s.ctrl.enq_rdy  )
      connect( s.deq_en,  s.ctrl.deq_en   )
      connect( s.deq_rdy, s.ctrl.deq_rdy  )
      connect( s.count,   s.ctrl.count    )
      connect( s.enq_msg, s.dpath.enq_msg )
      connect( s.deq_msg, s.dpath.deq_msg )

  # Line trace

  def line_trace( s ):
    enq_str = enrdy_to_str( s.enq_msg, s.enq_en, s.enq_rdy )
    deq_str = enrdy_to_str( s.deq_msg, s.deq_en, s.deq_rdy )
    return f"{enq_str}({s.count}){deq_str}"

#-------------------------------------------------------------------------
# NormalQueue1Entry
#-------------------------------------------------------------------------

class NormalQueue1Entry( Component ):

  def construct( s, EntryType ):

    # Interface

    s.enq_en = InPort()
    s.enq_rdy = OutPort()
    s.enq_msg = InPort( EntryType )
    s.deq_en = InPort()
    s.deq_rdy = OutPort()
    s.deq_msg = OutPort( EntryType )
    s.count = OutPort  ( Bits1     )

    # Components

    s.entry = Wire( EntryType )
    s.full  = Wire( Bits1 )

    # Logic

    s.count //= s.full

    s.deq_msg //= s.entry

    s.enq_rdy //= lambda: ~s.reset & ~s.full
    s.deq_rdy //= lambda: ~s.reset & s.full

    @update_ff
    def ff_normal1():
      s.full <<= ~s.reset & ( ~s.deq_en & (s.enq_en | s.full) )
      if s.enq_en:
        s.entry <<= s.enq_msg

  def line_trace( s ):
    enq_str = enrdy_to_str( s.enq_msg, s.enq_en, s.enq_rdy )
    deq_str = enrdy_to_str( s.deq_msg, s.deq_en, s.deq_rdy )
    return f"{enq_str}({s.full}){deq_str}"

#-------------------------------------------------------------------------
# PipeQueue1Entry
#-------------------------------------------------------------------------

class PipeQueue1Entry( Component ):

  def construct( s, EntryType ):

    # Interface

    s.enq_en = InPort()
    s.enq_rdy = OutPort()
    s.enq_msg = InPort( EntryType )
    s.deq_en = InPort()
    s.deq_rdy = OutPort()
    s.deq_msg = OutPort( EntryType )
    s.count = OutPort  ( Bits1     )

    # Components

    s.entry = Wire( EntryType )
    s.full  = Wire( Bits1 )

    # Logic

    s.count //= s.full

    s.deq_msg //= s.entry

    s.enq_rdy //= lambda: ~s.reset & ( ~s.full | s.deq_en )
    s.deq_rdy //= lambda: s.full & ~s.reset

    @update_ff
    def ff_pipe1():
      s.full <<= ~s.reset & ( s.enq_en | s.full & ~s.deq_en )

      if s.enq_en:
        s.entry <<= s.enq_msg

  def line_trace( s ):
    enq_str = enrdy_to_str( s.enq_msg, s.enq_en, s.enq_rdy )
    deq_str = enrdy_to_str( s.deq_msg, s.deq_en, s.deq_rdy )
    return f"{enq_str}({s.full}){deq_str}"

#-------------------------------------------------------------------------
# BypassQueue1Entry
#-------------------------------------------------------------------------

class BypassQueue1Entry( Component ):

  def construct( s, EntryType ):

    # Interface

    s.enq_en = InPort()
    s.enq_rdy = OutPort()
    s.enq_msg = InPort( EntryType )
    s.deq_en = InPort()
    s.deq_rdy = OutPort()
    s.deq_msg = OutPort( EntryType )
    s.count = OutPort  ( Bits1     )

    # Components

    s.entry = Wire( EntryType )
    s.full  = Wire( Bits1 )

    s.bypass_mux = m = Mux( EntryType, 2 )
    m.in_[0] //= s.enq_msg
    m.in_[1] //= s.entry
    m.out    //= s.deq_msg
    m.sel    //= s.full

    # Logic

    s.count //= s.full

    s.enq_rdy //= lambda: ~s.reset & ~s.full
    s.deq_rdy //= lambda: ~s.reset & ( s.full | s.enq_en )

    @update_ff
    def ff_bypass1():
      s.full <<= ~s.reset & ( ~s.deq_en & (s.enq_en | s.full) )

      if s.enq_en & ~s.deq_en:
        s.entry <<= s.enq_msg

  def line_trace( s ):
    enq_str = enrdy_to_str( s.enq_msg, s.enq_en, s.enq_rdy )
    deq_str = enrdy_to_str( s.deq_msg, s.deq_en, s.deq_rdy )
    return f"{enq_str}({s.full}){deq_str}"
