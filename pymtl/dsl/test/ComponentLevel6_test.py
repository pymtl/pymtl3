#=========================================================================
# ComponentLevel6_test.py
#=========================================================================
# Tests for component level6.
#
# Author : Yanghui Ou
#   Date : Feb 24, 2019

from pymtl import *
from pymtl.dsl.ComponentLevel6 import method_port, ComponentLevel6
from sim_utils import simple_sim_pass
from collections import deque
from pymtl.passes.PassGroups import SimpleCLSim

#-------------------------------------------------------------------------
# TestSrc
#-------------------------------------------------------------------------

class TestSrc( ComponentLevel6 ):

  def construct( s, msgs ):

    s.send = CallerPort()

    s.msgs = deque( msgs )
    s.head = None
    s.trace_len = len( str( s.msgs[0] ) )
 
    @s.update
    def send_msg():
      s.head = None
      if s.send.rdy() and s.msgs:
        s.head = s.msgs.popleft()
        s.send( s.head )

  def done( s ):
    return not s.msgs
  
  def line_trace( s ):
    return "{}".format( 
        "" if s.head is not None 
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
    # s.recv = CalleePort( s._recv )

  @method_port( lambda : True )
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
    return s.idx >= s.len( s.msgs )
  
  def line_trace( s ):
    tmp = s.head
    s.head = None
    return "{}".format( 
      "" if s.head is None else str( tmp ) ).ljust( s.trace_len )

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( ComponentLevel6 ):
  
  def construct( s, dut, src_msgs, sink_msgs ):
   
    s.src     = TestSrc ( src_msgs  )
    s.sink    = TestSink( sink_msgs )
    s.dut     = dut

    # Connections
    print s.dut.send
    print s.sink.recv
    s.connect( s.src.send, s.dut.enq  )
    s.connect( s.dut.send, s.sink.recv )


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

  th.apply( SimpleCLSim )

  # Run simluation

  ncycles = 0
  print "{}:{}".format( ncycles, th.line_trace() )
  while not th.done() and ncycles < max_cycles:
    th.tick()
    ncycles += 1
    print "{}:{}".format( ncycles, th.line_trace() )
  
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
    s.send = CallerPort()

    @s.update
    def send_msg():
      if s.send.rdy() and not s.empty():
        s.send( s.deq() )

  def empty( s ):
    return s.element is None

  @method_port( lambda s : s.empty() )
  def enq( s, ele ):
    s.element = ele

  @method_port( lambda s: not s.empty() )
  def deq( s ):
    ret = s.element
    s.element = None
    return ret
  
  def line_trace( s ):
    return "{}".format( "" if s.element is None else str( s.element ) )

# Test the SimpleQueue as a SW data structure. 

def test_queue_sw():

  q = SimpleQueue()
  q.elaborate()

  assert q.enq.rdy()
  assert q.empty()
  assert not q.deq.rdy()

  q.enq( Bits16( 128) )
  assert not q.enq.rdy()
  assert not q.empty()
  assert q.deq.rdy()

  assert q.deq() == Bits16( 128 )
  assert q.enq.rdy()
  assert q.empty()
  assert not q.deq.rdy()

# Test the SimpleQueue as a CL model.

def test_queue_cl():
  q    = SimpleQueue()
  msgs = [ Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ) ]
  th = TestHarness( q, msgs, msgs )
  run_cl_sim( th )

#-------------------------------------------------------------------------
# QueueIncr
#-------------------------------------------------------------------------

