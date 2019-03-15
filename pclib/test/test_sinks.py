#=========================================================================
# Test sinks 
#=========================================================================
# Test sinks with CL and RTL interfaces.
#
# Author : Yanghui Ou
#   Date : Mar 11, 2019

from pymtl import *
from pymtl.dsl.ComponentLevel6 import method_port, ComponentLevel6
from pclib.ifcs                import RecvIfcRTL
from pclib.ifcs                import RecvCL2SendRTL, RecvRTL2SendCL

#-------------------------------------------------------------------------
# TestSinkCL
#-------------------------------------------------------------------------

class TestSinkCL( ComponentLevel6 ):
  
  def construct( s, msgs, initial_delay=0, interval_delay=0 ):
    
    s.idx  = 0
    s.msgs = list( msgs )
    
    s.initial_count    = initial_delay
    s.interval_delay = interval_delay
    s.interval_count   = 0

    s.recv_msg    = None 
    s.recv_called = False 
    s.recv_rdy    = False
    s.trace_len   = len( str( s.msgs[0] ) )

    @s.update
    def decr_count():

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
      s.recv_rdy    = s.recv.rdy()

    s.add_constraints( 
      U( decr_count ) < M( s.recv ),
      U( decr_count ) < M( s.recv.rdy )
    )
 
  @method_port( lambda s: s.initial_count==0 and s.interval_count==0 )
  def recv( s, msg ):

    s.recv_msg = msg
    # Sanity check 
    if s.idx >= len( s.msgs ):
      raise Exception( "Test Sink received more msgs than expected" )

    if s.recv_msg != s.msgs[s.idx]:
      raise Exception( """
        Test Sink received WRONG msg!
        Expected : {}
        Received : {}
        """.format( s.msgs[s.idx], s.recv_msg ) )
    else:
      s.idx += 1
      s.recv_called = True

  def done( s ):
    return s.idx >= len( s.msgs )
  
  def line_trace( s ):
    trace = " " if not s.recv_called and s.recv_rdy else \
            "#" if not s.recv_called and not s.recv_rdy else \
            "X" if s.recv_called and not s.recv_rdy else \
            str( s.recv_msg )

    return "{}".format( trace.ljust( s.trace_len ) )

#-------------------------------------------------------------------------
# TestSinkRTL
#-------------------------------------------------------------------------

class TestSinkRTL( ComponentLevel6 ):

  def construct( s, MsgType, msgs, initial_delay=0, interval_delay=0 ):

    # Interface

    s.recv = RecvIfcRTL( MsgType )

    # Components

    s.sink    = TestSinkCL( msgs, initial_delay, interval_delay )
    s.adapter = RecvRTL2SendCL( MsgType )
    
    s.connect( s.recv,         s.adapter.recv )
    s.connect( s.adapter.send, s.sink.recv    )

  def done( s ):
    return s.sink.done()

  # Line trace

  def line_trace( s ):
    return "|{}|->{}".format(
      s.adapter.line_trace(), s.sink.line_trace() )
