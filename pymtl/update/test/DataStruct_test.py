from pymtl import *

from pclib.bundle import TestSource
from pclib.bundle import TestSink
from pclib.bundle import ValRdyBundle

class ABMsg( object ):

  def __init__( s, a=0, b=0 ):
    s.a = Bits( 32, a )
    s.b = b

def test_wr_wire_read_member():

  class Top(Updates):
    def __init__( s ):
      s.wire  = Wire( ABMsg )

      @s.update
      def up_copy():
        s.wire = ABMsg( 123, 12 )

      @s.update
      def up_out():
        assert s.wire.a == 123 and s.wire.b == 12

  A = Top()
  A.elaborate()
  A.print_schedule()

  for x in xrange(10):
    A.cycle()

def test_wr_member_connect_member():

  class Top(Updates):
    def __init__( s ):
      s.wire  = Wire( ABMsg )
      s.wire2 = Wire( ABMsg )

      s.wire.a |= s.wire2.a
      s.wire.b |= s.wire2.b

      @s.update
      def up_copy():
        s.wire.a = Bits(32, 123)
        s.wire.b = 12

      @s.update
      def up_out():
        assert s.wire2.a == 123 and s.wire2.b == 12

  A = Top()
  A.elaborate()
  A.print_schedule()
  for x in xrange(10):
    A.cycle()

def test_wr_wire_connect_member():

  class Top(Updates):
    def __init__( s ):
      s.wire  = Wire( ABMsg )
      s.wire2 = Wire( ABMsg )

      s.wire.a |= s.wire2.a
      s.wire.b |= s.wire2.b

      @s.update
      def up_copy():
        s.wire = ABMsg( 123, 12 )

      @s.update
      def up_out():
        assert s.wire2.a == 123 and s.wire2.b == 12

  A = Top()
  A.elaborate()
  A.print_schedule()

  for x in xrange(10):
    A.cycle()
