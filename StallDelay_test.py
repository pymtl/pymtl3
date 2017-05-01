from pymtl import *
from pclib.test   import TestSourceCL, TestSinkCL
from pclib.cl     import PipeQueue, BypassQueue, RandomStall, RandomDelay, PipelinedDelay
from MixingQueues_test import CLRTLEnqAdapter

class TestHarness( MethodsConnection ):

  def __init__( s, stall1=0.5, delay1=3, stall2=0.5, delay2=3 ):
    Type = int

    s.src    = TestSourceCL( Type, [ Bits8(1),Bits8(2),Bits8(3),Bits8(4) ] )
    s.stall1 = RandomStall( 0, 0x2 )
    s.delay1 = RandomDelay( delay1 )
    s.q1     = PipeQueue(1)
    s.q2     = PipeQueue(1)
    s.sink   = TestSinkCL( Type, [ Bits8(1),Bits8(2),Bits8(3),Bits8(4) ] )

    #---------------------------------------------------------------------
    # src.enq(out) --> q1.enq
    #---------------------------------------------------------------------

    s.src.send        |= s.delay1.recv
    s.src.send_rdy    |= s.delay1.recv_rdy
    s.delay1.send     |= s.stall1.recv
    s.delay1.send_rdy |= s.stall1.recv_rdy
    s.stall1.send     |= s.q1.enq
    s.stall1.send_rdy |= s.q1.enq_rdy

    #---------------------------------------------------------------------
    # q1.deq --> q2.enq
    #---------------------------------------------------------------------

    @s.update
    def up_q1_CL_deq_q2_CL_enq_adapter():
      if s.q2.enq_rdy() & s.q1.deq_rdy():
        s.q2.enq( s.q1.deq() )

    #---------------------------------------------------------------------
    # q2.deq --> stall --> sink.enq(recv)
    #---------------------------------------------------------------------

    s.stall2 = RandomStall( stall2, 0x3 )

    @s.update
    def up_q2_CL_deq_stall_CL_enq_adapter():
      if s.stall2.recv_rdy() & s.q2.deq_rdy():
        s.stall2.recv( s.q2.deq() )

    s.stall2.send     |= s.sink.recv
    s.stall2.send_rdy |= s.sink.recv_rdy

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace() +" ("+ s.delay1.line_trace()+ ") >>> " + \
           s.q1.line_trace()+" > "+s.q2.line_trace() + " > " +\
           s.stall2.line_trace() + " >>> "+s.sink.line_trace()

def test_src_point5delay3_sink_point5delay2():
  A = TestHarness( stall1=0.5, delay1=3, stall2=0.5, delay2=2 )
  A.elaborate()
  A.print_schedule()
  print

  T = 0
  while not A.done():
    T += 1
    A.cycle()
    print "{:3d}:".format(T), A.line_trace()
