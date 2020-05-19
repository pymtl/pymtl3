from pymtl3.datatypes import Bits32
from pymtl3.dsl import *
from pymtl3.dsl.errors import UpblkCyclicError

from ..PassGroups import Mamba2020


def test_very_deep_dag():

  class Inner(Component):
    def construct( s ):
      s.in_ = InPort(Bits32)
      s.out = OutPort(Bits32)

      @update
      def up():
        s.out @= s.in_ + 1

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
      @update_ff
      def ff():
        if s.reset:
          s.out <<= 0
        else:
          s.out <<= s.out + s.inners[N-1].out

    def line_trace( s ):
      return str(s.inners[-1].out) + " " + str(s.out)

  N = 2000
  A = Top( N )

  A.apply( Mamba2020() )
  A.sim_reset()

  T = 0
  while T < 5:
    assert A.out == T * N
    A.sim_tick()
    T += 1
  return A

def test_combinational_loop():

  class Top(Component):

    def construct( s ):
      s.a = Wire(32)
      s.b = Wire(32)
      s.c = Wire(32)
      s.d = Wire(32)

      @update
      def up1():
        s.b @= s.d + 1

      @update
      def up2():
        s.c @= s.b + 1

      @update
      def up3():
        s.d @= s.c + 1
        print("up3 prints out d =", s.d)

    def line_trace( s ):
      return "a {} | b {} | c {} | d {}" \
              .format( s.a, s.b, s.c, s.d )

  A = Top()
  A.apply( Mamba2020() )

  try:
    A.sim_reset()
  except UpblkCyclicError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown UpblkCyclicError.")

def test_equal_top_level():
  class A(Component):
    def construct( s ):
      @update
      def up():
        print(1)

  a = A()
  a.apply( Mamba2020() )
  a.sim_reset()

  try:
    a.reset = 0
    a.sim_tick()
  except AssertionError as e:
    print(e)
    assert str(e).startswith("Please use @= to assign top level InPort")
    return
  raise Exception("Should've thrown AssertionError")

def test_update_once():

  class A(Component):
    @method_port
    def recv( s, v ):
      s.v = v

    def construct( s ):
      s.send = CallerPort()

      s.v = None
      @update_once
      def up():
        if s.v is not None:
          s.send( s.v )

      s.add_constraints( M(s.recv) < U(up) )

  class Top(Component):
    def construct( s ):
      s.a = A()
      s.b = A()
      s.a.send //= s.b.recv
      s.b.send //= s.a.recv

  t = Top()
  t.elaborate()
  try:
    t.apply( Mamba2020() )
  except UpblkCyclicError as e:
    print(e)
    return

  raise Exception("Should've thrown UpblkCyclicError")
