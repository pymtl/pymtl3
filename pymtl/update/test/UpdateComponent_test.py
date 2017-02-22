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
        upA < upB,
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
        upA < upB,
        upB < upA,
      )

  A = Top()
  try:
    A.elaborate()
  except Exception:
    return
  raise Exception("Should've thrown cyclic dependency exception.")
