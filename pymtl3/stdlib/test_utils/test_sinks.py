"""
========================================================================
Test sinks
========================================================================
Test sinks with CL and RTL interfaces.

Author : Yanghui Ou
  Date : Mar 11, 2019
"""

from pymtl3 import *
from pymtl3.stdlib.ifcs import RecvIfcRTL, RecvRTL2SendCL


class PyMTLTestSinkError( Exception ): pass

#-------------------------------------------------------------------------
# TestSinkCL
#-------------------------------------------------------------------------

class TestSinkCL( Component ):

  def construct( s, Type, msgs, initial_delay=0, interval_delay=0,
                 arrival_time=None, cmp_fn=lambda a, b : a == b ):

    s.recv.Type = Type

    # [msgs] and [arrival_time] must have the same length.
    if arrival_time is not None:
      assert len( msgs ) == len( arrival_time )

    s.idx          = 0
    s.cycle_count  = 0
    s.msgs         = list( msgs )
    s.arrival_time = None if not arrival_time else list( arrival_time )
    s.cmp_fn       = cmp_fn
    s.error_msg    = ''

    s.all_msg_recved = False
    s.done_flag      = False

    s.count = initial_delay
    s.intv  = interval_delay

    s.recv_called = False

    @update_once
    def up_sink_count():
      # Raise exception at the start of next cycle so that the errored
      # line trace gets printed out
      if s.error_msg:
        raise PyMTLTestSinkError( s.error_msg )

      # Tick one more cycle after all message is received so that the
      # exception gets thrown
      if s.all_msg_recved:
        s.done_flag = True

      if s.idx >= len( s.msgs ):
        s.all_msg_recved = True

      if not s.reset:
        s.cycle_count += 1
      else:
        s.cycle_count = 0

      # if recv was called in previous cycle
      if s.recv_called:
        s.count = s.intv
      elif s.count != 0:
        s.count -= 1
      else:
        s.count = 0

      s.recv_called = False

    s.add_constraints(
      U( up_sink_count ) < M( s.recv ),
      U( up_sink_count ) < M( s.recv.rdy )
    )

  @non_blocking( lambda s: s.count==0 )
  def recv( s, msg ):
    assert s.count == 0, "Invalid en/rdy transaction! Sink is stalled (not ready), but receives a message."

    # Sanity check
    if s.idx >= len( s.msgs ):
      s.error_msg = ( 'Test Sink received more msgs than expected!\n'
                      f'Received : {msg}' )

    # Check correctness first
    elif not s.cmp_fn( msg, s.msgs[ s.idx ] ):
      s.error_msg = (
        f'Test sink {s} received WRONG message!\n'
        f'Expected : { s.msgs[ s.idx ] }\n'
        f'Received : { msg }'
      )

    # Check timing if performance regeression is turned on
    elif s.arrival_time and s.cycle_count > s.arrival_time[ s.idx ]:
      s.error_msg = (
        f'Test sink {s} received message LATER than expected!\n'
        f'Expected msg : {s.msgs[ s.idx ]}\n'
        f'Expected at  : {s.arrival_time[ s.idx ]}\n'
        f'Received msg : {msg}\n'
        f'Received at  : {s.cycle_count}'
      )

    else:
      s.idx += 1
      s.recv_called = True

  def done( s ):
    return s.done_flag

  # Line trace
  def line_trace( s ):
    return "{}".format( s.recv )

#-------------------------------------------------------------------------
# TestSinkRTL
#-------------------------------------------------------------------------

class TestSinkRTL( Component ):

  def construct( s, Type, msgs, initial_delay=0, interval_delay=0,
                 arrival_time=None, cmp_fn=lambda a, b : a == b ):

    # Interface

    s.recv = RecvIfcRTL( Type )

    # Components

    s.sink    = TestSinkCL( Type, msgs, initial_delay, interval_delay,
                            arrival_time, cmp_fn )
    s.adapter = RecvRTL2SendCL( Type )

    connect( s.recv,         s.adapter.recv )
    connect( s.adapter.send, s.sink.recv    )

  def done( s ):
    return s.sink.done()

  # Line trace

  def line_trace( s ):
    return "{}".format( s.recv )
