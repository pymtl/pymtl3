from pymtl import *
from collections import deque
from pclib.ifcs  import valrdy_to_str, ValRdyBundle, EnRdyBundle
from pclib.ifcs  import EnqIfcFL, EnqIfcCL, EnqIfcRTL

class TestSinkValRdy( UpdatesImpl ):

  def __init__( s, Type, msgs ):
    assert type(msgs) == list, "TestSink only accepts a list of outputs!"
    s.msgs = deque( msgs )

    s.in_    = ValRdyBundle( Type )

    @s.update
    def up_sink():
      s.in_.rdy = len(s.msgs) > 0

      if s.in_.val and s.in_.rdy:
        ref = s.msgs.popleft()
        ans = s.in_.msg

        assert ref == ans, "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.msgs

  def line_trace( s ):
    return s.in_.line_trace()

class StreamSinkValRdy( UpdatesImpl ):

  def __init__( s, Type ):
    s.in_ = ValRdyBundle( Type )

    @s.update_on_edge
    def up_sink():
      s.in_.rdy = 1

  def line_trace( s ):
    return s.in_.line_trace()

class TestSinkEnRdy( UpdatesImpl ):

  def __init__( s, Type, msgs, accept_interval=1 ):
    assert type(msgs) == list, "TestSink only accepts a list of outputs!"
    s.msgs = deque( msgs )

    s.recv = EnqIfcRTL( Type )

    s.ts = 0
    @s.update
    def up_sink_rdy():
      s.ts = (s.ts + 1) % accept_interval
      s.recv.rdy = (s.ts == 0) & (len(s.msgs) > 0)

    @s.update
    def up_sink_en():
      if s.recv.en:
        ref = s.msgs.popleft()
        ans = s.recv.msg
        assert ref == ans, "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.msgs

  def line_trace( s ):
    return s.recv.line_trace()

class TestSinkFL( MethodsConnection ):

  def __init__( s, Type, msgs=[] ):
    assert type(msgs) == list, "TestSink only accepts a list of outputs!"
    s.msgs = deque( msgs )

    s.recv = EnqIfcFL( Type )
    s.recv.enq |= s.enq_

    s.msg = "."
    s.tracelen = len( str( Type() ) )

  def enq_( s, msg ):
    assert s.msgs
    s.msg = msg
    ref = s.msgs.popleft()
    assert ref == msg, "Expect %s, get %s instead" % (ref, msg)

  def done( s ):
    return not s.msgs

  def line_trace( s ): # called once per cycle
    trace = str(s.msg)
    s.msg = "." if s.msgs else " "
    return "{:>4s}".format( trace ).center( s.tracelen )

class TestSinkCL( MethodsConnection ):

  def __init__( s, Type, msgs=[] ):
    assert type(msgs) == list, "TestSink only accepts a list of outputs!"
    s.msgs = deque( msgs )

    s.recv = EnqIfcCL( Type )
    s.recv.enq |= s.recv_
    s.recv.rdy |= s.recv_rdy_

    s.msg = "."
    s.tracelen = len( str( Type() ) )

  def recv_( s, msg ):
    s.msg = msg
    ref = s.msgs.popleft()
    assert ref == msg, "Expect %s, get %s instead" % (ref, msg)

  def recv_rdy_( s ):
    return len(s.msgs) > 0

  def done( s ):
    return not s.msgs

  def line_trace( s ): # called once per cycle
    trace = str(s.msg)
    s.msg = "." if s.msgs else " "
    return "{:>4s}".format( trace ).center( s.tracelen )

from pclib.cl import RandomDelay

class TestSink( MethodsConnection ):

  def __init__( s, Type, msgs=[], max_delay=0 ):
    s.recv = EnqIfcCL( Type )

    s.sink = TestSinkCL( Type, msgs )

    if not max_delay:
      s.has_delay = False
      s.sink.recv |= s.recv
    else:
      s.has_delay = True
      s.rdelay    = RandomDelay( max_delay )

      s.recv        |= s.rdelay.recv
      s.rdelay.send |= s.sink.recv

  def done( s ):
    return s.sink.done()

  def line_trace( s ):
    return "{}{}".format( "{} ".format( s.rdelay.line_trace() ) if s.has_delay else "",
                          s.sink.line_trace() )
