from pymtl import *
from collections import deque
from pclib.update import PipeQueue1RTL, BypassQueue1RTL, NormalQueue1RTL
from pclib.test   import TestSourceEnRdy, TestSinkEnRdy

class TestHarness( Updates ):

  def __init__( s ):

    s.src  = TestSourceEnRdy( int, [ 1,2,3,4 ])
    s.q1   = BypassQueue1RTL(int)
    s.q2   = PipeQueue1RTL(int)
    s.sink = TestSinkEnRdy( int, [ 1,2,3,4 ], accept_interval=2 )

    s.q1.enq   |= s.src.out
    s.sink.in_ |= s.q2.deq

    @s.update
    def up_q2_enq_q1_deq_adapter():
      s.q2.enq.msg = s.q1.deq.msg

      s.q2.enq.en = s.q2.enq.rdy & s.q1.deq.rdy
      s.q1.deq.en = s.q2.enq.rdy & s.q1.deq.rdy

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.q1.line_trace()+">"+s.q2.line_trace()+" >>> "+"rdy:%d "%s.sink.in_.rdy+s.sink.line_trace()

if __name__ == "__main__":
  A = TestHarness()
  A.elaborate()
  A.print_schedule()

  # while not A.done():
  for i in xrange(20):
    A.cycle()
    print A.line_trace()
