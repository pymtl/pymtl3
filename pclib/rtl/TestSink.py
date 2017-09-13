from pymtl import *
from collections import deque
from pclib.ifcs   import InValRdyIfc
from pclib.valrdy import valrdy_to_str

class TestBasicSink( ComponentLevel3 ):

  def __init__( s, Type, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!" 

    s.answer = deque( answer )
    s.in_ = InVPort( Type )

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

class TestSinkValRdy( ComponentLevel3 ):

  def __init__( s, Type, msgs ):
    assert type(msgs) == list, "TestSink only accepts a list of outputs!"
    s.msgs = deque( msgs )

    s.in_    = InValRdyIfc( Type )

    @s.update
    def up_sink():
      s.in_.rdy = Bits1( len(s.msgs) > 0 )

      if s.in_.val and s.in_.rdy:
        ref = s.msgs.popleft()
        ans = s.in_.msg

        assert ref == ans, "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.msgs

  def line_trace( s ):
    return s.in_.line_trace()

class TestSink( ComponentLevel3 ):

  def __init__( s, Type, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!" 

    s.answer = deque( answer )
    s.msg = InVPort(int)
    s.en  = InVPort(int)
    s.rdy = OutVPort(int)

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
