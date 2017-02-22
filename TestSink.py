from pymtl_v3 import *
from collections import deque

class TestSink( Updates ):

  def __init__( s, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!" 

    s.answer = deque( answer )
    s.in_ = 0

    @s.update
    def up_sink():
      if not s.answer:
        assert False, "Simulation has ended"
      else:
        ref = s.answer.popleft()
        ans = s.in_

        assert ref == ans or ref == "?", "Expect %s, get %s instead" % (ref, ans)

  def line_trace( s ):
    return "%s" % s.in_
