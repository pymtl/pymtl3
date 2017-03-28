from pymtl import *

from pclib.bundle import TestSource
from pclib.bundle import TestSink
from pclib.bundle import ValRdyBundle

def _test_model( model ):
  m = model()
  m.elaborate()
  m.print_schedule()

  for x in xrange(10):
    m.cycle()

# write two disjoint slices
def test_write_two_disjoint_slices():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits(32) )

      @s.update
      def up_wr_0_16():
        s.A[0:16] = Bits( 16, 0xff )

      @s.update
      def up_wr_16_30():
        s.A[16:32][0:14] = Bits( 14, 0xff )

  _test_model( Top )

# write two disjoint slices and a single bit
def test_write_two_slices_and_bit():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits(32) )

      @s.update
      def up_wr_0_16():
        s.A[0:16] = Bits( 16, 0xff )

      @s.update
      def up_wr_16_30():
        s.A[16:32][0:14] = Bits( 14, 0xff )

      @s.update
      def up_wr_30_32():
        s.A[30] = Bits( 0, 1 )

      @s.update
      def up_rd_A():
        x = s.A

  _test_model( Top )

# write two overlapping slices

def test_write_two_overlapping_slices():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits(32) )

      @s.update
      def up_wr_0_24():
        s.A[0:24] = Bits( 16, 0xff )

      @s.update
      def up_wr_8_32():
        s.A[8:32] = Bits( 16, 0xff )

      @s.update
      def up_rd_A():
        x = s.A

  _test_model( Top )
