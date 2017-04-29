from pymtl import *
from collections import deque
from pclib.test   import TestSourceEnRdy, TestSourceCL, TestSinkEnRdy, TestSinkCL
from pclib.update import PipeQueue1RTL, BypassQueue1RTL, NormalQueue1RTL
from pclib.cl     import PipeQueue, BypassQueue

class TestHarness( MethodsConnection ):

  def __init__( s, src = 'rtl', q1 = 'rtl', q2 = 'rtl', sink = 'rtl' ):
    Type = int

    assert (src  == 'rtl' or src   == 'cl') and \
           (q1   == 'rtl' or q1    == 'cl') and \
           (q2   == 'rtl' or q2    == 'cl') and \
           (sink == 'rtl' or sink  == 'cl'), "src/q1/q2/sink: Only 'cl' and 'rtl' are accepted"

    if src  == 'rtl': s.src = TestSourceEnRdy( Type, [ 1,2,3,4 ] )
    else:             s.src = TestSourceCL( Type, [ 1,2,3,4 ] )

    if q1   == 'rtl': s.q1 = PipeQueue1RTL(Type)
    else:             s.q1 = PipeQueue(1)

    if q2   == 'rtl': s.q2 = PipeQueue1RTL(Type)
    else:             s.q2 = PipeQueue(1)

    if sink == 'rtl': s.sink = TestSinkEnRdy( Type, [ 1,2,3,4 ], accept_interval=2 )
    else:             s.sink = TestSinkCL( Type, [ 1,2,3,4 ], accept_interval=2 )

    #---------------------------------------------------------------------
    # src.enq(out) --> q1.enq
    #---------------------------------------------------------------------

    if src == 'rtl' and q1 == 'rtl':
      s.q1.enq |= s.src.send

    if src == 'rtl' and q1 == 'cl':
      @s.update
      def up_src_RTL_enq_q1_CL_enq_adapter_rdyblk():
        s.src.send.rdy = s.q1.enq_rdy()
      @s.update
      def up_src_RTL_enq_q1_CL_enq_adapter_enblk():
        if s.src.send.en:
          s.q1.enq( s.src.send.msg )

    if src == 'cl'  and q1 == 'rtl':
      # ?????????????????????
      pass

    if src == 'cl'  and q1 == 'cl':
      s.src.send     |= s.q1.enq
      s.src.send_rdy |= s.q1.enq_rdy

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

    if q1 == 'cl' and q2 == 'rtl':
      @s.update
      def up_q1_CL_deq_q2_RTL_enq_adapter():

        s.q2.enq.en = Bits1( False )

        if s.q2.enq.rdy & s.q1.deq_rdy():
          s.q2.enq.en  = Bits1( True )
          s.q2.enq.msg = s.q1.deq()

    if q1 == 'cl' and q2 == 'cl':
      @s.update
      def up_q1_CL_deq_q2_CL_enq_adapter():
        if s.q2.enq_rdy() & s.q1.deq_rdy():
          s.q2.enq( s.q1.deq() )

    #---------------------------------------------------------------------
    # q2.deq --> sink.enq(recv)
    #---------------------------------------------------------------------
    
    if q2 == 'rtl' and sink == 'rtl':
      @s.update
      def up_q2_RTL_deq_sink_RTL_enq_adapter():
        s.q2.deq.en  = Bits1( False )

        s.sink.recv.en  = Bits1( False )
        s.sink.recv.msg = Type()

        if s.sink.recv.rdy & s.q2.deq.rdy:
          s.q2.deq.en = Bits1( True )

          s.sink.recv.en = Bits1( True )
          s.sink.recv.msg = s.q2.deq.msg

    if q2 == 'rtl' and sink == 'cl':
      @s.update
      def up_q2_RTL_deq_sink_CL_enq_adapter():
        s.q2.deq.en = Bits1( False )

        if s.sink.recv_rdy() & s.q2.deq.rdy:
          s.q2.deq.en = Bits1( True )
          s.sink.recv( s.q2.deq.msg )

    if q2 == 'cl'  and sink == 'rtl':
      @s.update
      def up_q2_CL_deq_sink_RTL_enq_adapter_rdyblk():
        s.sink.recv.en = Bits1( False )

        if s.sink.recv.rdy & s.q2.deq_rdy():
          s.sink.recv.en  = Bits1( True )
          s.sink.recv.msg = s.q2.deq()

    if q2 == 'cl' and sink == 'cl':
      @s.update
      def up_q2_CL_deq_sink_CL_enq_adapter():
        if s.sink.recv_rdy() & s.q2.deq_rdy():
          s.sink.recv( s.q2.deq() )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.q1.line_trace()+">"+s.q2.line_trace()+" >>> "+s.sink.line_trace()

import pytest
from pclib.test import mk_test_case_table

test_case_table = mk_test_case_table([
  (         "src    q1     q2     sink" ),
  [ "0000", 'rtl', 'rtl', 'rtl', 'rtl' ], # 0000
  [ "0001", 'rtl', 'rtl', 'rtl', 'cl'  ], # 0001
  [ "0010", 'rtl', 'rtl', 'cl' , 'rtl' ], # 0010
  [ "0011", 'rtl', 'rtl', 'cl' , 'cl'  ], # 0011
  [ "0100", 'rtl', 'cl' , 'rtl', 'rtl' ], # 0100
  [ "0101", 'rtl', 'cl' , 'rtl', 'cl'  ], # 0101
  [ "0110", 'rtl', 'cl' , 'cl' , 'rtl' ], # 0110
  [ "0111", 'rtl', 'cl' , 'cl' , 'cl'  ], # 0111
  # [ "1000", 'cl' , 'rtl', 'rtl', 'rtl' ], # 1000
  # [ "1001", 'cl' , 'rtl', 'rtl', 'cl'  ], # 1001
  # [ "1010", 'cl' , 'rtl', 'cl' , 'rtl' ], # 1010
  # [ "1011", 'cl' , 'rtl', 'cl' , 'cl'  ], # 1011
  [ "1100", 'cl' , 'cl' , 'rtl', 'rtl' ], # 1100
  [ "1101", 'cl' , 'cl' , 'rtl', 'cl'  ], # 1101
  [ "1110", 'cl' , 'cl' , 'cl' , 'rtl' ], # 1110
  [ "1111", 'cl' , 'cl' , 'cl' , 'cl'  ], # 1111
])

@pytest.mark.parametrize( **test_case_table )
def test_mixing( test_params ):
  A = TestHarness( test_params.src, test_params.q1, test_params.q2, test_params.sink)
  A.elaborate()
  print 

  T = 0
  while not A.done():
    T += 1
    A.cycle()
    print "{:3d}:".format(T), A.line_trace()
