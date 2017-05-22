from pymtl.components import UpdateOnly, U
from pymtl.tools import SimLevel1
from collections import deque

class TestSource( UpdateOnly ):

  def __init__( s, input_ ):
    assert type(input_) == list, "TestSrc only accepts a list of inputs!" 

    s.input_ = deque( input_ ) # deque.popleft() is faster
    s.out = 0

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

class TestSink( UpdateOnly ):

  def __init__( s, answer ):
    assert type(answer) == list, "TestSink only accepts a list of outputs!" 

    s.answer = deque( answer )
    s.in_ = 0

    @s.update
    def up_sink():
      if not s.answer:
        assert False, "Simulation has ended"
      else:
        ref = s.answer.popleft()
        ans = s.in_

        assert ref == ans, "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.answer

  def line_trace( s ):
    return "%s" % s.in_

def test_bb():

  class Top(UpdateOnly):

    def __init__( s ):

      @s.update
      def upA():
        pass

      @s.update
      def upB():
        pass

      s.add_constraints(
        U(upA) < U(upB),
      )

  A = Top()
  sim = SimLevel1( A )

def test_cyclic_dependency():

  class Top(UpdateOnly):

    def __init__( s ):

      @s.update
      def upA():
        pass

      @s.update
      def upB():
        pass

      s.add_constraints(
        U(upA) < U(upB),
        U(upB) < U(upA),
      )

  A = Top()
  try:
    sim = SimLevel1( A )
  except Exception as e:
    print e
    return
  raise Exception("Should've thrown cyclic dependency exception.")

def test_upblock_same_name():

  class Top(UpdateOnly):

    def __init__( s ):

      @s.update
      def upA():
        pass

      @s.update
      def upA():
        pass

  try:
    A = Top()
  except Exception as e:
    print e
    return
  raise Exception("Should've thrown name conflict exception.")

def test_register_behavior():

  class Top(UpdateOnly):

    def __init__( s ):

      s.src  = TestSource( [5,4,3,2,1] )
      s.sink = TestSink  ( [0,5,4,3,2] )

      s.wire0 = 0
      s.wire1 = 0

      @s.update
      def up_from_src():
        s.wire0 = s.src.out

      up_src = s.src.get_update_block("up_src")

      s.add_constraints(
        U(up_src) < U(up_from_src),
      )

      @s.update
      def up_reg():
        s.wire1 = s.wire0

      @s.update
      def up_to_sink():
        s.sink.in_ = s.wire1

      s.add_constraints(
        U(up_reg) < U(up_to_sink),
        U(up_reg) < U(up_from_src),
      )

      up_sink = s.sink.get_update_block("up_sink")

      s.add_constraints(
        U(up_to_sink) < U(up_sink),
      )

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0={} > w1={}".format(s.wire0,s.wire1) + \
             " >>> " + s.sink.line_trace()

  A = Top()
  sim = SimLevel1( A )
  for i in xrange(5):
    sim.tick()
    print sim.line_trace()
