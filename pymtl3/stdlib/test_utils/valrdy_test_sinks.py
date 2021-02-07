"""
========================================================================
Test sinks
========================================================================
Test sinks with CL and RTL interfaces.

Author : Yanghui Ou
  Date : Mar 11, 2019
"""

from pymtl3 import *
from pymtl3.stdlib.ifcs import InValRdyIfc


class PyMTLTestSinkError( Exception ): pass

#-------------------------------------------------------------------------
# TestSinkRTL
#-------------------------------------------------------------------------

class TestSinkRTL( Component ):

  def construct( s, Type, msgs, initial_delay=0, interval_delay=0,
                 arrival_time=None, cmp_fn=lambda a, b : a == b ):

    # Interface

    s.in_ = InValRdyIfc( Type )

    # Data

    # [msgs] and [arrival_time] must have the same length.
    if arrival_time is None:
      s.arrival_time = None
    else:
      assert len( msgs ) == len( arrival_time )
      s.arrival_time = list( arrival_time )

    s.num_msgs     = len(msgs)
    s.idx          = 0
    s.count        = 0
    s.cycle_count  = 0
    s.msgs         = list( msgs )

    s.error_msg    = ''

    s.received = False
    s.all_msg_recved = False
    s.done_flag      = False

    @update_ff
    def up_sink():
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

      s.received = False

      if s.reset:
        s.cycle_count = 0

        s.idx = 0
        s.count = initial_delay
        s.in_.rdy <<= (s.idx < s.num_msgs) & (s.count == 0)

      else:
        s.cycle_count += 1

        # This means at least previous cycle count = 0
        if s.in_.val & s.in_.rdy:
          msg = s.in_.msg

          # Sanity check
          if s.idx >= s.num_msgs:
            s.error_msg = ( 'Test Sink received more msgs than expected!\n'
                           f'Received : {msg}' )

          else:
            # Check correctness first
            if not cmp_fn( msg, s.msgs[ s.idx ] ):
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

          s.idx += 1
          s.count = interval_delay

        if s.count > 0:
          s.count -= 1
          s.in_.rdy <<= 0
        else: # s.count == 0
          s.in_.rdy <<= (s.idx < s.num_msgs)

  def done( s ):
    return s.done_flag

  # Line trace

  def line_trace( s ):
    return f"{s.in_}"
