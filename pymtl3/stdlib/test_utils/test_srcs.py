"""
========================================================================
Test sources
========================================================================
Test sources with CL or RTL interfaces.

Author : Yanghui Ou
  Date : Mar 11, 2019
"""
from collections import deque

from pymtl3 import *
from pymtl3.stdlib.ifcs import RecvCL2SendRTL, SendIfcRTL

#-------------------------------------------------------------------------
# TestSrcCL
#-------------------------------------------------------------------------

class TestSrcCL( Component ):

  def construct( s, Type, msgs, initial_delay=0, interval_delay=0 ):

    s.send = CallerIfcCL( Type=Type )
    s.msgs = deque( msgs )

    s.count  = initial_delay
    s.delay  = interval_delay

    @update_once
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
# TODO: deprecating TestSrcRTL.

class TestSrcRTL( Component ):

  def construct( s, Type, msgs, initial_delay=0, interval_delay=0 ):

    # Interface

    s.send = SendIfcRTL( Type )

    # Components

    s.src     = TestSrcCL( Type, msgs, initial_delay, interval_delay )
    s.adapter = RecvCL2SendRTL( Type )

    connect( s.src.send,     s.adapter.recv )
    connect( s.adapter.send, s.send         )

  def done( s ):
    return s.src.done()

  # Line trace

  def line_trace( s ):
    return "{}".format( s.send )
