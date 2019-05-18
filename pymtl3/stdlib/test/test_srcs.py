"""
========================================================================
Test sources
========================================================================
Test sources with CL or RTL interfaces.

Author : Yanghui Ou
  Date : Mar 11, 2019
"""

from __future__ import absolute_import, division, print_function

from collections import deque

from pymtl3 import *
from pymtl3.stdlib.ifcs import (
    GuardedCallerIfc,
    RecvCL2SendRTL,
    RecvRTL2SendCL,
    SendIfcRTL,
)

#-------------------------------------------------------------------------
# TestSrcCL
#-------------------------------------------------------------------------

class TestSrcCL( Component ):

  def construct( s, msgs, initial_delay=0, interval_delay=0 ):

    s.send = GuardedCallerIfc()

    s.msgs = deque( msgs )

    s.count  = initial_delay
    s.delay  = interval_delay

    s.msg_to_send = None
    s.send_called = False
    s.send_rdy    = False
    s.trace_len = len( str( s.msgs[0] ) ) if len(s.msgs) != 0 else 0

    @s.update
    def up_src_send():

      s.send_called = False
      if not s.count==0:
        s.count -= 1
      elif not s.reset:
        s.msg_to_send = None
        if s.send.rdy() and s.msgs:
          s.msg_to_send = s.msgs.popleft()
          s.send( s.msg_to_send )
          # reset count only after a message is sent
          s.count = s.delay
          s.send_called = True
          s.send_rdy    = True

  def done( s ):
    return not s.msgs

  # Line trace

  def line_trace( s ):
    trace = " " if not s.send_called and s.send_rdy else \
            "#" if not s.send_called and not s.send_rdy else \
            "X" if s.send_called and not s.send_rdy else \
            str( s.msg_to_send )

    return "{}".format( trace.ljust( s.trace_len ) )

#-------------------------------------------------------------------------
# TestSrcRTL
#-------------------------------------------------------------------------

class TestSrcRTL( Component ):

  def construct( s, MsgType, msgs, initial_delay=0, interval_delay=0 ):

    # Interface

    s.send = SendIfcRTL( MsgType )

    # Components

    s.src     = TestSrcCL( msgs, initial_delay, interval_delay )
    s.adapter = RecvCL2SendRTL( MsgType )

    s.connect( s.src.send,     s.adapter.recv )
    s.connect( s.adapter.send, s.send         )

  def done( s ):
    return s.src.done()

  # Line trace

  def line_trace( s ):
    return "{}|{}|".format( s.src.line_trace(), s.adapter.line_trace() )
