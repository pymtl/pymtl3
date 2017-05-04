from pymtl import *
from pclib.test   import TestSourceEnRdy, TestSource, TestSinkEnRdy, TestSink
from pclib.update import PipeQueue1RTL, BypassQueue1RTL, NormalQueue1RTL
from pclib.cl     import PipeQueue, BypassQueue
from pclib.ifcs   import EnRdyBundle, EnqIfcCL, EnqIfcCL

class EnqRTL_EnqCL( MethodsConnection ):

  def __init__( s, Type ):

    s.recv = EnRdyBundle( Type )
    s.send = EnqIfcCL( Type )

    @s.update
    def up_rdyblk():
      s.recv.rdy = s.send.rdy()

    @s.update
    def up_enblk():
      if s.recv.en:
        s.send.enq( s.recv.msg )

class EnqCL_EnqRTL( MethodsConnection ):

  def __init__( s, Type ):

    s.msg = Wire( Type )
    s.en  = Wire( Bits1 )
    s.rdy = Wire( Bits1 )

    s.send = EnRdyBundle( Type )
    s.recv = EnqIfcCL( Type )
    s.recv.enq |= s.recv_
    s.recv.rdy |= s.recv_rdy_

    @s.update
    def up_rdyblk():
      s.rdy = s.send.rdy
      # I put it here because up_rdy < s.send
      s.en  = Bits1( False )
      s.msg = Type()

    @s.update
    def up_enblk():
      s.send.en  = s.en
      s.send.msg = s.msg

    s.add_constraints(
      U(up_rdyblk) < M(s.recv_rdy_),
      M(s.recv_  ) < U(up_enblk),
    )

  def recv_( s, msg ):
    s.msg = msg
    s.en  = Bits1( True )

  def recv_rdy_( s ):
    return s.rdy

class TestHarness( MethodsConnection ):

  def __init__( s, src = 'rtl', q1 = 'rtl', q2 = 'rtl', sink = 'rtl' ):
    Type = int

    assert (src  == 'rtl' or src   == 'cl') and \
           (q1   == 'rtl' or q1    == 'cl') and \
           (q2   == 'rtl' or q2    == 'cl') and \
           (sink == 'rtl' or sink  == 'cl'), "src/q1/q2/sink: Only 'cl' and 'rtl' are accepted"

    if src  == 'rtl': s.src = TestSourceEnRdy( Type, [ 1,2,3,4 ] )
    else:             s.src = TestSource( Type, [ 1,2,3,4 ], max_delay=2 )

    if q1   == 'rtl': s.q1 = PipeQueue1RTL(Type)
    else:             s.q1 = PipeQueue(Type, 1)

    if q2   == 'rtl': s.q2 = PipeQueue1RTL(Type)
    else:             s.q2 = PipeQueue(Type, 1)

    if sink == 'rtl': s.sink = TestSinkEnRdy( Type, [ 1,2,3,4 ], accept_interval=2 )
    else:             s.sink = TestSink( Type, [ 1,2,3,4 ], max_delay=2 )

    #---------------------------------------------------------------------
    # src.enq(out) --> q1.enq
    #---------------------------------------------------------------------

    if src == 'rtl' and q1 == 'rtl':
      s.q1.enq |= s.src.send

    if src == 'rtl' and q1 == 'cl':
      s.src_q1 = EnqRTL_EnqCL( Type )
      s.src.send    |= s.src_q1.recv
      s.src_q1.send |= s.q1.enq

    if src == 'cl'  and q1 == 'rtl':
      s.src_q1 = EnqCL_EnqRTL( Type )
      s.src.send    |= s.src_q1.recv
      s.src_q1.send |= s.q1.enq

    if src == 'cl'  and q1 == 'cl':
      s.src.send     |= s.q1.enq

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

        if s.q2.enq.rdy() & s.q1.deq.rdy:
          s.q1.deq.en = Bits1( True )
          s.q2.enq.enq( s.q1.deq.msg )

    if q1 == 'cl' and q2 == 'rtl':
      @s.update
      def up_q1_CL_deq_q2_RTL_enq_adapter():

        s.q2.enq.en = Bits1( False )

        if s.q2.enq.rdy & s.q1.deq.rdy():
          s.q2.enq.en  = Bits1( True )
          s.q2.enq.msg = s.q1.deq.deq()

    if q1 == 'cl' and q2 == 'cl':
      @s.update
      def up_q1_CL_deq_q2_CL_enq_adapter():
        if s.q2.enq.rdy() & s.q1.deq.rdy():
          s.q2.enq.enq( s.q1.deq.deq() )

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

        if s.sink.recv.rdy() & s.q2.deq.rdy:
          s.q2.deq.en = Bits1( True )
          s.sink.recv.enq( s.q2.deq.msg )

    if q2 == 'cl'  and sink == 'rtl':
      @s.update
      def up_q2_CL_deq_sink_RTL_enq_adapter_rdyblk():
        s.sink.recv.en = Bits1( False )

        if s.sink.recv.rdy & s.q2.deq.rdy():
          s.sink.recv.en  = Bits1( True )
          s.sink.recv.msg = s.q2.deq.deq()

    if q2 == 'cl' and sink == 'cl':
      @s.update
      def up_q2_CL_deq_sink_CL_enq_adapter():
        if s.sink.recv.rdy() & s.q2.deq.rdy():
          s.sink.recv.enq( s.q2.deq.deq() )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.q1.line_trace()+">"+s.q2.line_trace()+" >>> "+s.sink.line_trace()

import pytest
from pclib.test import mk_test_case_table

test_case_table = mk_test_case_table([
  (         "src    q1     q2     sink" ),
  [ "r-r-r-r", 'rtl', 'rtl', 'rtl', 'rtl' ],
  [ "r-r-r-c", 'rtl', 'rtl', 'rtl', 'cl'  ],
  [ "r-r-c-r", 'rtl', 'rtl', 'cl' , 'rtl' ],
  [ "r-r-c-c", 'rtl', 'rtl', 'cl' , 'cl'  ],
  [ "r-c-r-r", 'rtl', 'cl' , 'rtl', 'rtl' ],
  [ "r-c-r-c", 'rtl', 'cl' , 'rtl', 'cl'  ],
  [ "r-c-c-r", 'rtl', 'cl' , 'cl' , 'rtl' ],
  [ "r-c-c-c", 'rtl', 'cl' , 'cl' , 'cl'  ],
  [ "c-r-r-r", 'cl' , 'rtl', 'rtl', 'rtl' ],
  [ "c-r-r-c", 'cl' , 'rtl', 'rtl', 'cl'  ],
  [ "c-r-c-r", 'cl' , 'rtl', 'cl' , 'rtl' ],
  [ "c-r-c-c", 'cl' , 'rtl', 'cl' , 'cl'  ],
  [ "c-c-r-r", 'cl' , 'cl' , 'rtl', 'rtl' ],
  [ "c-c-r-c", 'cl' , 'cl' , 'rtl', 'cl'  ],
  [ "c-c-c-r", 'cl' , 'cl' , 'cl' , 'rtl' ],
  [ "c-c-c-c", 'cl' , 'cl' , 'cl' , 'cl'  ],
])

@pytest.mark.parametrize( **test_case_table )
def test_mixing( test_params ):
  A = TestHarness( test_params.src, test_params.q1, test_params.q2, test_params.sink)
  A.elaborate()
  A.print_schedule()
  print

  T = 0
  while not A.done():
    T += 1
    A.cycle()
    print "{:3d}:".format(T), A.line_trace()
