"""
========================================================================
queues.py
========================================================================
This file contains cycle-level queues.

Author : Shunning Jiang, Yanghui Ou
Date   : Mar 10, 2018
"""

from collections import deque

from pymtl3 import *
from pymtl3.stdlib.ifcs.SendRecvIfc import enrdy_to_str

#-------------------------------------------------------------------------
# PipeQueueCL
#-------------------------------------------------------------------------

class PipeQueueCL( Component ):

  def construct( s, num_entries=1 ):
    s.queue = deque( maxlen=num_entries )

    s.add_constraints(
      M( s.peek   ) < M( s.enq  ),
      M( s.deq    ) < M( s.enq  )
    )

  @non_blocking( lambda s: len( s.queue ) < s.queue.maxlen )
  def enq( s, v ):
    s.enq_called = True
    s.enq_msg    = v
    s.queue.appendleft( s.enq_msg )

  @non_blocking( lambda s: len( s.queue ) > 0 )
  def deq( s ):
    s.deq_called = True
    s.enq_rdy    = True
    s.deq_msg    = s.queue.pop()
    return s.deq_msg

  @non_blocking( lambda s: len( s.queue ) > 0 )
  def peek( s ):
    return s.queue[-1]

  def line_trace( s ):
    return "{}(){}".format( s.enq, s.deq )

#-------------------------------------------------------------------------
# BypassQueueCL
#-------------------------------------------------------------------------

class BypassQueueCL( Component ):

  def construct( s, num_entries=1 ):
    s.queue = deque( maxlen=num_entries )

    s.add_constraints(
      M( s.enq    ) < M( s.peek    ),
      M( s.enq    ) < M( s.deq     ),
    )

  @non_blocking( lambda s: len( s.queue ) < s.queue.maxlen )
  def enq( s, v ):
    s.queue.appendleft( v )

  @non_blocking( lambda s: len( s.queue ) > 0 )
  def deq( s ):
    return s.queue.pop()

  @non_blocking( lambda s: len( s.queue ) > 0 )
  def peek( s ):
    return s.queue[-1]

  def line_trace( s ):
    return "{}(){}".format( s.enq, s.deq )

#-------------------------------------------------------------------------
# NormalQueueCL
#-------------------------------------------------------------------------

class NormalQueueCL( Component ):

  def construct( s, num_entries=1 ):
    s.queue = deque( maxlen=num_entries )
    s.enq_rdy = False
    s.deq_rdy = False

    @s.update
    def up_pulse():
      s.enq_rdy    = len( s.queue ) < s.queue.maxlen
      s.deq_rdy    = len( s.queue ) > 0

    s.add_constraints(
      U( up_pulse ) < M( s.enq.rdy ),
      U( up_pulse ) < M( s.deq.rdy ),
      M( s.peek   ) < M( s.deq  ),
      M( s.peek   ) < M( s.enq  )
    )

  @non_blocking( lambda s: s.enq_rdy )
  def enq( s, v ):
    s.queue.appendleft( v )

  @non_blocking( lambda s: s.deq_rdy )
  def deq( s ):
    return s.queue.pop()

  @non_blocking( lambda s: len( s.queue ) > 0 )
  def peek( s ):
    return s.queue[-1]

  def line_trace( s ):
    return "{}(){}".format( s.enq, s.deq )
