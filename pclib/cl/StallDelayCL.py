from pymtl import *
from random import Random
from collections import deque


# This stall delay is for testing purpose
# Recv side has a random stall

class StallDelayCL( ComponentLevel5 ):

  def recv_delay_( s, msg ):
    assert s.entry is None
    s.entry     = msg
    s.countdown = s.delay

  def recv_no_delay_( s, msg ):
    assert s.entry is None
    s.entry = msg

  def recv_rdy_stall_( s ):
    return s.stall_rgen.random() < s.stall_prob and s.entry is None

  def recv_rdy_no_stall_( s ):
    return s.entry is None

  def construct( s, stall_prob=0.5, delay=5,
                    stall_seed=0x1 ):

    s.send     = CallerPort()
    s.send_rdy = CallerPort()

    s.recv     = CalleePort( s.recv_no_delay_ if delay == 0 else \
                             s.recv_delay_ )
    s.recv_rdy = CalleePort( s.recv_rdy_no_stall_ if stall_prob == 0 else \
                             s.recv_rdy_stall_ )

    s.stall_prob = stall_prob
    s.delay      = delay
    s.stall_rgen = Random( stall_seed ) # Separate randgen for each injector

    s.v = None

    if delay == 0:
      s.entry = None

      @s.update
      def up_no_delay():
        s.v = None
        if s.entry is not None and s.send_rdy():
          s.v = s.entry
          s.send( s.entry )
          s.entry = None

      s.add_constraints(
        M(s.recv)     < U(up_no_delay),  # bypass behavior
        M(s.recv_rdy) < U(up_no_delay),  # recv before update
      )

    else:
      s.entry = None
      s.countdown = 0

      @s.update
      def up_delay():
        s.v = None
        if s.entry is not None and s.countdown <= 0 and s.send_rdy():
          s.v = s.entry
          s.send( s.entry )
          s.entry = None
          s.countdown = 0
        else:
          s.countdown -= 1

      s.add_constraints(
        M(s.recv)     > U(up_delay),  # pipe behavior
        M(s.recv_rdy) > U(up_delay),  # recv after update
      )

  def line_trace( s ):
    # TODO figure out how to dynamically figure out trace width
    return "{}".format( "" if s.v is None else str(s.v) ).ljust( 30 )

# This delay pipe is for cycle-level performance modeling purpose

class DelayPipeCL( ComponentLevel5 ):

  def recv_( s, msg ):
    assert s.pipeline[0] is None
    s.pipeline[0] = msg

  def recv_rdy_( s ):
    return s.pipeline[0] is None

  def construct( s, delay=5 ):

    s.send     = CallerPort()
    s.send_rdy = CallerPort()

    s.recv     = CalleePort( s.recv_ )
    s.recv_rdy = CalleePort( s.recv_rdy_ )

    s.delay = delay

    s.v = None

    if delay == 0:
      s.pipeline = [ None ]

      @s.update
      def up_no_delay():
        s.v = None
        if s.pipeline[0] is not None and s.send_rdy():
          s.v = s.pipeline[0]
          s.send( s.pipeline[0] )
          s.pipeline[0] = None

      s.add_constraints(
        M(s.recv)     < U(up_no_delay),  # bypass behavior
        M(s.recv_rdy) < U(up_no_delay),  # recv before update
      )

    else: # delay >= 1, pipe behavior
      s.pipeline = deque( [None]*delay, maxlen=delay )

      @s.update
      def up_delay():
        s.v = None
        if s.pipeline[-1] is not None:
          if s.send_rdy():
            s.v = s.pipeline[-1]
            s.send( s.pipeline[-1] )
            s.pipeline[-1] = None
            s.pipeline.rotate()
        else:
          s.pipeline.rotate()

      s.add_constraints(
        M(s.recv)     > U(up_delay),  # pipe behavior
        M(s.recv_rdy) > U(up_delay),  # recv after update
      )

  def line_trace( s ):
    # TODO figure out how to dynamically figure out trace width
    return "{}".format( "" if s.v is None else str(s.v) ).ljust( 30 )
