from pymtl import *
from pclib.rtl import Reg, RegEn, Mux
from pclib.ifcs   import InValRdyIfc, OutValRdyIfc

class PipeQueue1RTL( ComponentLevel3 ):

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
        s.next_full = s.enq.val | (s.full & (not s.deq.val))

    else:
      @s.update
      def up_pipeq_set_enq_rdy():
        s.enq.rdy = ~s.full | s.deq.rdy

      @s.update
      def up_pipeq_full():
        s.buf.en    = s.enq.val & s.enq.rdy
        s.next_full = s.enq.val | (s.full & ~s.deq.val)

  def line_trace( s ):
    print s.full, s.next_full
    return s.enq.line_trace() + " > " + \
            ("*" if s.full else " ") + " > " + \
            s.deq.line_trace()

class BypassQueue1RTL( ComponentLevel3 ):

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

class NormalQueue1RTL( ComponentLevel3 ):

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
