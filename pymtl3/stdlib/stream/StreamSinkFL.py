"""
========================================================================
StremSinkFL
========================================================================
Test sinks with port interfaces.

Author : Shunning Jiang, Peitian Pan
  Date : Aug 26, 2022
"""

from random import randint

from pymtl3 import *
from .ifcs import IStreamIfc


class PyMTLTestSinkError( Exception ): pass

#-------------------------------------------------------------------------
# StreamSinkFL
#-------------------------------------------------------------------------

class StreamSinkFL( Component ):

  def construct( s, Type, msgs, initial_delay=0, interval_delay=0,
                 interval_delay_mode='fixed',
                 arrival_time=None, cmp_fn=lambda a, b : a == b,
                 ordered=True ):

    # Interface

    s.istream = IStreamIfc( Type )

    # Data

    # [msgs] and [arrival_time] must have the same length.
    if arrival_time is None:
      s.arrival_time = None
    else:
      assert len( msgs ) == len( arrival_time )
      s.arrival_time = list( arrival_time )

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

      if s.idx >= len(s.msgs):
        s.all_msg_recved = True

      s.received = False

      if s.reset:
        s.cycle_count = 0

        s.idx = 0
        s.count = initial_delay
        s.istream.rdy <<= (s.idx < len(s.msgs)) & (s.count == 0)

      else:
        s.cycle_count += 1

        # This means at least previous cycle count = 0
        if s.istream.val & s.istream.rdy:
          msg = s.istream.msg

          # Sanity check
          if s.idx >= len(s.msgs):
            s.error_msg = ( 'Test Sink received more msgs than expected!\n'
                           f'Received : {msg}' )

          else:

            # Check correctness assuming sink messages are ordered

            if ordered:

              if not cmp_fn( msg, s.msgs[ s.idx ] ):
                s.error_msg = (
                  f'Test sink {s} received WRONG message!\n'
                  f'Expected : { s.msgs[ s.idx ] }\n'
                  f'Received : { msg }'
                )

            # Check correctness assuming sink messages are unordered

            else:

              found = False
              for ref_msg in s.msgs:
                if cmp_fn( msg, ref_msg ):
                  found = True
                  break

              if not found:
                s.error_msg = (
                  f'Test sink {s} received WRONG message!'
                  f'Received : { msg }\n'
                  f'Sink is in not checking message order, so the received\n'
                  f'message was compared against all expected messages'
                )

            # Check timing if performance regeression is turned on
            if not s.error_msg:
              if s.arrival_time and s.cycle_count > s.arrival_time[ s.idx ]:
                s.error_msg = (
                  f'Test sink {s} received message LATER than expected!\n'
                  f'Expected msg : {s.msgs[ s.idx ]}\n'
                  f'Expected at  : {s.arrival_time[ s.idx ]}\n'
                  f'Received msg : {msg}\n'
                  f'Received at  : {s.cycle_count}'
                )

          s.idx += 1
          if ( interval_delay_mode == 'random' ):
            s.count = randint(0,interval_delay)
          else:
            s.count = interval_delay

        if s.count > 0:
          s.count -= 1
          s.istream.rdy <<= 0
        else: # s.count == 0
          # s.istream.rdy <<= (s.idx < len(s.msgs))
          s.istream.rdy <<= 1

  def done( s ):
    return s.done_flag

  # Line trace

  def line_trace( s ):
    return f"{s.istream}"
