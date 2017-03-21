from pymtl import *
from collections import deque
from pclib.valrdy import valrdy_to_str
from ValRdyBundle import ValRdyBundle

class TestSink( Updates ):

  def __init__( s, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!" 

    s.answer = deque( answer )
    s.in_ = ValRdyBundle()

    @s.update
    def up_sink():
      s.in_.rdy = len(s.answer) > 0

      if s.in_.val:
        ref = s.answer.popleft()
        ans = s.in_.msg[0]

        assert ref == ans or ref == "?", "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.answer

  def line_trace( s ):
    return s.in_.line_trace()

class StreamSink( Updates ):

  def __init__( s ):
    s.in_ = ValRdyBundle()

    @s.update_on_edge
    def up_sink():
      s.in_.rdy = 1

  def line_trace( s ):
    return s.in_.line_trace()
