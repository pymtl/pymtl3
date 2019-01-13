from pymtl import *
from random import Random
from collections import deque

# Recv side has a random stall,

class StallDelayCL( ComponentLevel5 ):

  def recv_( s, msg ):
    assert s.pipeline[0] is None
    s.pipeline[0] = msg

  def recv_rdy_stall_( s ):
    return s.stall_rgen.random() < s.stall_prob and s.pipeline[0] is None

  def recv_rdy_no_stall_( s ):
    return s.pipeline[0] is None

  def construct( s, stall_prob=0.5, delay=5,
                    stall_seed=0x1 ):

    s.send     = CallerPort()
    s.send_rdy = CallerPort()

    s.recv     = CalleePort( s.recv_ )
    s.recv_rdy = CalleePort( s.recv_rdy_no_stall_ if stall_prob == 0 else \
                             s.recv_rdy_stall_ )

    s.stall_prob = stall_prob
    s.delay      = delay
    s.stall_rgen = Random( stall_seed ) # Separate randgen for each injector

    if delay == 0:
      s.pipeline = [ None ]

      @s.update
      def up_no_delay():
        if s.pipeline[0] is not None and s.send_rdy():
          s.send( s.pipeline[0] )
          s.pipeline[0] = None

      s.add_constraints(
        M(s.recv)     < U(up_no_delay),  # bypass behavior
        M(s.recv_rdy) < U(up_no_delay),  # recv before update
      )

    else:
      s.pipeline = deque( [None]*delay, maxlen=delay )

      @s.update
      def up_delay():

        if s.pipeline[-1] is not None:
          if s.send_rdy():
            s.send( s.pipeline[-1] )
            s.pipeline.rotate()
            s.pipeline[0] = None
        else:
          s.pipeline.rotate()

      s.add_constraints(
        M(s.recv)     > U(up_delay),  # pipe behavior
        M(s.recv_rdy) > U(up_delay),  # recv after update
      )

  def line_trace( s ):
    return ""
