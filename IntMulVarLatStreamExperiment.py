from pymtl import *
from IntMulVarLatUp import IntMulVarLat
from pclib.update import StreamSource, StreamSink

class TestHarness( Updates ):

  def __init__( s ):

    s.src  = StreamSource( 2 )
    s.imul = IntMulVarLat()
    s.sink = StreamSink()

    s.src.val    |= s.imul.req_val
    s.src.rdy    |= s.imul.req_rdy
    s.src.msg[0] |= s.imul.req_msg_a
    s.src.msg[1] |= s.imul.req_msg_b

    s.sink.val   |= s.imul.resp_val
    s.sink.rdy   |= s.imul.resp_rdy
    s.sink.msg   |= s.imul.resp_msg

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.imul.line_trace()+" >>> "+s.sink.line_trace()

A = TestHarness()
A.elaborate()
A.print_schedule()

for x in xrange(10000000):
  A.cycle()
  # print A.line_trace()
