from pymtl3 import *
from pymtl3.stdlib.basic_rtl import Mux, Reg, RegEn, RegisterFile
from pymtl3.stdlib.ifcs import InValRdyIfc, OutValRdyIfc


class PipeQueue1RTL( Component ):

  def construct( s, Type ):
    s.enq = InValRdyIfc ( Type )
    s.deq = OutValRdyIfc( Type )

    s.buffer = m = RegEn( Type )
    m.out //= s.deq.msg
    m.in_ //= s.enq.msg

    s.next_full = Wire( Bits1 )
    s.full      = Wire( Bits1 )
    connect( s.full, s.deq.val )

    @update_ff
    def up_full():
      s.full <<= s.next_full

    @update
    def up_pipeq_set_enq_rdy():
      s.enq.rdy @= ~s.full | s.deq.rdy

    @update
    def up_pipeq_full():
      s.buffer.en @= s.enq.val & s.enq.rdy
      s.next_full @= s.enq.val | (s.full & ~s.deq.rdy)

  def line_trace( s ):
    return s.enq.line_trace() + " > " + \
            ("*" if s.full else " ") + " > " + \
            s.deq.line_trace()

class BypassQueue1RTL( Component ):

  def construct( s, Type ):
    s.enq = InValRdyIfc ( Type )
    s.deq = OutValRdyIfc( Type )

    s.buffer = RegEn( Type )
    s.buffer.in_ //= s.enq.msg

    s.next_full = Wire( Bits1 )
    s.full      = Wire( Bits1 )

    s.byp_mux = m = Mux( Type, 2 )
    m.out    //= s.deq.msg
    m.in_[0] //= s.enq.msg
    m.in_[1] //= s.buffer.out
    m.sel    //= s.full # full -- buffer.out, empty -- bypass

    @update_ff
    def up_full():
      s.full <<= s.next_full

    @update
    def up_bypq_set_enq_rdy():
      s.enq.rdy @= ~s.full

    @update
    def up_bypq_internal():
      s.buffer.en @= (~s.deq.rdy) & (s.enq.val & s.enq.rdy)
      s.next_full @= (~s.deq.rdy) & s.deq.val

    # this enables the sender to make enq.val depend on enq.rdy
    @update
    def up_bypq_set_deq_val():
      s.deq.val @= s.full | s.enq.val

  def line_trace( s ):
    return s.enq.line_trace() + " > " + \
            ("*" if s.full else " ") + " > " + \
            s.deq.line_trace()

class NormalQueue1RTL( Component ):

  def construct( s, Type ):
    s.enq = InValRdyIfc( Type )
    s.deq = OutValRdyIfc( Type )

    s.buffer = m = RegEn( Type )
    m.in_ //= s.enq.msg
    m.out //= s.deq.msg

    s.next_full = Wire( Bits1 )
    s.full      = Wire( Bits1 )
    connect( s.full, s.deq.val )

    @update_ff
    def up_full():
      s.full <<= s.next_full

    @update
    def up_normq_set_enq_rdy():
      s.enq.rdy @= ~s.full

    @update
    def up_normq_internal():
      s.buffer.en @= s.enq.val & s.enq.rdy
      s.next_full @= (s.full & ~s.deq.rdy) | s.buffer.en

  def line_trace( s ):
    return s.enq.line_trace() + " > " + \
            ("*" if s.full else " ") + " > " + \
            s.deq.line_trace()

#-----------------------------------------------------------------------
# NormalQueueRTL
#-----------------------------------------------------------------------
class NormalQueueRTL( Component ):

  def construct( s, num_entries, Type ):

    s.enq              = InValRdyIfc( Type )
    s.deq              = OutValRdyIfc( Type )
    s.num_free_entries = OutPort( mk_bits( clog2(num_entries+1) ) )

    # Ctrl and Dpath unit instantiation

    s.ctrl  = NormalQueueRTLCtrl ( num_entries       )
    s.dpath = NormalQueueRTLDpath( num_entries, Type )

    # Ctrl unit connections

    connect( s.ctrl.enq_val,          s.enq.val          )
    connect( s.ctrl.enq_rdy,          s.enq.rdy          )
    connect( s.ctrl.deq_val,          s.deq.val          )
    connect( s.ctrl.deq_rdy,          s.deq.rdy          )
    connect( s.ctrl.num_free_entries, s.num_free_entries )

    # Dpath unit connections

    connect( s.dpath.enq_bits, s.enq.msg    )
    connect( s.dpath.deq_bits, s.deq.msg    )

    # Control Signal connections (ctrl -> dpath)

    connect( s.dpath.wen,      s.ctrl.wen   )
    connect( s.dpath.waddr,    s.ctrl.waddr )
    connect( s.dpath.raddr,    s.ctrl.raddr )

  def line_trace( s ):
    return "{} () {}".format( s.enq.line_trace(), s.deq.line_trace() )

#-----------------------------------------------------------------------
# NormalQueueRTLDpath
#-----------------------------------------------------------------------
class NormalQueueRTLDpath( Component ):

  def construct( s, num_entries, Type ):

    SizeType      = mk_bits( clog2( num_entries+1 ) )
    AddrType      = mk_bits( clog2( num_entries ) )

    s.enq_bits  = InPort  ( Type )
    s.deq_bits  = OutPort ( Type )

    # Control signal (ctrl -> dpath)
    s.wen       = InPort  ( Bits1 )
    s.waddr     = InPort  ( AddrType )
    s.raddr     = InPort  ( AddrType )

    # Queue storage

    s.queue = RegisterFile( Type, num_entries )

    # Connect queue storage

    connect( s.queue.raddr[0], s.raddr    )
    connect( s.queue.rdata[0], s.deq_bits )
    connect( s.queue.wen[0],   s.wen      )
    connect( s.queue.waddr[0], s.waddr    )
    connect( s.queue.wdata[0], s.enq_bits )

#-----------------------------------------------------------------------
# NormalQueueRTLCtrl
#-----------------------------------------------------------------------
class NormalQueueRTLCtrl( Component ):

  def construct( s, num_entries ):

    s.num_entries = num_entries

    SizeType      = mk_bits( clog2( num_entries+1 ) )
    AddrType      = mk_bits( clog2( num_entries ) )

    # Interface Ports

    s.enq_val          = InPort  ( Bits1 )
    s.enq_rdy          = OutPort ( Bits1 )
    s.deq_val          = OutPort ( Bits1 )
    s.deq_rdy          = InPort  ( Bits1 )
    s.num_free_entries = OutPort ( SizeType )

    # Control signal (ctrl -> dpath)
    s.wen              = OutPort ( Bits1 )
    s.waddr            = OutPort ( AddrType )
    s.raddr            = OutPort ( AddrType )

    # Wires

    s.full             = Wire ( Bits1 )
    s.empty            = Wire ( Bits1 )
    s.do_enq           = Wire ( Bits1 )
    s.do_deq           = Wire ( Bits1 )
    s.enq_ptr          = Wire ( AddrType )
    s.deq_ptr          = Wire ( AddrType )
    s.enq_ptr_next     = Wire ( AddrType )
    s.deq_ptr_next     = Wire ( AddrType )
    # TODO: can't infer these temporaries due to if statement, fix
    s.enq_ptr_inc      = Wire ( AddrType )
    s.deq_ptr_inc      = Wire ( AddrType )
    s.full_next_cycle  = Wire ( Bits1 )

    s.last_idx         = AddrType( num_entries - 1 )

    @update
    def comb():

      # only enqueue/dequeue if valid and ready

      s.do_enq @= s.enq_rdy & s.enq_val
      s.do_deq @= s.deq_rdy & s.deq_val

      # write enable

      s.wen @= s.do_enq

      # enq ptr incrementer

      if s.enq_ptr == s.last_idx: s.enq_ptr_inc @= 0
      else:                       s.enq_ptr_inc @= s.enq_ptr + 1

      # deq ptr incrementer

      if s.deq_ptr == s.last_idx: s.deq_ptr_inc @= 0
      else:                       s.deq_ptr_inc @= s.deq_ptr + 1

      # set the next ptr value

      if s.do_enq: s.enq_ptr_next @= s.enq_ptr_inc
      else:        s.enq_ptr_next @= s.enq_ptr

      if s.do_deq: s.deq_ptr_next @= s.deq_ptr_inc
      else:        s.deq_ptr_next @= s.deq_ptr

      # number of free entries calculation

      if   s.reset:
        s.num_free_entries @= s.num_entries
      elif s.full:
        s.num_free_entries @= 0
      elif s.empty:
        s.num_free_entries @= s.num_entries
      elif s.enq_ptr > s.deq_ptr:
        s.num_free_entries @= s.num_entries - zext( s.enq_ptr - s.deq_ptr, SizeType)
      elif s.deq_ptr > s.enq_ptr:
        s.num_free_entries @= zext( s.deq_ptr - s.enq_ptr, SizeType )

      s.full_next_cycle @= s.do_enq & ~s.do_deq & (s.enq_ptr_next == s.deq_ptr)

    @update
    def up_ctrl_signals():

      # set output signals

      s.empty   @= ~s.full & (s.enq_ptr == s.deq_ptr)

      s.enq_rdy @= ~s.full
      s.deq_val @= ~s.empty

      # set control signals

      s.waddr   @= s.enq_ptr
      s.raddr   @= s.deq_ptr

    @update_ff
    def seq():

      if s.reset:
        s.deq_ptr <<= AddrType( 0 )
        s.enq_ptr <<= AddrType( 0 )
      else:
        s.deq_ptr <<= s.deq_ptr_next
        s.enq_ptr <<= s.enq_ptr_next

      if   s.reset:             s.full <<= Bits1(0)
      elif s.full_next_cycle:   s.full <<= Bits1(1)
      elif (s.do_deq & s.full): s.full <<= Bits1(0)
      else:                     s.full <<= s.full
