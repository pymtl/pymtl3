from pymtl import *
from collections import deque
from pclib.test   import TestSourceEnRdy, TestSinkEnRdy
from pclib.update import PipeQueue1RTL, BypassQueue1RTL, NormalQueue1RTL
from pclib.cl     import PipeQueue, BypassQueue

class TestHarnessRTLSrcSink( MethodsConnection ):

  def __init__( s, q1 = 'rtl', q2 = 'rtl' ):
    Type = int

    assert (q1 == 'rtl' or q1 == 'cl') and (q2 == 'rtl' or q2 == 'cl'), "q1/q2: Only 'cl' and 'rtl' are accepted"

    # src and sink are always RTL
    # * src  has push/enq interface
    # * sink, however, has pull/deq interface

    s.src  = TestSourceEnRdy( Type, [ 1,2,3,4 ])
    s.sink = TestSinkEnRdy  ( Type, [ 1,2,3,4 ], accept_interval=1 )

    if q1 == 'rtl':  s.q1 = PipeQueue1RTL(Type)
    else:            s.q1 = PipeQueue(1)

    if q2 == 'rtl':  s.q2 = PipeQueue1RTL(Type)
    else:            s.q2 = PipeQueue(1)

    #---------------------------------------------------------------------
    # src.enq(out) --> q1.enq
    #---------------------------------------------------------------------

    if q1 == 'rtl':
      s.q1.enq |= s.src.out

    if q1 == 'cl':
      @s.update
      def up_src_RTL_enq_q1_CL_enq_adapter_rdyblk():
        s.src.out.rdy = s.q1.enq_rdy()
      @s.update
      def up_src_RTL_enq_q1_CL_enq_adapter_enblk():
        if s.src.out.en:
          s.q1.enq( s.src.out.msg )

    #---------------------------------------------------------------------
    # q1.deq --> q2.enq
    #---------------------------------------------------------------------

    if q1 == 'rtl' and q2 == 'rtl':
      @s.update
      def up_q1_RTL_deq_q2_RTL_enq_adapter():
        s.q1.deq.en  = Bits1( False )

        s.q2.enq.en  = Bits1( False )
        s.q2.enq.msg = Type()

        if s.q2.enq.rdy & s.q1.deq.rdy:
          s.q1.deq.en = Bits1( True )

          s.q2.enq.en = Bits1( True )
          s.q2.enq.msg = s.q1.deq.msg

    if q1 == 'rtl' and q2 == 'cl':
      @s.update
      def up_q1_RTL_deq_q2_CL_enq_adapter():

        s.q1.deq.en = Bits1( False )

        if s.q2.enq_rdy() & s.q1.deq.rdy:
          s.q1.deq.en = Bits1( True )
          s.q2.enq( s.q1.deq.msg )

    if q1 == 'cl' and q2 == 'cl':
      @s.update
      def up_q1_CL_deq_q2_CL_enq_adapter():
        if s.q2.enq_rdy() & s.q1.deq_rdy():
          s.q2.enq( s.q1.deq() )

    if q1 == 'cl' and q2 == 'rtl':
      @s.update
      def up_q1_CL_deq_q2_RTL_enq_adapter():

        s.q2.enq.en = Bits1( False )

        if s.q2.enq.rdy & s.q1.deq_rdy():
          s.q2.enq.en  = Bits1( True )
          s.q2.enq.msg = s.q1.deq()

    #---------------------------------------------------------------------
    # q2.deq --> sink.deq(in_)
    #---------------------------------------------------------------------
    
    if q2 == 'rtl':
      s.q2.deq |= s.sink.in_

    if q2 == 'cl':
      @s.update
      def up_q2_CL_deq_sink_RTL_deq_adapter_rdyblk():
        s.sink.in_.rdy = s.q2.deq_rdy()
      @s.update
      def up_q2_CL_deq_sink_RTL_deq_adapter_enblk():
        if s.sink.in_.en:
          s.sink.in_.msg = s.q2.deq()

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.q1.line_trace()+">"+s.q2.line_trace()+" >>> "+s.sink.line_trace()

if __name__ == "__main__":
  A = TestHarnessRTLSrcSink(q1='cl',q2='cl')
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()
