from pymtl import *
from collections import deque
from StallDelayCL import StallDelayCL

# This simple source doesn't have any constraints or such

class TestSimpleSource( ComponentLevel6 ):

  def construct( s, msgs ):
    s.msgs = deque( msgs )

    s.req     = CallerPort()
    s.req_rdy = CallerPort()

    s.v = None
    s.trace_len = len(str(msgs[0]))

    @s.update
    def up_src():
      s.v = None
      if s.req_rdy() and s.msgs:
        s.v = s.msgs.popleft()
        s.req( s.v )

  def done( s ):
    return not s.msgs

  def line_trace( s ):
    return "{}".format( "" if s.v is None else str(s.v) ).ljust( s.trace_len )

# This source includes a random stall delay

class TestSource( ComponentLevel6 ):

  def construct( s, msgs, stall_prob=0, delay=1 ):

    s.req     = CallerPort()
    s.req_rdy = CallerPort()

    s.src = TestSimpleSource( msgs )

    # Feed src's msg into stall_delay's recv port

    s.stall_delay = StallDelayCL( stall_prob, delay )(
      recv = s.src.req, recv_rdy = s.src.req_rdy,
      send = s.req, send_rdy = s.req_rdy,
    )

  def done( s ):
    return s.src.done()

  def line_trace( s ):
    return s.stall_delay.line_trace()
