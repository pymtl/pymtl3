from pymtl import *
from collections import deque
from pclib.ifcs  import valrdy_to_str, ValRdyBundle, EnRdyBundle

class TestSourceValRdy( Updates ):

  def __init__( s, Type, input_ ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!"
    s.input_  = deque( input_ ) # deque.popleft() is faster

    s.default = Type()
    s.out     = ValRdyBundle( Type )

    @s.update_on_edge
    def up_src():
      if s.out.rdy and s.input_:  s.input_.popleft()
      s.out.val = len(s.input_) > 0
      s.out.msg = s.default if not s.input_ else s.input_[0]

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return s.out.line_trace()

class StreamSourceValRdy( Updates ):

  def __init__( s, Type ):
    s.out = ValRdyBundle( Type )
    s.ts  = 0

    @s.update_on_edge
    def up_src():
      s.out.msg = Bits64( ((s.ts+95827*(s.ts&1))<<32) + s.ts+(19182)*(s.ts&1) )
      s.out.val = 1
      s.ts += 1

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return s.out.line_trace()

class TestSourceEnRdy( Updates ):

  def __init__( s, Type, input_ = [] ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!"
    s.input_ = deque( input_ ) # deque.popleft() is faster

    s.default = Type()
    s.send = EnRdyBundle( Type )

    @s.update
    def up_src():
      s.send.en  = Bits1( len(s.input_) > 0 ) & s.send.rdy
      s.send.msg = s.default if not s.input_ else s.input_[0]

      if s.send.en and s.input_:
        s.input_.popleft()

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return s.send.line_trace()

class TestSourceCL( MethodsConnection ):

  def __init__( s, Type, input_ = [] ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!"
    s.input_ = deque( input_ ) # deque.popleft() is faster

    s.send     = MethodPort()
    s.send_rdy = MethodPort()

    s.sended   = "#"
    s.tracelen = len( str( Type() ) )

    @s.update
    def up_src():
      if s.send_rdy() and len(s.input_) > 0:
        s.send( s.input_[0] )
        s.sended = s.input_[0]
        s.input_.popleft()

  def done( s ):
    return not s.input_

  def line_trace( s ):
    trace = str(s.sended)
    s.sended = "#" if s.input_ else " "
    return "{:>4s}".format( trace ).center( s.tracelen )

from pclib.cl import RandomDelay

class TestSource( MethodsConnection ):

  def __init__( s, Type, input_=[], max_delay=0 ):
    s.send     = MethodPort()
    s.send_rdy = MethodPort()

    s.src    = TestSourceCL( Type, input_ )

    if not max_delay:
      s.has_delay = False
      s.src.send     |= s.send
      s.src.send_rdy |= s.send_rdy
    else:
      s.has_delay = True
      s.rdelay    = RandomDelay( max_delay )

      s.src.send     |= s.rdelay.recv
      s.src.send_rdy |= s.rdelay.recv_rdy

      s.rdelay.send     |= s.send
      s.rdelay.send_rdy |= s.send_rdy

  def done( s ):
    return s.src.done()

  def line_trace( s ):
    return "{}{}".format( s.src.line_trace(),
                          " {}".format( s.rdelay.line_trace() ) if s.has_delay else "" )
