from pymtl import *
from collections import deque
from pclib.update import Reg, RegEn, Mux, PipeQueue1RTL, BypassQueue1RTL, NormalQueue1RTL
from pclib.ifcs   import EnRdyBundle

class TestSource( Updates ):

  def __init__( s, input_ = [] ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!"
    s.input_ = deque( input_ ) # deque.popleft() is faster

    s.out = EnRdyBundle( int )

    @s.update
    def up_src_msg():
      s.out.en  = Bits1( len(s.input_) > 0 ) & s.out.rdy
      s.out.msg = 0 if not s.input_ else s.input_[0]

      if s.out.en and s.input_:
        s.input_.popleft()

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return s.out.line_trace()

class TestSink( Updates ):

  def __init__( s, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!"
    s.answer = deque( answer )

    s.in_ = EnRdyBundle( int )

    s.ts = 0
    @s.update
    def up_sink_rdy():
      s.ts = (s.ts + 1) % 1
      if not s.ts:
        s.in_.en = Bits1( len(s.answer) > 0 ) & s.in_.rdy
      else:
        s.in_.en = Bits1( False ) & s.in_.rdy

    @s.update
    def up_sink_msg():
      if s.in_.en:
        ref = s.answer.popleft()
        ans = s.in_.msg

        assert ref == ans or ref == "?", "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.answer

  def line_trace( s ):
    return s.in_.line_trace()

class TestHarness( Updates ):

  def __init__( s ):

    s.src  = TestSource( [ 1,2,3,4 ])
    s.q1   = PipeQueue1RTL(int)
    s.q2   = PipeQueue1RTL(int)
    s.sink = TestSink( [ 1,2,3,4 ] )

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
