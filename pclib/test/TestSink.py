from pymtl import *
from collections import deque
from pclib.ifcs  import valrdy_to_str, ValRdyBundle, EnRdyBundle

class TestSinkValRdy( Updates ):

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

class StreamSinkValRdy( Updates ):

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

    s.recv = EnRdyBundle( Type )

    s.ts = 0
    @s.update
    def up_sink_rdy():
      s.ts = (s.ts + 1) % accept_interval
      s.recv.rdy = (s.ts == 0) & (len(s.answer) > 0)

    @s.update
    def up_sink_en():
      if s.recv.en:
        ref = s.answer.popleft()
        ans = s.recv.msg
        assert ref == ans, "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.answer

  def line_trace( s ):
    return s.recv.line_trace()

class TestSinkCL( MethodsConnection ):

  def __init__( s, Type, answer, accept_interval=1 ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!"
    s.answer = deque( answer )
    s.accept_interval = accept_interval

    s.ts  = 0
    s.msg = ".".center(4)

  def recv( s, msg ):
    s.msg = msg
    ref = s.answer.popleft()
    assert ref == msg, "Expect %s, get %s instead" % (ref, msg)

  def recv_rdy( s ):
    s.ts = (s.ts + 1) % s.accept_interval
    return s.ts == 0 & (len(s.answer) > 0)

  def done( s ):
    return not s.answer

  def line_trace( s ): # called once per cycle
    trace = str(s.msg)
    s.msg = ".".center(4) if len(s.answer) > 0 else " ".center(4)
    return "{:>4s}".format( trace )

class TestSinkCL( MethodsConnection ):

  def __init__( s, Type, answer=[] ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!"
    s.answer = deque( answer )

    s.msg = ".".center(4)

  def recv( s, msg ):
    s.msg = msg
    ref = s.answer.popleft()
    assert ref == msg, "Expect %s, get %s instead" % (ref, msg)

  def recv_rdy( s ):
    return len(s.answer) > 0

  def done( s ):
    return not s.answer

  def line_trace( s ): # called once per cycle
    trace = str(s.msg)
    s.msg = ".".center(4) if len(s.answer) > 0 else " ".center(4)
    return "{:>4s}".format( trace )

from pclib.cl import RandomDelay

class TestSink( MethodsConnection ):

  def __init__( s, Type, answer=[], max_delay=0 ):
    s.recv     = MethodPort()
    s.recv_rdy = MethodPort()

    s.sink = TestSinkCL( Type, answer )

    if not max_delay:
      s.has_delay = False
      s.sink.recv     |= s.recv
      s.sink.recv_rdy |= s.recv_rdy
    else:
      s.has_delay = True
      s.rdelay    = RandomDelay( max_delay )

      s.recv     |= s.rdelay.recv
      s.recv_rdy |= s.rdelay.recv_rdy

      s.rdelay.send     |= s.sink.recv
      s.rdelay.send_rdy |= s.sink.recv_rdy

  def done( s ):
    return s.sink.done()

  def line_trace( s ):
    return "{} {}".format( s.rdelay.line_trace() if s.has_delay else "",
                          s.sink.line_trace() )
