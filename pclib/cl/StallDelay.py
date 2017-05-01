from pymtl import *
from collections import deque
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

class RandomDelay( MethodsConnection ):

  def __init__( s, max_delay=5, seed=0x3 ):
    s.send     = MethodPort()
    s.send_rdy = MethodPort()

    s.rgen      = Random( seed ) # Separate randgen for each injector
    s.randnum   = 0
    s.max_delay = max_delay
    s.buf       = (False, None)
    s.counter   = 0

    @s.update
    def up_delay():
      if s.send_rdy():
        if s.counter == 0:
          frontier = s.buf
          if frontier[0]:
            s.send( frontier[1] )
            s.buf = (False, None)
        else:
          s.counter -= 1
          

    s.add_constraints(
      M(s.recv)     < U(up_delay), # bypass behavior, recv < send
      M(s.recv_rdy) < U(up_delay),
    )

  def recv( s, msg ):
    s.buf  = (True, msg)
    s.counter = s.rgen.randint(0, s.max_delay)

  def recv_rdy( s ):
    return not s.buf[0]

  def line_trace( s ):
    return str(s.counter+1) if s.buf[0] else ' '

class PipelinedDelay( MethodsConnection ):

  def __init__( s, delay=5, seed=0x3 ):
    s.send     = MethodPort()
    s.send_rdy = MethodPort()

    s.delay = deque( [ (False, None) ] * max(delay,1), maxlen=max(delay,1) )

    @s.update
    def up_delay():
      if s.send_rdy():
        frontier = s.delay[-1]
        if frontier[0]:
          s.send( frontier[1] )
          s.delay[-1] = (False, None)
        s.delay.rotate()

    if delay > 0:
      s.add_constraints(
        U(up_delay) < M(s.recv), # pipe behavior, send < recv
        U(up_delay) < M(s.recv_rdy),
      )
    else:
      s.add_constraints(
        M(s.recv)     < U(up_delay), # bypass behavior, recv < send
        M(s.recv_rdy) < U(up_delay),
      )

  def recv( s, msg ):
    s.delay[0] = (True, msg)

  def recv_rdy( s ):
    return not s.delay[0][0]

  def line_trace( s ):
    return ''.join( [ '*' if x[0] else ' ' for x in s.delay ] )
