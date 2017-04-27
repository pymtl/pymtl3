from pymtl import *
from collections import deque
from pclib.test   import TestSourceEnRdy, TestSinkEnRdy
from pclib.update import PipeQueue1RTL, BypassQueue1RTL, NormalQueue1RTL
from pclib.cl     import PipeQueue, BypassQueue

class TestHarness( MethodsConnection ):

  def __init__( s ):
    Type = int

    s.src  = TestSourceEnRdy( Type, [ 1,2,3,4 ])
    s.q1   = PipeQueue1RTL(Type)
    s.q2   = PipeQueue1RTL(Type)
    s.sink = TestSinkEnRdy( Type, [ 1,2,3,4 ], accept_interval=1 )

    #---------------------------------------------------------------------
    # src.enq(out) --> q1.enq
    #---------------------------------------------------------------------
    s.q1.enq |= s.src.out

    # @s.update
    # def up_src_RTL_enq_q1_CL_enq_adapter():

      # s.src.enq.

      # if s.src.enq.rdy & s.q1.enq_rdy():
        # s.q1.enq( s.q1.deq() )

    #---------------------------------------------------------------------
    # q1.deq --> q2.enq
    #---------------------------------------------------------------------

    # q1 is RTL, q2 is RTL

    @s.update
    def up_q1_RTL_deq_q2_RTL_enq_adapter():
      s.q1.deq.en  = Bits1( False )

      s.q2.enq.en  = Bits1( False )
      s.q2.enq.msg = Type()

      if s.q2.enq.rdy & s.q1.deq.rdy:
        s.q1.deq.en = Bits1( True )

        s.q2.enq.en = Bits1( True )
        s.q2.enq.msg = s.q1.deq.msg

    # q1 is CL, q2 is CL

    # @s.update
    # def up_q1_CL_deq_q2_CL_enq_adapter():

      # if s.q2.enq_rdy() & s.q1.deq_rdy():
        # s.q2.enq( s.q1.deq() )

    # q1 is RTL, q2 is CL

    # @s.update
    # def up_q1_RTL_deq_q2_CL_enq_adapter():

      # s.q1.deq.en = Bits1( False )

      # if s.q2.enq_rdy() & s.q1.deq.rdy:
        # s.q1.deq.en = Bits1( True )
        # s.q2.enq( s.q1.deq.msg )

    # q1 is CL, q2 is RTL

    # @s.update
    # def up_q1_CL_deq_q2_RTL_enq_adapter():

      # s.q2.enq.en = Bits1( False )

      # if s.q2.enq.rdy & s.q1.deq_rdy():
        # s.q2.enq.en  = Bits1( True )
        # s.q2.enq.msg = s.q1.deq()

    #---------------------------------------------------------------------
    # q2.deq --> sink.deq(in_)
    #---------------------------------------------------------------------
    s.q2.deq |= s.sink.in_

    # q2 is CL, sink is RTL
    # @s.update
    # def up_q2_CL_deq_sink_RTL_deq_adapter():

      # s.sink.in_.rdy = Bits1( False )
      # if s.q2.deq_rdy():
        # s.sink.in_.rdy = Bits1( True )
        # s.sink.in_.msg = s.q2.deq()
        # print s.sink.in_.msg

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.q1.line_trace()+">"+s.q2.line_trace()+" >>> "+s.sink.line_trace()

if __name__ == "__main__":
  A = TestHarness()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()
