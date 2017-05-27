from pymtl import *
from collections import deque
from pclib.valrdy import valrdy_to_str

class TestBasicSink( UpdateConnect ):

  def __init__( s, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!" 

    s.answer = deque( answer )
    s.in_ = InVPort(int)

    @s.update
    def up_sink():
      if not s.answer:
        assert False, "Simulation has ended"
      else:
        ref = s.answer.popleft()
        ans = s.in_

        assert ref == ans or ref == "*", "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.answer

  def line_trace( s ):
    return "%s" % s.in_

class TestSink( UpdateConnect ):

  def __init__( s, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!" 

    s.answer = deque( answer )
    s.msg = InVPort(int)
    s.en  = InVPort(int)
    s.rdy = OutVPort(int)

    @s.update
    def up_sink_rdy():
      s.rdy = len(s.answer) > 0

    @s.update
    def up_sink_rdy():
      s.rdy = len(s.answer) > 0
      if s.en:
        ref = s.answer.popleft()
        ans = s.msg

        assert ref == ans or ref == "*", "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.answer

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy )
