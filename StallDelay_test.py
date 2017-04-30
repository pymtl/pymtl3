from pymtl import *
from pclib.test   import TestSourceCL, TestSinkCL
from pclib.cl     import PipeQueue, BypassQueue, RandomStall, FixDelay
from MixingQueues_test import CLRTLEnqAdapter

class TestHarness( MethodsConnection ):

  def __init__( s ):
    Type = int

    s.src  = TestSourceCL( Type, [ 1,2,3,4,5,6,7,8 ] )
    s.q1   = PipeQueue(1)
    s.q2   = PipeQueue(1)
    s.sink = TestSinkCL( Type, [ 1,2,3,4,5,6,7,8 ] )

    #---------------------------------------------------------------------
    # src.enq(out) --> q1.enq
    #---------------------------------------------------------------------

    s.src.send     |= s.q1.enq
    s.src.send_rdy |= s.q1.enq_rdy

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

    s.stall = RandomStall(0.5)
    s.stall.send     |= s.sink.recv
    s.stall.send_rdy |= s.sink.recv_rdy

    @s.update
    def up_q2_CL_deq_stall_CL_enq_adapter():
      if s.stall.recv_rdy() & s.q2.deq_rdy():
        s.stall.recv( s.q2.deq() )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.q1.line_trace()+">"+s.q2.line_trace()+" >>> "+s.sink.line_trace()

def test_stalldelay():
  A = TestHarness()
  A.elaborate()
  A.print_schedule()
  print

  T = 0
  while not A.done():
    T += 1
    A.cycle()
    print "{:3d}:".format(T), A.line_trace()

