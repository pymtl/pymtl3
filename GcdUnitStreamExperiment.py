from pymtl import *
from GcdUnitUp import GcdUnit
from pclib.update import StreamSource, StreamSink

class TestHarness( Updates ):

  def __init__( s ):

    s.src  = StreamSource( 2 )
    s.gcd  = GcdUnit()
    s.sink = StreamSink()

    s.gcd.req_val   |= s.src.val
    s.gcd.req_msg_a |= s.src.msg[0]
    s.gcd.req_msg_b |= s.src.msg[1]
    s.src.rdy       |= s.gcd.req_rdy

    s.sink.val      |= s.gcd.resp_val
    s.gcd.resp_rdy  |= s.sink.rdy
    s.sink.msg      |= s.gcd.resp_msg

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.gcd.line_trace()+" >>> "+s.sink.line_trace()

A = TestHarness()
A.elaborate()
A.print_schedule()

for x in xrange(10000000):
  A.cycle()
  # print A.line_trace()
