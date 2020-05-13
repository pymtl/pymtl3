"""
========================================================================
ComponentLevel6_test.py
========================================================================
Tests for component level6.

Author : Yanghui Ou
  Date : Feb 24, 2019
"""
from collections import deque

from pymtl3.datatypes import Bits16
from pymtl3.dsl.ComponentLevel1 import update
from pymtl3.dsl.ComponentLevel3 import connect
from pymtl3.dsl.ComponentLevel4 import update_once
from pymtl3.dsl.ComponentLevel6 import ComponentLevel6, non_blocking
from pymtl3.dsl.Connectable import CalleeIfcCL, CallerIfcCL
from pymtl3.dsl.ConstraintTypes import M, U

from .sim_utils import simple_sim_pass

#-------------------------------------------------------------------------
# TestSrc
#-------------------------------------------------------------------------

class TestSrc( ComponentLevel6 ):

  def construct( s, msgs ):

    s.send = CallerIfcCL()

    s.msgs = deque( msgs )
    s.head = None
    s.trace_len = len( str( s.msgs[0] ) )

    @update_once
    def send_msg():
      s.head = None
      if s.send.rdy() and s.msgs:
        s.head = s.msgs.popleft()
        s.send( s.head )

  def done( s ):
    return not s.msgs

  def line_trace( s ):
    return "{}".format(
        "" if s.head is None
           else str( s.head ) ).ljust( s.trace_len )

#-------------------------------------------------------------------------
# TestSink
#-------------------------------------------------------------------------

class TestSink( ComponentLevel6 ):

  def construct( s, msgs ):
    s.idx  = 0
    s.msgs = list( msgs )
    s.head = None
    s.trace_len = len( str( s.msgs[0] ) )

  @non_blocking( lambda s: True )
  def recv( s, msg ):

    s.head = msg
    # Sanity check
    if s.idx >= len( s.msgs ):
      raise Exception( "Test Sink received more msgs than expected" )

    if msg != s.msgs[s.idx]:
      raise Exception( """
        Test Sink received WRONG msg!
        Expected : {}
        Received : {}
        """.format( s.msgs[s.idx], msg ) )
    else:
      s.idx += 1

  def done( s ):
    return s.idx >= len( s.msgs )

  def line_trace( s ):
    tmp = s.head
    s.head = None
    return "{}".format(
      "" if tmp is None else str( tmp ) ).ljust( s.trace_len )

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( ComponentLevel6 ):

  def construct( s, DUT, src_msgs, sink_msgs ):

    s.src     = TestSrc ( src_msgs  )
    s.sink    = TestSink( sink_msgs )
    s.dut     = DUT

    # Connections
    connect( s.src.send, s.dut.recv  )
    connect( s.dut.send, s.sink.recv )


  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{} ->| {} |-> {}".format(
      s.src.line_trace(), s.dut.line_trace(), s.sink.line_trace() )

#-------------------------------------------------------------------------
# run_cl_sim
#-------------------------------------------------------------------------

def run_cl_sim( th, max_cycles=50 ):

  # Create a simulator

  th.elaborate()
  simple_sim_pass( th )

  # Run simluation

  ncycles = 0
  print("{}:{}".format( ncycles, th.line_trace() ))
  while not th.done() and ncycles < max_cycles:
    th.tick()
    ncycles += 1
    print("{}:{}".format( ncycles, th.line_trace() ))

  # Check timeout

  assert ncycles < max_cycles

  th.tick()
  th.tick()
  th.tick()

#-------------------------------------------------------------------------
# SimpleQueue
#-------------------------------------------------------------------------

class SimpleQueue( ComponentLevel6 ):

  def construct( s ):
    s.element = None

    # TODO: Improve this
    s.add_constraints(
      # M( s.deq.method ) < M( s.enq.method ),
      M( s.deq ) < M( s.enq ),
      # M( s.deq.rdy ) < M( s.enq.rdy )
    )

  def empty( s ):
    return s.element is None

  @non_blocking( lambda s : s.empty() )
  def enq( s, ele ):
    s.element = ele

  @non_blocking( lambda s: not s.empty() )
  def deq( s ):
    ret = s.element
    s.element = None
    return ret

  def line_trace( s ):
    return "{}".format(
      "    " if s.element is None else str( s.element ) )

# Test the SimpleQueue as a SW data structure.

def test_queue_sw():

  q = SimpleQueue()
  q.elaborate()

  assert q.enq.rdy()
  assert q.empty()
  assert not q.deq.rdy()

  q.enq( Bits16( 128 ) )
  assert not q.enq.rdy()
  assert not q.empty()
  assert q.deq.rdy()

  assert q.deq() == Bits16( 128 )
  assert q.enq.rdy()
  assert q.empty()
  assert not q.deq.rdy()

#-------------------------------------------------------------------------
# QueueIncr
#-------------------------------------------------------------------------

class QueueIncr( ComponentLevel6 ):

  def construct( s ):
    s.recv  = CalleeIfcCL()
    s.send  = CallerIfcCL()
    s.queue = SimpleQueue()

    connect( s.recv, s.queue.enq )

    s.v = None
    @update_once
    def deq_incr():
      s.v = None
      if s.queue.deq.rdy() and s.send.rdy():
        s.v = s.queue.deq() + 1
        s.send( s.v )

  def line_trace( s ):
    return "{} (+) {}".format( s.queue.line_trace(), s.v )

#-------------------------------------------------------------------------
# QueueIncrChained
#-------------------------------------------------------------------------

class QueueIncrChained( ComponentLevel6 ):

  def construct( s ):

    s.recv = CalleeIfcCL()
    s.send = CallerIfcCL()

    s.q0 = QueueIncr()
    s.q1 = QueueIncr()

    connect( s.recv,    s.q0.recv )
    connect( s.q0.send, s.q1.recv )
    connect( s.q1.send, s.send    )

  def line_trace( s ):
    return "{} -> {}".format( s.q0.line_trace(), s.q1.line_trace() )

#-------------------------------------------------------------------------
# CL tests
#-------------------------------------------------------------------------

def test_queue_incr_cl():
  q    = QueueIncr()
  src_msgs  = [ Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ) ]
  sink_msgs = [ Bits16( 1 ), Bits16( 2 ), Bits16( 3 ), Bits16( 4 ) ]
  th = TestHarness( q, src_msgs, sink_msgs )
  run_cl_sim( th )

def test_chained_queue_incr_cl():
  q    = QueueIncrChained()
  src_msgs  = [ Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ) ]
  sink_msgs = [ Bits16( 2 ), Bits16( 3 ), Bits16( 4 ), Bits16( 5 ) ]
  th = TestHarness( q, src_msgs, sink_msgs )
  run_cl_sim( th )
