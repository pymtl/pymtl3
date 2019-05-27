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

from pclib.ifcs import RecvCL2SendRTL, SendIfcRTL
from pymtl import *

#-------------------------------------------------------------------------
# TestSrcCL
#-------------------------------------------------------------------------

class TestSrcCL( Component ):

  def construct( s, msgs, initial_delay=0, interval_delay=0 ):

    s.send = NonBlockingCallerIfc()

    s.msgs = deque( msgs )

    s.count  = initial_delay
    s.delay  = interval_delay

    @s.update
    def up_src_send():
      if s.count > 0:
        s.count -= 1
      elif not s.reset:
        if s.send.rdy() and s.msgs:
          s.send( s.msgs.popleft() )
          s.count = s.delay # reset count after a message is sent

  def done( s ):
    return not s.msgs

  # Line trace

  def line_trace( s ):
    return "{}".format( s.send )

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
    return "{}".format( s.send )
