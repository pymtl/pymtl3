#=========================================================================
# DelayPipeCL.py
#=========================================================================
# This delay pipe models a inelasic pipeline queue with enq/deq interfaces
#
# Author : Shunning Jiang
# Date   : May 7, 2018

from __future__ import absolute_import, division, print_function

from collections import deque

from pclib.ifcs import guarded_ifc
from pymtl import *

# This delay pipe is for cycle-level performance modeling purpose

class DelayPipeCL( Component ):

  @guarded_ifc( lambda s: s.pipeline[0] is None )
  def enq( s, msg ):
    assert s.pipeline[0] is None
    s.pipeline[0] = msg

  @guarded_ifc( lambda s: s.pipeline[-1] is not None )
  def deq( s ):
    ret = s.pipeline[-1]
    s.pipeline[-1] = None
    return ret

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

      @s.update
      def up_delay():
        if not s.pipeline[-1]:
          s.pipeline.rotate()

      # Model decoupled pipe behavior to cut cyclic dependencies.
      # Basically no matter in what order s.deq and s.enq are called,
      # the outcomes are the same as long as up_delay is called before
      # both of them.
      s.add_constraints(
        U(up_delay) < M(s.deq),
        U(up_delay) < M(s.enq),
      )

  def line_trace( s ):
    return "[{}]".format( "".join( [ " " if x is None else "*" for x in list(s.pipeline)[:-1] ] ) )
