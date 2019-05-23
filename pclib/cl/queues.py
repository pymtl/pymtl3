"""
========================================================================
queues.py
========================================================================
This file contains cycle-level queues.

Author : Shunning Jiang, Yanghui Ou
Date   : Mar 10, 2018
"""

from __future__ import absolute_import, division, print_function

from collections import deque

from pclib.ifcs.SendRecvIfc import enrdy_to_str
from pymtl import *

#-------------------------------------------------------------------------
# PipeQueueCL
#-------------------------------------------------------------------------

class PipeQueueCL( Component ):

  def construct( s, size ):
    s.queue = deque( maxlen=size )

    # Line trace variables
    s.enq_called = False
    s.enq_msg    = None
    s.enq_rdy    = False
    s.deq_called = False
    s.deq_msg    = None
    s.deq_rdy    = False

    @s.update
    def up_pulse():
      s.enq_called = False
      s.enq_msg    = None
      s.enq_rdy    = s.enq.rdy()
      s.deq_called = False
      s.deq_msg    = None
      s.deq_rdy    = s.deq.rdy()

    s.add_constraints(
      U( up_pulse ) < M( s.enq.rdy ),
      U( up_pulse ) < M( s.deq.rdy ),
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
    return "{}(){}".format(
      enrdy_to_str( s.enq_msg, s.enq_called, s.enq_rdy ),
      enrdy_to_str( s.deq_msg, s.deq_called, s.deq_rdy )
    )

#-------------------------------------------------------------------------
# BypassQueueCL
#-------------------------------------------------------------------------

class BypassQueueCL( Component ):

  def construct( s, size ):
    s.queue = deque( maxlen=size )

    # Line trace variables
    s.enq_called = False
    s.enq_msg    = None
    s.enq_rdy    = False
    s.deq_called = False
    s.deq_msg    = None
    s.deq_rdy    = False

    @s.update
    def up_pulse():
      s.enq_called = False
      s.enq_msg    = None
      s.enq_rdy    = s.enq.rdy()
      s.deq_called = False
      s.deq_msg    = None
      s.deq_rdy    = s.deq.rdy()

    s.add_constraints(
      U( up_pulse ) < M( s.enq.rdy ),
      U( up_pulse ) < M( s.deq.rdy ),
      M( s.enq    ) < M( s.peek    ),
      M( s.enq    ) < M( s.deq     ),
    )

  @non_blocking( lambda s: len( s.queue ) < s.queue.maxlen )
  def enq( s, v ):
    s.enq_called = True
    s.deq_rdy    = True
    s.enq_msg    = v
    s.queue.appendleft( s.enq_msg )

  @non_blocking( lambda s: len( s.queue ) > 0 )
  def deq( s ):
    s.deq_called = True
    s.deq_msg    = s.queue.pop()
    return s.deq_msg

  @non_blocking( lambda s: len( s.queue ) > 0 )
  def peek( s ):
    return s.queue[-1]

  def line_trace( s ):
    return "{}(){}".format(
      enrdy_to_str( s.enq_msg, s.enq_called, s.enq_rdy ),
      enrdy_to_str( s.deq_msg, s.deq_called, s.deq_rdy )
    )

#-------------------------------------------------------------------------
# NormalQueueCL
#-------------------------------------------------------------------------

class NormalQueueCL( Component ):

  def construct( s, size ):
    s.queue = deque( maxlen=size )

    # Line trace variables
    s.enq_called = False
    s.enq_msg    = None
    s.enq_rdy    = False
    s.deq_called = False
    s.deq_msg    = None
    s.deq_rdy    = False

    @s.update
    def up_pulse():
      s.enq_called = False
      s.enq_msg    = None
      s.enq_rdy    = len( s.queue ) < s.queue.maxlen
      s.deq_called = False
      s.deq_msg    = None
      s.deq_rdy    = len( s.queue ) > 0

    s.add_constraints(
      U( up_pulse ) < M( s.enq.rdy ),
      U( up_pulse ) < M( s.deq.rdy ),
      M( s.peek   ) < M( s.deq  ),
      M( s.peek   ) < M( s.enq  )
    )

  @non_blocking( lambda s: s.enq_rdy )
  def enq( s, v ):
    s.enq_called = True
    s.enq_msg    = v
    s.queue.appendleft( s.enq_msg )

  @non_blocking( lambda s: s.deq_rdy )
  def deq( s ):
    s.deq_called = True
    s.deq_msg    = s.queue.pop()
    return s.deq_msg

  @non_blocking( lambda s: len( s.queue ) > 0 )
  def peek( s ):
    return s.queue[-1]

  def line_trace( s ):
    return "{}(){}".format(
      enrdy_to_str( s.enq_msg, s.enq_called, s.enq_rdy ),
      enrdy_to_str( s.deq_msg, s.deq_called, s.deq_rdy )
    )
