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
        s.A[16:30] = Bits( 14, 0xff )

      @s.update
      def up_rd_12_30():
        assert s.A[12:30] == 0xff0

  _test_model( Top )

# write two disjoint slices, but one slice is not read at all
def test_write_two_disjoint_slices_no_reader():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits(32) )

      @s.update
      def up_wr_0_16():
        s.A[0:16] = Bits( 16, 0xff )

      @s.update
      def up_wr_16_30():
        s.A[16:30] = Bits( 14, 0xff )

      @s.update
      def up_rd_17_30():
        assert s.A[16:30] == 0xff

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown no constraint exception.")

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

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown two-writer conflict exception.")

# write two slices and a single bit
def test_write_two_slices_and_bit():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits(32) )

      @s.update
      def up_wr_0_16():
        s.A[0:16] = Bits( 16, 0xff )

      @s.update
      def up_wr_16_30():
        s.A[16:30] = Bits( 14, 0xff )

      @s.update
      def up_wr_30_31():
        s.A[30] = Bits( 0, 1 )

      @s.update
      def up_rd_A():
        print s.A[0:17]

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown no constraint exception.")

# write a slice and a single bit, but they are overlapped
def test_write_slices_and_bit_overlapped():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits(32) )

      @s.update
      def up_wr_0_16():
        s.A[0:16] = Bits( 16, 0xff )

      @s.update
      def up_wr_15():
        s.A[15] = Bits( 0, 1 )

      @s.update
      def up_rd_A():
        print s.A[0:17]

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown two-writer conflict exception.")
