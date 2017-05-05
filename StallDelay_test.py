from pymtl import *
from pclib.test   import TestSourceCL, TestSinkCL
from pclib.cl     import PipeQueue, BypassQueue, RandomStall, RandomDelay, PipelinedDelay

class TestHarnessAllKinds( MethodsAdapt ):

  def __init__( s, src_max_delay=3, sink_stall=0.5, sink_delay=3 ):
    Type = int

    s.src    = TestSourceCL( Type, [ Bits8(x) for x in [1,2,3,4,5,6,7,8] ] )
    s.rdelay = RandomDelay( src_max_delay )
    s.q1     = PipeQueue(Type, 1)
    s.q2     = PipeQueue(Type, 1)
    s.pipe   = PipelinedDelay( sink_delay )
    s.stall  = RandomStall( sink_stall, 0x3 )
    s.sink   = TestSinkCL( Type, [ Bits8(x) for x in [1,2,3,4,5,6,7,8] ] )

    # src.send --> randomdelay --> q1.enq
    # q1.deq <-> q2.enq
    # q2.deq <-> pipe -> stall --> sink.enq(recv)

    s.src.send    |= s.rdelay.recv
    s.rdelay.send |= s.q1.enq

    s.connect_ifcs( s.q1.deq, s.q2.enq )
    s.connect_ifcs( s.q2.deq, s.pipe.recv )

    s.pipe.send   |= s.stall.recv
    s.stall.send  |= s.sink.recv

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" "+s.rdelay.line_trace()+ " >>> " + \
           s.q1.line_trace()+" > "+s.q2.line_trace() + " >>> " + \
           s.pipe.line_trace()+" "+s.stall.line_trace() + " " + \
           s.sink.line_trace()

from pclib.test   import TestSource, TestSink

class TestHarness( MethodsAdapt ):

  def __init__( s, src_max_delay=3, sink_max_delay=3 ):
    Type = int

    s.src    = TestSource( Type, [ Bits8(x) for x in [1,2,3,4,5,6,7,8] ], src_max_delay )
    s.q1     = PipeQueue(Type, 1)
    s.q2     = PipeQueue(Type, 1)
    s.sink   = TestSink  ( Type, [ Bits8(x) for x in [1,2,3,4,5,6,7,8] ], sink_max_delay )

    # src.send --> q1.enq
    # q1.deq <-> q2.enq
    # q2.deq <-> sink.recv

    s.src.send |= s.q1.enq

    s.connect_ifcs( s.q1.deq, s.q2.enq )
    s.connect_ifcs( s.q2.deq, s.sink.recv )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace() + " >>> " + \
           s.q1.line_trace()+" > "+s.q2.line_trace() + " >>> " + \
           s.sink.line_trace()

def test_all_kinds_src_maxdelay3_sink_point5delay2():
  A = TestHarnessAllKinds( src_max_delay=3, sink_stall=0.5, sink_delay=2 )
  A.elaborate()
  A.print_schedule()
  print

  T = 0
  while not A.done():
    T += 1
    A.cycle()
    print "{:3d}:".format(T), A.line_trace()

def test_src_maxdelay4_sink_maxdelay5():
  A = TestHarness( src_max_delay=4, sink_max_delay=5 )
  A.elaborate()
  A.print_schedule()
  print

  T = 0
  while not A.done():
    T += 1
    A.cycle()
    print "{:3d}:".format(T), A.line_trace()
