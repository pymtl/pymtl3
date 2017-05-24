from pymtl import *
from collections import deque

def simulate( cls ):
  A = cls()
  sim = SimLevel2( A )

  while not A.done():
    sim.cycle()
    print A.line_trace()

class TestSource( UpdateWithVar ):

  def __init__( s, input_ ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!" 

    s.input_ = deque( input_ ) # deque.popleft() is faster
    s.out = Wire(int)

    @s.update
    def up_src():
      if not s.input_:
        s.out = 0
      else:
        s.out = s.input_.popleft()

  def done( s ):
    return not s.input_

  def line_trace( s ):
    return "%s" % s.out

class TestSink( UpdateWithVar ):

  def __init__( s, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!" 

    s.answer = deque( answer )
    s.in_ = Wire(int)

    @s.update
    def up_sink():
      if not s.answer:
        assert False, "Simulation has ended"
      else:
        ref = s.answer.popleft()
        ans = s.in_

        assert ref == ans or ref == "*", "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.answer

  def line_trace( s ):
    return "%s" % s.in_


def test_2d_array_vars():

  class Top(UpdateWithVar):

    def __init__( s ):

      s.src  = TestSource( [2,1,0,2,1,0] )
      s.sink = TestSink  ( ["*",(5+6),(3+4),(1+2),
                                (5+6),(3+4),(1+2)] )

      s.wire = [ [ Wire(int) for _ in xrange(2)] for _ in xrange(2) ]

      @s.update
      def up_from_src():
        s.wire[0][0] = s.src.out
        s.wire[0][1] = s.src.out + 1

      s.reg = Wire(int)

      @s.update
      def up_reg():
        s.reg = s.wire[0][0] + s.wire[0][1]

      s.add_constraints(
        U(up_reg) < RD(s.reg), # up_reg writes s.reg
      )

      @s.update
      def upA():
        for i in xrange(2):
          s.wire[1][i] = s.reg + i

      for i in xrange(2):
        s.add_constraints(
          U(up_reg) < WR(s.wire[0][i]), # up_reg reads  s.wire[0][i]
        )

      @s.update
      def up_to_sink():
        s.sink.in_ = s.wire[1][0] + s.wire[1][1]

      up_sink = s.sink.get_update_block("up_sink")

      s.add_constraints(
        U(upA)        < U(up_to_sink),
        U(up_to_sink) < U(up_sink),
      )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
             str(s.wire)+"r0=%s" % s.reg + \
             " >>> " + s.sink.line_trace()

  simulate( Top )

def test_wire_up_constraint():

  class Top(UpdateWithVar):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1,4,3,2,1] )
      s.sink = TestSink  ( [5,4,3,2,5,4,3,2] )

      @s.update
      def up_from_src():
        s.sink.in_ = s.src.out + 1

      s.add_constraints(
        U(up_from_src) < RD(s.sink.in_),
      )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
             " >>> " + s.sink.line_trace()

  simulate( Top )

# write two disjoint slices
def test_write_two_disjoint_slices():

  class Top(UpdateWithVar):
    def __init__( s ):
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_0_16():
        s.A[0:16] = Bits16( 0xff )

      @s.update
      def up_wr_16_30():
        s.A[16:30] = Bits16( 0xff )

      @s.update
      def up_rd_12_30():
        assert s.A[12:30] == 0xff0

  simulate( Top )

# WR A.b - RD A
def test_wr_A_b_rd_A_impl():

  class SomeMsg( object ):

    def __init__( s ):
      s.a = int
      s.b = Bits32

    def __call__( s, a = 0, b = Bits1() ):
      x = SomeMsg()
      x.a = x.a(a)
      x.b = x.b(b)
      return x

  class Top(UpdateWithVar):
    def __init__( s ):
      s.A  = Wire( SomeMsg() )

      @s.update
      def up_wr_A_b():
        s.A.b = 123

      @s.update
      def up_rd_A():
        z = s.A

  simulate( Top )
