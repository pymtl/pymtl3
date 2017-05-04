from pymtl import *
from pclib.test   import TestSourceEnRdy, TestSource, TestSinkEnRdy, TestSink
from pclib.update import PipeQueue1RTL, BypassQueue1RTL, NormalQueue1RTL
from pclib.cl     import PipeQueue, BypassQueue
from pclib.ifcs   import *

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

    if src == q1:
      s.q1.enq |= s.src.send

    else:
      if   src == 'rtl' and q1 == 'cl':
        s.src_q1 = EnqIfcRTL_EnqIfcCL( Type )
      elif src == 'cl'  and q1 == 'rtl':
        s.src_q1 = EnqIfcCL_EnqIfcRTL( Type )

      s.src.send    |= s.src_q1.recv
      s.src_q1.send |= s.q1.enq

    #---------------------------------------------------------------------
    # q1.deq --> q2.enq
    #---------------------------------------------------------------------

    if q1 == 'rtl' and q2 == 'rtl':
      s.q1_q2 = DeqIfcRTL_EnqIfcRTL( Type )

    if q1 == 'rtl' and q2 == 'cl':
      s.q1_q2 = DeqIfcRTL_EnqIfcCL( Type )

    if q1 == 'cl' and q2 == 'rtl':
      s.q1_q2 = DeqIfcCL_EnqIfcRTL( Type )

    if q1 == 'cl' and q2 == 'cl':
      s.q1_q2 = DeqIfcCL_EnqIfcCL( Type )

    s.q1.deq     |= s.q1_q2.recv
    s.q1_q2.send |= s.q2.enq

    #---------------------------------------------------------------------
    # q2.deq --> sink.enq(recv)
    #---------------------------------------------------------------------

    if q2 == 'rtl' and sink == 'rtl':
      s.q2_sink = DeqIfcRTL_EnqIfcRTL( Type )

    if q2 == 'rtl' and sink == 'cl':
      s.q2_sink = DeqIfcRTL_EnqIfcCL( Type )

    if q2 == 'cl'  and sink == 'rtl':
      s.q2_sink = DeqIfcCL_EnqIfcRTL( Type )

    if q2 == 'cl' and sink == 'cl':
      s.q2_sink = DeqIfcCL_EnqIfcCL( Type )

    s.q2.deq       |= s.q2_sink.recv
    s.q2_sink.send |= s.sink.recv

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
