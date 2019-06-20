"""
========================================================================
Test sinks
========================================================================
Test sinks with CL and RTL interfaces.

Author : Yanghui Ou
  Date : Mar 11, 2019
"""

from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.stdlib.ifcs import RecvIfcRTL, RecvRTL2SendCL, enrdy_to_str

#-------------------------------------------------------------------------
# TestSinkCL
#-------------------------------------------------------------------------

class TestSinkCL( Component ):

  def construct( s, Type, msgs, initial_delay=0, interval_delay=0,
                 arrival_time=None ):

    s.recv.Type = Type

    # [msgs] and [arrival_time] must have the same length.
    if arrival_time is not None:
      assert len( msgs ) == len( arrival_time )

    s.idx          = 0
    s.cycle_count  = 0
    s.msgs         = list( msgs )
    s.arrival_time = (
      None if arrival_time is None else
      list( arrival_time )
    )
    s.perf_regr = True if arrival_time is not None else False

    s.count = initial_delay
    s.intv  = interval_delay

    s.recv_called = False

    @s.update
    def up_sink_count():
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
    assert s.count == 0

    # Sanity check
    if s.idx >= len( s.msgs ):
      raise Exception( "Test Sink received more msgs than expected" )

    # Check correctness first
    if msg != s.msgs[ s.idx ]:
      raise Exception( """
Test Sink received WRONG msg!
Expected : {}
Received : {}""".format( s.msgs[ s.idx ], msg ) )
    elif s.perf_regr and s.cycle_count > s.arrival_time[ s.idx ]:
      raise Exception( """
Test Sink received msg LATER than expected!
Expected msg   : {}
Expected cycles: {}
Received at    : {}""".format(
        s.msgs[ s.idx ],
        s.arrival_time[ s.idx ],
        s.cycle_count
      ) )
    else:
      s.idx += 1
      s.recv_called = True

  def done( s ):
    return s.idx >= len( s.msgs )

  # Line trace
  def line_trace( s ):
    return "{}".format( s.recv )

#-------------------------------------------------------------------------
# TestSinkRTL
#-------------------------------------------------------------------------

class TestSinkRTL( Component ):

  def construct( s, Type, msgs, initial_delay=0, interval_delay=0,
                 arrival_time=None ):

    # Interface

    s.recv = RecvIfcRTL( Type )

    # Components

    s.sink    = TestSinkCL( Type, msgs, initial_delay, interval_delay,
                            arrival_time )
    s.adapter = RecvRTL2SendCL( Type )

    s.connect( s.recv,         s.adapter.recv )
    s.connect( s.adapter.send, s.sink.recv    )

  def done( s ):
    return s.sink.done()

  # Line trace

  def line_trace( s ):
    return "{}".format( s.recv )
