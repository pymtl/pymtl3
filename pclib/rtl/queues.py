from pymtl import *
from pclib.rtl import Reg, RegEn, Mux
from pclib.ifcs   import EnqIfcRTL, DeqIfcRTL

# The reason why we have 3 update blocks for pipe queue:
# start: deq.rdy = full.out (queue, up1)
# --> deq.en (receiver AND deq.rdy with valid expression)
# --> enq.rdy (queue, up2)
# --> enq.en (sender AND enq.rdy with valid expression)
# --> buf.en/full.in (takes enq.en and deq.en into account, up3)

class PipeQueue1RTL( ComponentLevel3 ):

  def __init__( s, Type ):
    s.enq = EnqIfcRTL( Type )
    s.deq = DeqIfcRTL( Type )

    s.buf  = RegEn( Type )( out = s.deq.msg, in_ = s.enq.msg )
    s.full = Reg( Bits1 )

    @s.update
    def up_pipeq_set_deq_rdy():
      s.deq.rdy =  s.full.out

    @s.update
    def up_pipeq_set_enq_rdy():
      s.enq.rdy = ~s.full.out | s.deq.en

    @s.update
    def up_pipeq_full():
      s.buf.en   = s.enq.en
      s.full.in_ = s.enq.en | (s.full.out & ~s.deq.en)

  def line_trace( s ):
    return s.buf.line_trace()

# The reason why we have 3 update blocks for bypass queue:
# start: enq.rdy = full.out (queue, up1)
# --> enq.en  (sender AND enq.rdy with valid expression)
# --> deq.rdy (queue, up2)
# --> deq.en  (receiver AND deq.rdy with valid expression)
# --> buf.en/full.in (takes enq.en and deq.en into account, up3)

class BypassQueue1RTL( ComponentLevel3 ):

  def __init__( s, Type ):
    s.enq = EnqIfcRTL( Type )
    s.deq = DeqIfcRTL( Type )

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
    def up_bypq_set_deq_rdy():
      s.deq.rdy = s.full.out | s.enq.en # if enq is enabled deq must be rdy

    @s.update
    def up_bypq_full():
      # enable buf <==> receiver marks deq.en=0 even if it sees deq.rdy=1
      s.buf.en   = ~s.deq.en &  s.enq.en
      s.full.in_ = ~s.deq.en & (s.enq.en | s.full.out)

  def line_trace( s ):
    return s.buf.line_trace()

# The reason why we only have 2 update blocks for normal queue:
# start: enq.rdy = full.out and also deq.rdy = ~full.out (queue, up1)
# --> enq.en and deq.en (sender and receiver do stuff)
# --> buf.en/full.in (takes enq.en and deq.en into account, up2)

class NormalQueue1RTL( ComponentLevel3 ):

  def __init__( s, type_ ):
    s.enq = EnqIfcRTL( type_ )
    s.deq = DeqIfcRTL( type_ )

    s.buf  = RegEn( type_ )( out = s.deq.msg, in_ = enq.msg )
    s.full = Reg( Bits1 )

    @s.update
    def up_normq_set_both_rdy():
      s.enq.rdy = ~s.full.out
      s.deq.rdy =  s.full.out

    @s.update
    def up_normq_full():
      s.buf.en   =  s.enq.en
      s.full.in_ = ~s.deq.en & (s.enq.en | s.full.out)

  def line_trace( s ):
    return s.buf.line_trace()
