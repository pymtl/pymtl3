from pymtl import *

def test_simple():

  class Top(UpdateComponent):

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
  A.elaborate()
  


def test_cyclic_dependency():

  class Top(UpdateComponent):

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
    A.elaborate()
  except Exception:
    return
  raise Exception("Should've thrown cyclic dependency exception.")

def test_upblock_same_name():

  class Top(UpdateComponent):

    def __init__( s ):

      @s.update
      def upA():
        pass

      @s.update
      def upA():
        pass

  try:
    A = Top()
  except Exception:
    return
  raise Exception("Should've thrown name conflict exception.")

def test_add_loopback():

  from pclib import TestSource
  from pclib import TestSink

  class Top(UpdateComponent):

    def __init__( s ):

      s.src  = TestSource( [4,3,2,1] )
      s.sink = TestSink  ( ["?",(4+1),(3+1)+(4+1),(2+1)+(3+1)+(4+1),(1+1)+(2+1)+(3+1)+(4+1)] )

      s.wire0 = 0
      s.wire1 = 0

      @s.update
      def up_from_src():
        s.wire0 = s.src.out + 1

      up_src = s.src.get_update_block("up_src")

      s.add_constraints(
        U(up_src) < U(up_from_src),
      )

      s.reg0 = 0

      @s.update
      def upA():
        s.reg0 = s.wire0 + s.wire1

      @s.update
      def up_to_sink_and_loop_back():
        s.sink.in_ = s.reg0
        s.wire1 = s.reg0

      s.add_constraints(
        U(upA) < U(up_to_sink_and_loop_back),
        U(upA) < U(up_from_src),
      )

      up_sink = s.sink.get_update_block("up_sink")

      s.add_constraints(
        U(up_to_sink_and_loop_back) < U(up_sink),
      )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
            "w0=%s > r0=%s > w1=%s" % (s.wire0,s.reg0,s.wire1) + \
             " >>> " + s.sink.line_trace()

  A = Top()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()
