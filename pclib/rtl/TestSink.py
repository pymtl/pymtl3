from pymtl import *
from collections import deque
from pclib.ifcs   import InValRdyIfc
from pclib.valrdy import valrdy_to_str

class TestBasicSink( RTLComponent ):

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

class TestSinkValRdy( RTLComponent ):

  def __init__( s, Type, msgs ):
    assert type(msgs) == list, "TestSink only accepts a list of outputs!"

    s.msgs = msgs
    s.sink_msgs = deque( s.msgs )

    s.in_ = InValRdyIfc( Type )

    @s.update_on_edge
    def up_sink():
      if s.reset:
        s.in_.rdy = Bits1( 0 )
        s.sink_msgs = deque( s.msgs )
      else:
        s.in_.rdy = Bits1( len(s.sink_msgs) > 0 )

        if s.in_.val and s.in_.rdy:
          ref = s.sink_msgs.popleft()
          ans = s.in_.msg

          assert ref == ans, "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.sink_msgs

  def line_trace( s ):
    return s.in_.line_trace()

class TestSinkUnorderedValRdy( RTLComponent ):

  def __init__( s, Type, msgs ):
    assert type(msgs) == list, "TestSink only accepts a list of outputs!"
    s.msgs = deque( msgs )
    s.recv = deque()

    s.in_    = InValRdyIfc( Type )

    @s.update_on_edge
    def up_sink():
      s.in_.rdy = len(s.msgs) > 0

      if s.in_.val and s.in_.rdy:
        ans = s.in_.msg

        if ans not in s.msgs:
          if ans in s.recv:
            raise AssertionError( "Message %s arrived twice!"
                                  % ans  )
          else:
            raise AssertionError( "Message %s not found in Test Sink!"
                                  % ans  )

        s.msgs.remove( ans )
        s.recv.append( ans )

  def done( s ):
    return not s.msgs

  def line_trace( s ):
    return s.in_.line_trace()


class TestSink( RTLComponent ):

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


