from pymtl import *
from collections import deque
from pclib.ifcs  import valrdy_to_str, ValRdyBundle, EnRdyBundle
from pclib.ifcs  import EnqIfcCL, EnqIfcRTL, DeqIfcFL


class TestSourceValRdy( UpdatesImpl ):

  def __init__( s, Type, msgs ):
    assert type(msgs) == list, "TestSrc only accepts a list of inputs!"
    s.msgs  = deque( msgs ) # deque.popleft() is faster

    s.default = Type()
    s.out     = ValRdyBundle( Type )

    @s.update_on_edge
    def up_src():
      if s.out.rdy and s.msgs:  s.msgs.popleft()
      s.out.val = len(s.msgs) > 0
      s.out.msg = s.default if not s.msgs else s.msgs[0]

  def done( s ):
    return not s.msgs

  def line_trace( s ):
    return s.out.line_trace()

class StreamSourceValRdy( UpdatesImpl ):

  def __init__( s, Type ):
    s.out = ValRdyBundle( Type )
    s.ts  = 0

    @s.update_on_edge
    def up_src():
      s.out.msg = Bits64( ((s.ts+95827*(s.ts&1))<<32) + s.ts+(19182)*(s.ts&1) )
      s.out.val = 1
      s.ts += 1

  def done( s ):
    return not s.msgs

  def line_trace( s ):
    return s.out.line_trace()

class TestSourceEnRdy( UpdatesImpl ):

  def __init__( s, Type, msgs = [] ):
    assert type(msgs) == list, "TestSrc only accepts a list of inputs!"
    s.msgs = deque( msgs ) # deque.popleft() is faster

    s.default = Type()
    s.send = EnqIfcRTL( Type )

    @s.update
    def up_src():
      s.send.en  = Bits1( len(s.msgs) > 0 ) & s.send.rdy
      s.send.msg = s.default if not s.msgs else s.msgs[0]

      if s.send.en and s.msgs:
        s.msgs.popleft()

  def done( s ):
    return not s.msgs

  def line_trace( s ):
    return s.send.line_trace()

class TestSourceFL( MethodsAdapt ):

  def __init__( s, Type, msgs = [] ):
    assert type(msgs) == list, "TestSrc only accepts a list of inputs!"
    s.msgs = deque( msgs ) # deque.popleft() is faster

    s.send      = DeqIfcFL( Type )
    s.send.deq |= s.deq_

    s.sended   = "#"
    s.tracelen = len( str( Type() ) )

  def deq_( s ):
    assert s.msgs
    s.sended = x = s.msgs.popleft()
    return x

  def done( s ):
    return not s.msgs

  def line_trace( s ):
    trace = str(s.sended)
    s.sended = "#" if s.msgs else " "
    return "{:>4s}".format( trace ).center( s.tracelen )

class TestSourceCL( MethodsConnection ):

  def __init__( s, Type, msgs = [] ):
    assert type(msgs) == list, "TestSrc only accepts a list of inputs!"
    s.msgs = deque( msgs ) # deque.popleft() is faster

    s.send = EnqIfcCL( Type )

    s.sended   = "#"
    s.tracelen = len( str( Type() ) )

    @s.update
    def up_src():
      if s.send.rdy() and len(s.msgs) > 0:
        s.sended = s.msgs.popleft()
        s.send.enq( s.sended )

  def done( s ):
    return not s.msgs

  def line_trace( s ):
    trace = str(s.sended)
    s.sended = "#" if s.msgs else " "
    return "{:>4s}".format( trace ).center( s.tracelen )

from pclib.cl import RandomDelay

class TestSource( MethodsConnection ):

  def __init__( s, Type, msgs=[], max_delay=0 ):
    s.send = EnqIfcCL( Type )

    s.src = TestSourceCL( Type, msgs )

    if not max_delay:
      s.has_delay = False
      s.src.send |= s.send
    else:
      s.has_delay = True
      s.rdelay    = RandomDelay( max_delay )

      s.src.send    |= s.rdelay.recv
      s.rdelay.send |= s.send

  def done( s ):
    return s.src.done()

  def line_trace( s ):
    return "{}{}".format( s.src.line_trace(),
                          " {}".format( s.rdelay.line_trace() ) if s.has_delay else "" )
