from pymtl import *
from collections import deque
from pclib.ifcs  import valrdy_to_str, ValRdyBundle, EnRdyBundle

class TestSink( Updates ):

  def __init__( s, Type, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!" 
    s.answer = deque( answer )

    s.in_    = ValRdyBundle( Type )

    @s.update
    def up_sink():
      s.in_.rdy = len(s.answer) > 0

      if s.in_.val and s.in_.rdy:
        ref = s.answer.popleft()
        ans = s.in_.msg

        assert ref == ans, "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.answer

  def line_trace( s ):
    return s.in_.line_trace()

class StreamSink( Updates ):

  def __init__( s, Type ):
    s.in_ = ValRdyBundle( Type )

    @s.update_on_edge
    def up_sink():
      s.in_.rdy = 1

  def line_trace( s ):
    return s.in_.line_trace()

class TestSinkEnRdy( Updates ):

  def __init__( s, Type, answer, accept_interval=1 ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!"
    s.answer = deque( answer )

    s.in_ = EnRdyBundle( Type )

    s.ts = 0
    @s.update
    def up_sink():
      s.ts = (s.ts + 1) % accept_interval
      s.in_.en = (s.ts == 0) & s.in_.rdy & (len(s.answer) > 0)

    @s.update
    def up_sink_faq():
      if s.in_.en:
        ref = s.answer.popleft()
        ans = s.in_.msg
        assert ref == ans or ref == "?", "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.answer

  def line_trace( s ):
    return s.in_.line_trace()
