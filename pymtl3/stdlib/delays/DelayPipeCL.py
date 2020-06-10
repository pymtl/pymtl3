#=========================================================================
# DelayPipeCL.py
#=========================================================================
# This delay pipe models a inelasic pipeline queue with enq/deq interfaces
#
# Author : Shunning Jiang
# Date   : May 7, 2018

from collections import deque

from pymtl3 import *
from pymtl3.extra import clone_deepcopy

# This delay pipe is for cycle-level performance modeling purpose

class DelayPipeDeqCL( Component ):

  @non_blocking( lambda s: s.pipeline[0] is None )
  def enq( s, msg ):
    assert s.pipeline[0] is None
    s.pipeline[0] = clone_deepcopy(msg)

  @non_blocking( lambda s: s.pipeline[-1] is not None )
  def deq( s ):
    ret = s.pipeline[-1]
    s.pipeline[-1] = None
    return ret

  @non_blocking( lambda s: True )
  def peek( s ):
    assert s.pipeline[-1] is not None
    return s.pipeline[-1]

  def construct( s, delay=5, trace_len=0 ):

    s.delay = delay

    s.trace_len = trace_len

    if delay == 0: # This is essentially a bypass queue
      s.pipeline = [ None ]

      s.add_constraints(
        M(s.enq) < M(s.deq),  # bypass behavior
      )

    else: # delay >= 1, pipe behavior
      s.pipeline = deque( [None]*(delay+1), maxlen=(delay+1) )

      @update_once
      def up_delay():
        if s.pipeline[-1] is None:
          s.pipeline.rotate()

      # Model decoupled pipe behavior to cut cyclic dependencies.
      # Basically no matter in what order s.deq and s.enq are called,
      # the outcomes are the same as long as up_delay is called before
      # both of them.

      # NOTE THAT this up_delay affects ready signal, we need to mark it
      # before enq.rdy
      s.add_constraints(
        U(up_delay) < M(s.peek),
        U(up_delay) < M(s.deq),
        U(up_delay) < M(s.deq.rdy),
        U(up_delay) < M(s.enq),
        U(up_delay) < M(s.enq.rdy),
      )

  def line_trace( s ):
    return "[{}]".format( "".join( [ " " if x is None else "*" for x in list(s.pipeline)[:-1] ] ) )

class DelayPipeSendCL( Component ):

  def enq_pipe( s, msg ):
    assert s.pipeline[0] is None
    s.pipeline[0] = clone_deepcopy(msg)

  def enq_rdy_pipe( s ):
    return s.pipeline[0] is None

  def construct( s, delay=5 ):

    s.send = CallerIfcCL()

    s.delay = delay

    if delay == 0: # combinational behavior
      s.enq = CalleeIfcCL()
      connect( s.enq, s.send )

    else: # delay >= 1, pipe behavior
      s.enq = CalleeIfcCL( Type=None, method=s.enq_pipe, rdy=s.enq_rdy_pipe )
      s.pipeline = deque( [None]*delay, maxlen=delay )

      @update_once
      def up_delay():
        if s.pipeline[-1] is not None:
          if s.send.rdy():
            s.send( s.pipeline[-1] )
            s.pipeline[-1] = None
            s.pipeline.rotate()
        else:
          s.pipeline.rotate()

      s.add_constraints(
        M(s.enq) > U(up_delay),  # pipe behavior
        M(s.enq.rdy) > U(up_delay),  # pipe behavior
      )

  def line_trace( s ):
    if s.delay > 0:
      return "[{}]".format( "".join( [ " " if x is None else "*" for x in s.pipeline ] ) )
    return ""
