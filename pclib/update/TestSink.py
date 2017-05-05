from pymtl import *
from collections import deque
from pclib.valrdy import valrdy_to_str

class TestSink( UpdatesImpl ):

  def __init__( s, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!" 

    s.answer = deque( answer )
    s.in_ = ValuePort(int)

    @s.update
    def up_sink():
      if not s.answer:
        assert False, "Simulation has ended"
      else:
        ref = s.answer.popleft()
        ans = s.in_

        assert ref == ans or ref == "?", "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.answer

  def line_trace( s ):
    return "%s" % s.in_

class TestSinkValRdy( UpdatesImpl ):

  def __init__( s, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!" 

    s.answer = deque( answer )
    s.msg = ValuePort(int)
    s.val = ValuePort(int)
    s.rdy = ValuePort(int)

    @s.update
    def up_sink():
      s.rdy = len(s.answer) > 0

      if s.val:
        ref = s.answer.popleft()
        ans = s.msg

        assert ref == ans or ref == "?", "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.answer

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy )

class StreamSink( UpdatesImpl ):

  def __init__( s ):

    s.msg = ValuePort(int)
    s.val = ValuePort(int)
    s.rdy = ValuePort(int)

    @s.update_on_edge
    def up_sink():
      s.rdy = 1

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy )
