from pymtl import *
from pclib.ifcs import InValRdyIfc, OutValRdyIfc
from pclib.rtl  import Mux, Reg, RegEn, RegisterFile

class PipeQueue1RTL( RTLComponent ):

  def __init__( s, Type ):
    s.enq = InValRdyIfc ( Type )
    s.deq = OutValRdyIfc( Type )

    s.buf  = RegEn( Type )( out = s.deq.msg, in_ = s.enq.msg )

    s.next_full = Wire( int if Type is int else Bits1 )
    s.full      = Wire( int if Type is int else Bits1 )
    s.connect( s.full, s.deq.val )

    @s.update_on_edge
    def up_full():
      s.full = s.next_full

    if Type is int:
      @s.update
      def up_pipeq_set_enq_rdy():
        s.enq.rdy = (not s.full) | s.deq.rdy

      @s.update
      def up_pipeq_full():
        s.buf.en    = s.enq.val & s.enq.rdy
        s.next_full = s.enq.val | (s.full & (not s.deq.rdy))

    else:
      @s.update
      def up_pipeq_set_enq_rdy():
        s.enq.rdy = ~s.full | s.deq.rdy

      @s.update
      def up_pipeq_full():
        s.buf.en    = s.enq.val & s.enq.rdy
        s.next_full = s.enq.val | (s.full & ~s.deq.rdy)

  def line_trace( s ):
    return s.enq.line_trace() + " > " + \
            ("*" if s.full else " ") + " > " + \
            s.deq.line_trace()

class BypassQueue1RTL( RTLComponent ):

  def __init__( s, Type ):
    s.enq = InValRdyIfc ( Type )
    s.deq = OutValRdyIfc( Type )

    s.buf = RegEn( Type )( in_ = s.enq.msg )

    s.next_full = Wire( int if Type is int else Bits1 )
    s.full      = Wire( int if Type is int else Bits1 )

    s.byp_mux = Mux( Type, 2 )(
      out = s.deq.msg,
      in_ = { 0: s.enq.msg,
              1: s.buf.out, },
      sel = s.full, # full -- buf.out, empty -- bypass
    )

    @s.update_on_edge
    def up_full():
      s.full = s.next_full

    if Type is int:
      @s.update
      def up_bypq_set_enq_rdy():
        s.enq.rdy = not s.full

      @s.update
      def up_bypq_internal():
        s.buf.en    = (not s.deq.rdy) & (s.enq.val & s.enq.rdy)
        s.next_full = (not s.deq.rdy) & s.deq.val
    else:
      @s.update
      def up_bypq_set_enq_rdy():
        s.enq.rdy = ~s.full

      @s.update
      def up_bypq_internal():
        s.buf.en    = (~s.deq.rdy) & (s.enq.val & s.enq.rdy)
        s.next_full = (~s.deq.rdy) & s.deq.val

    # this enables the sender to make enq.val depend on enq.rdy
    @s.update
    def up_bypq_set_deq_val():
      s.deq.val = s.full | s.enq.val

  def line_trace( s ):
    return s.enq.line_trace() + " > " + \
            ("*" if s.full else " ") + " > " + \
            s.deq.line_trace()

class NormalQueue1RTL( RTLComponent ):

  def __init__( s, Type ):
    s.enq = InValRdyIfc( Type )
    s.deq = OutValRdyIfc( Type )

    s.buf  = RegEn( Type )( out = s.deq.msg, in_ = s.enq.msg )

    s.next_full = Wire( int if Type is int else Bits1 )
    s.full      = Wire( int if Type is int else Bits1 )
    s.connect( s.full, s.deq.val )

    @s.update_on_edge
    def up_full():
      s.full = s.next_full

    if Type is int:
      @s.update
      def up_normq_set_enq_rdy():
        s.enq.rdy = not s.full

      @s.update
      def up_normq_internal():
        s.buf.en    = s.enq.val & s.enq.rdy
        s.next_full = (s.full & (not s.deq.rdy)) | s.buf.en
    else:
      @s.update
      def up_normq_set_enq_rdy():
        s.enq.rdy = ~s.full

      @s.update
      def up_normq_internal():
        s.buf.en    = s.enq.val & s.enq.rdy
        s.next_full = (s.full & ~s.deq.rdy) | s.buf.en

  def line_trace( s ):
    return s.enq.line_trace() + " > " + \
            ("*" if s.full else " ") + " > " + \
            s.deq.line_trace()


#-----------------------------------------------------------------------
# NormalQueueRTL
#-----------------------------------------------------------------------
class NormalQueueRTL( RTLComponent ):

  def __init__( s, num_entries, Type ):

    s.enq              = InValRdyIfc( Type )
    s.deq              = OutValRdyIfc( Type )
    s.num_free_entries = OutVPort( mk_bits( clog2(num_entries) ) )

    # Ctrl and Dpath unit instantiation

    s.ctrl  = NormalQueueRTLCtrl ( num_entries       )
    s.dpath = NormalQueueRTLDpath( num_entries, Type )

    # Ctrl unit connections

    s.connect( s.ctrl.enq_val,          s.enq.val          )
    s.connect( s.ctrl.enq_rdy,          s.enq.rdy          )
    s.connect( s.ctrl.deq_val,          s.deq.val          )
    s.connect( s.ctrl.deq_rdy,          s.deq.rdy          )
    s.connect( s.ctrl.num_free_entries, s.num_free_entries )

    # Dpath unit connections

    s.connect( s.dpath.enq_bits, s.enq.msg    )
    s.connect( s.dpath.deq_bits, s.deq.msg    )

    # Control Signal connections (ctrl -> dpath)

    s.connect( s.dpath.wen,      s.ctrl.wen   )
    s.connect( s.dpath.waddr,    s.ctrl.waddr )
    s.connect( s.dpath.raddr,    s.ctrl.raddr )

  def line_trace( s ):
    return "{} () {}".format( s.enq, s.deq )

#-----------------------------------------------------------------------
# NormalQueueRTLDpath
#-----------------------------------------------------------------------
class NormalQueueRTLDpath( RTLComponent ):

  def __init__( s, num_entries, Type ):

    s.enq_bits  = InVPort  ( Type )
    s.deq_bits  = OutVPort ( Type )

    # Control signal (ctrl -> dpath)
    addr_nbits  = clog2( num_entries )
    s.wen       = InVPort  ( Bits1 )
    s.waddr     = InVPort  ( mk_bits( addr_nbits ) )
    s.raddr     = InVPort  ( mk_bits( addr_nbits ) )

    # Queue storage

    s.queue = RegisterFile( Type, num_entries )

    # Connect queue storage

    s.connect( s.queue.raddr[0], s.raddr    )
    s.connect( s.queue.rdata[0], s.deq_bits )
    s.connect( s.queue.wen[0],   s.wen      )
    s.connect( s.queue.waddr[0], s.waddr    )
    s.connect( s.queue.wdata[0], s.enq_bits )

#-----------------------------------------------------------------------
# NormalQueueRTLCtrl
#-----------------------------------------------------------------------
class NormalQueueRTLCtrl( RTLComponent ):

  def __init__( s, num_entries ):

    s.num_entries = num_entries
    addr_nbits    = clog2( num_entries )

    # Interface Ports

    s.enq_val          = InVPort  ( Bits1 )
    s.enq_rdy          = OutVPort ( Bits1 )
    s.deq_val          = OutVPort ( Bits1 )
    s.deq_rdy          = InVPort  ( Bits1 )
    s.num_free_entries = OutVPort ( mk_bits( clog2( num_entries ) ) )

    # Control signal (ctrl -> dpath)
    s.wen              = OutVPort ( Bits1 )
    s.waddr            = OutVPort ( mk_bits( addr_nbits ) )
    s.raddr            = OutVPort ( mk_bits( addr_nbits ) )

    # Wires

    s.full             = Wire ( Bits1 )
    s.empty            = Wire ( Bits1 )
    s.do_enq           = Wire ( Bits1 )
    s.do_deq           = Wire ( Bits1 )
    s.enq_ptr          = Wire ( mk_bits( addr_nbits ) )
    s.deq_ptr          = Wire ( mk_bits( addr_nbits ) )
    s.enq_ptr_next     = Wire ( mk_bits( addr_nbits ) )
    s.deq_ptr_next     = Wire ( mk_bits( addr_nbits ) )
    # TODO: can't infer these temporaries due to if statement, fix
    s.enq_ptr_inc      = Wire ( mk_bits( addr_nbits ) )
    s.deq_ptr_inc      = Wire ( mk_bits( addr_nbits ) )
    s.full_next_cycle  = Wire ( Bits1 )

    s.last_idx         = num_entries - 1

    @s.update
    def comb():

      # only enqueue/dequeue if valid and ready

      s.do_enq = s.enq_rdy and s.enq_val
      s.do_deq = s.deq_rdy and s.deq_val

      # write enable

      s.wen     = s.do_enq

      # enq ptr incrementer

      if s.enq_ptr == s.last_idx: s.enq_ptr_inc = 0
      else:                       s.enq_ptr_inc = s.enq_ptr + 1

      # deq ptr incrementer

      if s.deq_ptr == s.last_idx: s.deq_ptr_inc = 0
      else:                       s.deq_ptr_inc = s.deq_ptr + 1

      # set the next ptr value

      if s.do_enq: s.enq_ptr_next = s.enq_ptr_inc
      else:        s.enq_ptr_next = s.enq_ptr

      if s.do_deq: s.deq_ptr_next = s.deq_ptr_inc
      else:        s.deq_ptr_next = s.deq_ptr

      # number of free entries calculation

      if   s.reset:
        s.num_free_entries = s.num_entries
      elif s.full:
        s.num_free_entries = 0
      elif s.empty:
        s.num_free_entries = s.num_entries
      elif s.enq_ptr > s.deq_ptr:
        s.num_free_entries = s.num_entries - ( s.enq_ptr - s.deq_ptr )
      elif s.deq_ptr > s.enq_ptr:
        s.num_free_entries = s.deq_ptr - s.enq_ptr

      s.full_next_cycle = (s.do_enq and not s.do_deq and
                                (s.enq_ptr_next == s.deq_ptr))

    @s.update
    def up_ctrl_signals():

      # set output signals

      s.empty   = not s.full and (s.enq_ptr == s.deq_ptr)

      s.enq_rdy = not s.full
      s.deq_val = not s.empty

      # set control signals

      s.waddr   = s.enq_ptr
      s.raddr   = s.deq_ptr

    @s.update_on_edge
    def seq():

      if s.reset: s.deq_ptr = 0
      else:       s.deq_ptr = s.deq_ptr_next

      if s.reset: s.enq_ptr = 0
      else:       s.enq_ptr = s.enq_ptr_next

      if   s.reset:               s.full = 0
      elif s.full_next_cycle:     s.full = 1
      elif (s.do_deq and s.full): s.full = 0
      else:                       s.full = s.full

