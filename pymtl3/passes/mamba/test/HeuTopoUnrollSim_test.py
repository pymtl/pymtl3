from pymtl3.dsl import *

from ..PassGroups import HeuTopoUnrollSim


def test_very_deep_dag():

  class Inner(Component):
    def construct( s ):
      s.in_ = InPort(int)
      s.out = OutPort(int)

      @s.update
      def up():
        s.out = s.in_ + 1

    def done( s ):
      return True

    def line_trace( s ):
      return "{} > {}".format( s.a, s.b, s.c, s.d )

  class Top(Component):
    def construct( s, N=2000 ):
      s.inners = [ Inner() for i in range(N) ]
      for i in range(N-1):
        s.inners[i].out //= s.inners[i+1].in_

    def line_trace( s ):
      return str(s.inners[-1].out)

  A = Top()

  A.apply( HeuTopoUnrollSim() )

  T = 0
  while T < 5:
    A.tick()
    print(A.line_trace())
    T += 1
  return A
