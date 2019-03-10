from pymtl import *
from pclib.rtl import Reg, RegEn, Mux
from pclib.ifcs.SendRecvIfc import SendIfc, RecvIfc

class PipeQueue1RTL( RTLComponent ):

  def construct( s, Type ):
    s.enq = RecvIfc( Type )
    s.deq = SendIfc( Type )

    s.buf  = RegEn( Type )( en = s.enq.en, in_ = s.enq.msg, out = s.deq.msg )
    s.full = Reg( Bits1 )

    @s.update
    def up_pipeq_use_deq_rdy():
      s.deq.en  =  s.full.out & s.deq.rdy
      s.enq.rdy = ~s.full.out | s.deq.rdy

    @s.update
    def up_pipeq_full():
      s.full.in_ = s.enq.en | (s.full.out & ~s.deq.rdy )

  def line_trace( s ):
    return s.buf.line_trace()

class BypassQueue1RTL( RTLComponent ):

  def construct( s, Type ):
    s.enq = RecvIfc( Type )
    s.deq = SendIfc( Type )

    s.buf  = RegEn( Type )( in_ = s.enq.msg )

    s.full = Reg( Bits1 )

    s.byp_mux = Mux( Type, 2 )(
      out = s.deq.msg,
      in_ = { 0: s.enq.msg,
              1: s.buf.out, },
      sel = s.full.out, # full -- buf.out, empty -- bypass
    )

    @s.update
    def up_bypq_set_enq_rdy():
      s.enq.rdy = ~s.full.out

    @s.update
    def up_bypq_use_enq_en():
      s.deq.en   = (s.enq.en | s.full.out) & s.deq.rdy
      s.buf.en   =  s.enq.en & ~s.deq.en
      s.full.in_ = (s.enq.en | s.full.out) & ~s.deq.en

  def line_trace( s ):
    return s.buf.line_trace()

class NormalQueue1RTL( RTLComponent ):

  def construct( s, Type ):
    s.enq = RecvIfc( Type )
    s.deq = SendIfc( Type )

    # Now since enq.en depends on enq.rdy, enq.en == 1 actually means
    # we will enq some stuff
    s.buf  = RegEn( Type )( en = s.enq.en, in_ = s.enq.msg, out = s.deq.msg )
    s.full = Reg( Bits1 )

    @s.update
    def up_normq_set_enq_rdy():
      s.enq.rdy = ~s.full.out

    @s.update
    def up_normq_full():
      # When the buff is full and deq side is ready, we enable deq
      s.deq.en = s.full.out & s.deq.rdy

      # not full and valid enq, or no deque and enq, or no deque and already full
      s.full.in_ = (~s.full.out & s.enq.en) | \
                   (~s.deq.rdy & s.enq.en)  | \
                   (~s.deq.rdy & s.full.out)


  def line_trace( s ):
    return s.buf.line_trace()
