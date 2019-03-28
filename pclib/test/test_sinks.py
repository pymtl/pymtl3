#=========================================================================
# Test sinks
#=========================================================================
# Test sinks with CL and RTL interfaces.
#
# Author : Yanghui Ou
#   Date : Mar 11, 2019

from pymtl import *
from pclib.ifcs import RecvIfcRTL, enrdy_to_str
from pclib.ifcs import RecvCL2SendRTL, RecvRTL2SendCL
from pclib.ifcs.GuardedIfc import guarded_ifc
#-------------------------------------------------------------------------
# TestSinkCL
#-------------------------------------------------------------------------

class TestSinkCL( ComponentLevel6 ):

  def construct( s, msgs, initial_delay=0, interval_delay=0,
                 arrival_time=None ):

    # [msgs] and [arrival_time] must have the same length.
    if arrival_time is not None:
      assert len( msgs ) == len( arrival_time )

    s.idx          = 0
    s.cycle_count  = 0
    s.msgs         = list( msgs )
    s.arrival_time = None if arrival_time is None else \
                     list( arrival_time )
    s.perf_regr    = True if arrival_time is not None else False

    s.initial_count  = initial_delay
    s.interval_delay = interval_delay
    s.interval_count = 0

    s.recv_msg    = None
    s.recv_called = False
    s.recv_rdy    = False
    s.trace_len   = len( str( s.msgs[0] ) )

    @s.update
    def up_sink_count():

      s.cycle_count += 1

      # if recv was called in previous cycle
      if s.recv_called:
        s.interval_count = s.interval_delay

      elif s.initial_count != 0:
        s.initial_count -= 1

      elif s.interval_count != 0:
        s.interval_count -= 1

      else:
        s.interval_count = 0

      s.recv_called = False
      s.recv_msg    = None
      s.recv_rdy    = s.initial_count == 0 and s.interval_count == 0

    s.add_constraints(
      U( up_sink_count ) < M( s.recv ),
      U( up_sink_count ) < M( s.recv.rdy )
    )

  @guarded_ifc( lambda s: s.initial_count==0 and s.interval_count==0 )
  def recv( s, msg ):

    s.recv_msg = msg
    # Sanity check
    if s.idx >= len( s.msgs ):
      raise Exception( "Test Sink received more msgs than expected" )

    # Check correctness first
    if s.recv_msg != s.msgs[ s.idx ]:
      raise Exception( """
Test Sink received WRONG msg!
Expected : {}
Received : {}""".format( s.msgs[ s.idx ], s.recv_msg ) )
    elif s.perf_regr and s.cycle_count > s.arrival_time[ s.idx ]:
      raise Exception( """
Test Sink received msg LATER than expected!
Expected cycles: {}
Received at    : {}""".format( s.arrival_time[ s.idx ], s.cycle_count ) )
    else:
      s.idx += 1
      s.recv_called = True

  def done( s ):
    return s.idx >= len( s.msgs )

  # Line trace
  def line_trace( s ):
    trace = enrdy_to_str( s.recv_msg, s.recv_called, s.recv_rdy )
    return "{}".format( trace.ljust( s.trace_len ) )

#-------------------------------------------------------------------------
# TestSinkRTL
#-------------------------------------------------------------------------

class TestSinkRTL( ComponentLevel6 ):

  def construct( s, MsgType, msgs, initial_delay=0, interval_delay=0,
                 arrival_time=None ):

    # Interface

    s.recv = RecvIfcRTL( MsgType )

    # Components

    s.sink    = TestSinkCL( msgs, initial_delay, interval_delay,
                            arrival_time )
    s.adapter = RecvRTL2SendCL( MsgType )

    s.connect( s.recv,         s.adapter.recv )
    s.connect( s.adapter.send, s.sink.recv    )

  def done( s ):
    return s.sink.done()

  # Line trace

  def line_trace( s ):
    return "|{}|->{}".format(
      s.adapter.line_trace(), s.sink.line_trace() )
