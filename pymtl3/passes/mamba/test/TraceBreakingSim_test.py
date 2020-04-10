from pymtl3.datatypes import Bits32
from pymtl3.dsl import *

from ..PassGroups import TraceBreakingSim


def test_very_deep_dag():

  class Inner(Component):
    def construct( s ):
      s.in_ = InPort(Bits32)
      s.out = OutPort(Bits32)

      @s.update
      def up():
        s.out = s.in_ + 1

    def done( s ):
      return True

    def line_trace( s ):
      return "{} > {}".format( s.a, s.b )

  class Top(Component):
    def construct( s, N=2000 ):
      s.inners = [ Inner() for i in range(N) ]
      for i in range(N-1):
        s.inners[i].out //= s.inners[i+1].in_

      s.out = OutPort(Bits32)
      @s.update_ff
      def ff():
        if s.reset:
          s.out <<= 0
        else:
          s.out <<= s.out + s.inners[N-1].out

    def line_trace( s ):
      return str(s.inners[-1].out) + " " + str(s.out)

  N = 2000
  A = Top( N )

  A.apply( TraceBreakingSim() )

  T = 0
  while T < 5:
    A.tick()
    print(A.line_trace())
    assert A.out == T * N
    T += 1
  return A
