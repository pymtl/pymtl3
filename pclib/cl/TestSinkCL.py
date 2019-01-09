from pymtl import *
from collections import deque

# This simple sink does have a buffer at input

class TestSinkError( Exception ):
  pass

class TestSimpleSink( ComponentLevel5 ):

  def resp_rdy_( s ):
    return s.idx < len(s.msgs)

  def resp_( s, v ):
    s.queue.appendleft(v)

  def construct( s, msgs ):
    s.msgs  = list( msgs )
    s.queue = deque( maxlen=1 )
    s.idx  = 0

    s.resp     = CalleePort( s.resp_ )
    s.resp_rdy = CalleePort( s.resp_rdy_ )

    s.v = None
    s.trace_len = len(str(msgs[0]))

    @s.update
    def up_sink():
      s.v = None

      if s.queue:
        msg = s.queue.pop()
        s.v = msg

        if s.idx >= len(s.msgs):
          raise TestSinkError( """
  The test sink received a message that !
  - sink name    : {}
  - msg number   : {}
  - actual msg   : {}
  """.format( s, s.idx, msg )
          )
        else:
          ref = s.msgs[ s.idx ]
          s.idx += 1

          if msg != ref:
            raise TestSinkError( """
  The test sink received an incorrect message!
  - sink name    : {}
  - msg number   : {}
  - expected msg : {}
  - actual msg   : {}
  """.format( s, s.idx, ref, msg )
          )

    s.add_constraints(
      U(up_sink) < M(s.resp_    ), # pipe behavior
      U(up_sink) < M(s.resp_rdy_),
    )

  def done( s ):
    return s.idx >= len(s.msgs)

  def line_trace( s ):
    return "{}".format( "" if s.v is None else str(s.v) ).ljust( s.trace_len )
