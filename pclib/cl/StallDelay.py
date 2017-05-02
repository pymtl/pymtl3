from pymtl import *
from collections import deque, namedtuple
from random import Random

class RandomStall( MethodsConnection ):

  def __init__( s, stall_prob=0.5, seed=0x3 ):
    s.send     = MethodPort()
    s.send_rdy = MethodPort()

    s.rgen       = Random( seed ) # Separate randgen for each injector
    s.randnum    = 0
    s.stall_prob = stall_prob

  def recv( s, msg ):
    s.send( msg )

  def recv_rdy( s ):
    s.stall = s.rgen.random() > s.stall_prob
    return s.send_rdy() and s.stall

  def line_trace( s ):
    return " " if s.stall else "#"

DelayEntry = namedtuple('DelayEntry', 'val msg')

class RandomDelay( MethodsConnection ):

  def __init__( s, max_delay=5, seed=0x3 ):
    s.send     = MethodPort()
    s.send_rdy = MethodPort()

    s.rgen      = Random( seed ) # Separate randgen for each injector
    s.randnum   = 0
    s.max_delay = max_delay
    s.counter   = 0
    s.buf       = DelayEntry( val=False, msg=None )

    @s.update
    def up_delay():
      if s.send_rdy():
        if s.counter <= 0 and s.buf.val:
          s.send( s.buf.msg )
          s.buf = DelayEntry( val=False, msg=None )
      s.counter -= 1

    s.add_constraints(
      M(s.recv)     < U(up_delay), # bypass behavior, recv < send
      M(s.recv_rdy) < U(up_delay), # since randint=0 ==> combinational
    )

  def recv( s, msg ):
    s.buf = DelayEntry( val=True, msg=msg )
    s.counter = s.rgen.randint(0, s.max_delay)

  def recv_rdy( s ):
    return not s.buf.val

  def line_trace( s ):
    return "({})".format( str(s.counter+1) if s.buf.val else ' ' )

class PipelinedDelay( MethodsConnection ):

  def __init__( s, delay=5, seed=0x3, elastic=False ):
    s.send     = MethodPort()
    s.send_rdy = MethodPort()

    assert delay > 0, "Please conditionally remove this PipelinedDelay if you want delay=0."

    s.delay = deque( [ DelayEntry( val=False, msg=None ) for _ in xrange(delay) ], maxlen=delay )

    if elastic:
      pass
      # TODO implement elastic pipeline
      # @s.update
      # def up_delay():
        # if s.send_rdy():
          # frontier = s.delay[-1]
          # if frontier[0]:
            # s.send( frontier[1] )
            # s.delay[-1] = (False, None)
          # s.delay.rotate()
    else:
      @s.update
      def up_delay():
        if s.send_rdy():
          frontier = s.delay[-1]
          if frontier.val:
            s.send( frontier.msg )
            s.delay[-1] = DelayEntry( val=False, msg=None )
          s.delay.rotate()

    s.add_constraints(
      U(up_delay) < M(s.recv), # pipe behavior, send < recv
      U(up_delay) < M(s.recv_rdy),
    )

  def recv( s, msg ):
    s.delay[0] = DelayEntry( val=True, msg=msg )

  def recv_rdy( s ):
    return not s.delay[0].val

  def line_trace( s ):
    return "({})".format( ''.join( [ '*' if x[0] else ' ' for x in s.delay ] ) )
