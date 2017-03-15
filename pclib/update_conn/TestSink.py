from pymtl import *
from collections import deque

class TestSink( UpdatesConnection ):

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

    s.add_constraints(
      WR(s.in_) < U(up_sink), # model wire behavior
    )

  def done( s ):
    return not s.answer

  def line_trace( s ):
    return "%s" % s.in_
