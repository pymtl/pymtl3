from pymtl import *
from pymtl.components import UpdateVar
from pymtl.passes     import SimUpdateVarPass
from collections import deque

def _test_model( cls ):
  A = cls()
  sim = SimUpdateVarPass(dump=True).execute( A )

  while not A.done():
    sim.tick()
    print A.line_trace()

class TestSource( UpdateVar ):

  def __init__( s, input_ ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!" 

    s.input_ = deque( input_ ) # deque.popleft() is faster
    s.out = OutVPort(int)

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

class TestSink( UpdateVar ):

  def __init__( s, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!" 

    s.answer = deque( answer )
    s.in_ = InVPort(int)

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

  class Top(UpdateVar):

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

  _test_model( Top )

def test_wire_up_constraint():

  class Top(UpdateVar):

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

  _test_model( Top )

# write two disjoint slices
def test_write_two_disjoint_slices():

  class Top(UpdateVar):
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

    def done( s ):
      return True

  _test_model( Top )

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

  class Top(UpdateVar):
    def __init__( s ):
      s.A  = Wire( SomeMsg() )

      @s.update
      def up_wr_A_b():
        s.A.b = 123

      @s.update
      def up_rd_A():
        z = s.A

    def done( s ):
      return True

  _test_model( Top )

def test_bb():

  class Top(UpdateVar):

    def __init__( s ):
      s.a = Wire(int)
      s.b = Wire(int)

      @s.update
      def upA():
        s.a = s.b + 1

      @s.update
      def upB():
        s.b = s.b + 1

    def done( s ):
      return True

  _test_model( Top )

def test_bb_cyclic_dependency():

  class Top(UpdateVar):

    def __init__( s ):
      s.a = Wire(int)
      s.b = Wire(int)

      @s.update
      def upA():
        s.a = s.b

      @s.update
      def upB():
        s.b = s.a

  try:
    _test_model( Top )
  except Exception:
    return
  raise Exception("Should've thrown cyclic dependency exception.")

def test_add_loopback():

  class Top(UpdateVar):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1] )
      s.sink = TestSink  ( ["*",(4+1),(3+1)+(4+1),(2+1)+(3+1)+(4+1),(1+1)+(2+1)+(3+1)+(4+1)] )

      s.wire0 = Wire(int)
      s.wire1 = Wire(int)

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      s.reg0 = Wire(int)

      @s.update
      def upA():
        s.reg0 = s.wire0 + s.wire1

      @s.update
      def up_to_sink_and_loop_back():
        s.sink.in_ = s.reg0
        s.wire1 = s.reg0

      s.add_constraints(
        U(upA) < WR(s.wire1),
        U(upA) < WR(s.wire0),
        U(upA) < RD(s.reg0), # also implicit
      )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0=%s > r0=%s > w1=%s" % (s.wire0,s.reg0,s.wire1) + \
             " >>> " + s.sink.line_trace()
  _test_model( Top )

def test_add_loopback_on_edge():

  class Top(UpdateVar):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1] )
      s.sink = TestSink  ( ["*",(4+1),(3+1)+(4+1),(2+1)+(3+1)+(4+1),(1+1)+(2+1)+(3+1)+(4+1)] )

      s.wire0 = Wire(int)
      s.wire1 = Wire(int)

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      s.reg0 = Wire(int)

      # UPDATE ON EDGE!
      @s.update_on_edge
      def upA():
        s.reg0 = s.wire0 + s.wire1

      @s.update
      def up_to_sink_and_loop_back():
        s.sink.in_ = s.reg0
        s.wire1 = s.reg0

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0=%s > r0=%s > w1=%s" % (s.wire0,s.reg0,s.wire1) + \
             " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_2d_array_vars_impl():

  class Top(UpdateVar):

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

      @s.update_on_edge
      def up_reg():
        s.reg = s.wire[0][0] + s.wire[0][1]

      @s.update
      def upA():
        for i in xrange(2):
          s.wire[1][i] = s.reg + i

      @s.update
      def up_to_sink():
        s.sink.in_ = s.wire[1][0] + s.wire[1][1]

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
             str(s.wire)+"r0=%s" % s.reg + \
             " >>> " + s.sink.line_trace()

  _test_model( Top )
