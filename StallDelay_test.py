from pymtl import *
from pclib.test   import TestSourceCL, TestSinkCL
from pclib.cl     import PipeQueue, BypassQueue, RandomStall, RandomDelay, PipelinedDelay
from MixingQueues_test import CLRTLEnqAdapter

class TestHarness( MethodsConnection ):

  def __init__( s, src_max_delay=3, sink_stall=0.5, sink_delay=3 ):
    Type = int

    s.src    = TestSourceCL( Type, [ Bits8(x) for x in [1,2,3,4,5,6,7,8] ] )
    s.rdelay = RandomDelay( src_max_delay )
    s.q1     = PipeQueue(1)
    s.q2     = PipeQueue(1)
    s.pipe   = PipelinedDelay( sink_delay )
    s.stall  = RandomStall( sink_stall, 0x3 )
    s.sink   = TestSinkCL( Type, [ Bits8(x) for x in [1,2,3,4,5,6,7,8] ] )

    #---------------------------------------------------------------------
    # src.enq(out) --> randomdelay --> q1.enq
    #---------------------------------------------------------------------

    s.src.send        |= s.rdelay.recv
    s.src.send_rdy    |= s.rdelay.recv_rdy
    s.rdelay.send     |= s.q1.enq
    s.rdelay.send_rdy |= s.q1.enq_rdy

    #---------------------------------------------------------------------
    # q1.deq --> q2.enq
    #---------------------------------------------------------------------

    @s.update
    def up_q1_CL_deq_q2_CL_enq_adapter():
      if s.q2.enq_rdy() & s.q1.deq_rdy():
        s.q2.enq( s.q1.deq() )

    #---------------------------------------------------------------------
    # q2.deq --> pipe -> stall --> sink.enq(recv)
    #---------------------------------------------------------------------

    @s.update
    def up_q2_CL_deq_stall_CL_enq_adapter():
      if s.pipe.recv_rdy() & s.q2.deq_rdy():
        s.pipe.recv( s.q2.deq() )

    s.pipe.send      |= s.stall.recv
    s.pipe.send_rdy  |= s.stall.recv_rdy

    s.stall.send     |= s.sink.recv
    s.stall.send_rdy |= s.sink.recv_rdy

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace() +" ("+ s.rdelay.line_trace()+ ") >>> " + \
           s.q1.line_trace()+" > "+s.q2.line_trace() + " > " + \
           " ("+s.pipe.line_trace()+")"+s.stall.line_trace() + \
           " >>> "+s.sink.line_trace()

def test_src_point5delay3_sink_point5delay2():
  A = TestHarness( src_max_delay=3, sink_stall=0.5, sink_delay=2 )
  A.elaborate()
  A.print_schedule()
  print

  T = 0
  while not A.done():
    T += 1
    A.cycle()
    print "{:3d}:".format(T), A.line_trace()
