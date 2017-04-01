from pymtl import *

from pclib.test import TestSource, TestSink
from pclib.ifcs import ValRdyBundle

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

  _test_model( Top )

# write two disjoint slices, but one slice is not read at all
def test_write_two_disjoint_slices_no_reader():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_0_16():
        s.A[0:16] = Bits16( 0xff )

      @s.update
      def up_wr_16_30():
        s.A[16:30] = Bits14( 0xff )

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
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_0_24():
        s.A[0:24] = Bits24( 0xff )

      @s.update
      def up_wr_8_32():
        s.A[8:32] = Bits24( 0xff )

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
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_0_16():
        s.A[0:16] = Bits16( 0xff )

      @s.update
      def up_wr_16_30():
        s.A[16:30] = Bits14( 0xff )

      @s.update
      def up_wr_30_31():
        s.A[30] = Bits1( 1 )

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
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_0_16():
        s.A[0:16] = Bits16( 0xff )

      @s.update
      def up_wr_15():
        s.A[15] = Bits1( 1 )

      @s.update
      def up_rd_A():
        print s.A[0:17]

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown two-writer conflict exception.")

# write a slice and there are two reader
def test_multiple_readers():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_8_24():
        s.A[8:24] = Bits16( 0x1234 )

      @s.update
      def up_rd_0_12():
        assert s.A[0:12] == 0x400

      @s.update
      def up_rd_bunch():
        assert s.A[23] == 0
        assert s.A[22] == 0
        assert s.A[21] == 0
        assert s.A[20] == 1
        assert s.A[19] == 0
        assert s.A[18] == 0
        assert s.A[17] == 1
        assert s.A[16] == 0

  _test_model( Top )

# 1. WR A[s], RD A    (A[s] (=) A, SAME AS data struct)
#    WR A[s], WR A    (detect 2-writer conflict, SAME AS data struct)
#    WR A[s], RD A[t] (A[s] (=) A[t] if s intersects t)
#    WR A[s], WR A[t] (detect 2-writer conflict if s intersects t)

# 2. WR A   , RD A[s] (A[s] (=) A, SAME AS data struct)

# 3. WR A[s], A   |=y, RD y (mark A as writer in net {A,y}, SAME AS data struct)
#    WR A[s], A   |=y, WR y (detect 2-writer conflict, SAME AS data struct)
#    WR A[s], A[t]|=y, RD y (mark A[t] as writer in net {A[t],y} if s intersects t)
#    WR A[s], A[t]|=y, WR y (detect 2-writer conflict if s intersects t)

# 4. WR A   , A[s]|=y, RD y (mark A[s] as writer in net {A[s],y}, SAME AS data struct)
#    WR A   , A[s]|=y, WR y (detect 2-writer conflict, SAME AS data struct)

# 5. WR x, x|=A[s], RD A    (A[s] (=) A, SAME AS data struct)
#    WR x, x|=A[s], RD A[t] (A[s] (=) A[t] if s intersects t)

# 6. WR x, x|=A   , RD A[s] (A[s] (=) A, SAME AS data struct)

# 7. WR x, x|=A[s], A   |=y, RD y (mark A as writer and implicit constraint)
#    WR x, x|=A[s], A   |=y, WR y (detect 2-writer conflict)
#    WR x, x|=A[s], A[t]|=y, RD y (mark A[t] as writer and implicit constraint if s intersects t)
#    WR x, x|=A[s], A[t]|=y, WR y (detect 2-writer conflict if s intersects t)

# 8. WR x, x|=A   , A[s]|=y, RD y (mark A[s] as writer in net {A[s],y}, SAME AS data struct)

# --------------------------------------------------------------------------

# RD A[s]
#  - WR A          (A[s] (=) A,                          SAME AS data struct)
#  - WR A[t]       (A[s] (=) A[t]                          if s intersects t)
#  - A   |=x, WR x (A[s] (=) A,                          SAME AS data struct)
#  - A[t]|=x, WR x (A[s] (=) A[t]                          if s intersects t)

# WR A[s]
#  - RD A          (A[s] (=) A,                          SAME AS data struct)
#  - WR A          (detect 2-writer conflict,            SAME AS data struct)
#  - WR A[t]       (detect 2-writer conflict               if s intersects t)
#  - A   |=x       (mark A as writer in net {A,x},       SAME AS data struct)
#  - A   |=x, WR x (detect 2-writer conflict,            SAME AS data struct)
#  - A[t]|=x       (mark A[t] as writer in net {A[t],x}    if s intersects t)
#  - A[t]|=x, WR x (detect 2-writer conflict               if s intersects t)

# A[s]|=x
#  - WR A          (mark A[s] as writer in net {A[s],x}, SAME AS data struct)
#  - A|=y, WR y    (mark A[s] as writer in net {A[s],x}, SAME AS data struct)
#  - A[t]|=y, WR y (mark A[s] as writer in net {A[s],x},   if s intersects t)

# A[s]|=x, WR x
#  - RD A          (A[s] (=) A,                          SAME AS data struct)
#  - WR A          (detect 2-writer conflict,            SAME AS data struct)
#  - A   |=y       (mark A as writer in net {A,y}        SAME AS data struct)
#  - A   |=y, WR y (detect 2-writer conflict,            SAME AS data struct)
#  - A[t]|=y, WR y (detect 2-writer conflict               if s intersects t)

# RD A[s] - WR A
def test_rd_As_wr_A_impl():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_A():
        s.A = Bits32( 123 )

      @s.update
      def up_rd_As():
        assert s.A[0:16] == 123

  _test_model( Top )

# RD A[s] - WR A[t], intersect
def test_rd_As_wr_At_impl_intersect():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_At():
        s.A[8:24] = Bits16( 0xff )

      @s.update
      def up_rd_As():
        assert s.A[0:16] == 0xff00

  _test_model( Top )

# RD A[s] - WR A[t], not intersect
def test_rd_As_wr_At_impl_disjoint():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_At():
        s.A[16:32] = Bits16( 0xff )

      @s.update
      def up_rd_As():
        assert s.A[0:16] == 0xff00

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown no constraint exception.")

# WR A[s] - WR A
def test_wr_As_wr_A_conflict():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_As():
        s.A[1:3] = Bits2( 2 )

      @s.update
      def up_wr_A():
        s.A = Bits32( 123 )

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown two-writer conflict exception.")

# WR A[s] - WR A[t], intersect
def test_wr_As_wr_At_intersect():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_As():
        s.A[1:3] = Bits2( 2 )

      @s.update
      def up_wr_At():
        s.A[2:4] = Bits2( 2 )

      @s.update
      def up_rd_A():
        z = s.A

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown two-writer conflict exception.")

# WR A[s] - WR A[t], not intersect
def test_wr_As_wr_At_disjoint():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_As():
        s.A[1:3] = Bits2( 2 )

      @s.update
      def up_wr_At():
        s.A[5:7] = Bits2( 2 )

      @s.update
      def up_rd_A():
        z = s.A

  _test_model( Top )

# WR A[s] - RD A
def test_wr_As_rd_A_impl():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_As():
        s.A[1:3] = Bits2( 2 )

      @s.update
      def up_rd_A():
        z = s.A

  _test_model( Top )

# WR A[s] - RD A, RD A[t], intersect
def test_wr_As_rd_A_rd_At_can_schedule():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_As():
        s.A[1:3] = Bits2( 2 )

      @s.update
      def up_rd_A():
        z = s.A

      @s.update
      def up_rd_As():
        assert s.A[2:4] == 1

  _test_model( Top )

# WR A[s] - RD A, RD A[t], not intersect
def test_wr_As_rd_A_rd_At_cannot_schedule():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_As():
        s.A[1:3] = Bits2( 2 )

      @s.update
      def up_rd_A():
        z = s.A

      @s.update
      def up_rd_At():
        assert s.A[3:5] == 0
  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown no constraint exception.")

# WR A - RD A[s], RD A[t]
def test_wr_A_rd_slices_can_schedule():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_A():
        s.A = Bits32( 0x12345678 )

      @s.update
      def up_rd_As():
        assert s.A[0:16] == 0x5678

      @s.update
      def up_rd_At():
        assert s.A[8:24] == 0x3456

  _test_model( Top )

# WR A[s] - RD A, RD A[t], not intersect
def test_wr_As_rd_A_rd_At_cannot_schedule():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( Bits32 )

      @s.update
      def up_wr_As():
        s.A[0:16] = Bits16( 0x1234 )

      @s.update
      def up_rd_A():
        z = s.A

      @s.update
      def up_rd_At():
        assert s.A[16] == 0

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown no constraint exception.")

# RD A[s] - A|=x, WR x
def test_connect_rd_As_wr_x_conn_A_impl():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( Bits32 )

      s.A |= s.x

      @s.update
      def up_wr_x():
        s.x = Bits32( 123 )

      @s.update
      def up_rd_As():
        assert s.A[0:16] == 123

  _test_model( Top )

# RD A[s] - A[t]|=x, WR x, intersect
def test_connect_rd_As_wr_x_conn_At_impl():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      s.A[0:24] |= s.x

      @s.update
      def up_wr_x():
        s.x = Bits24( 0x123456 )

      @s.update
      def up_rd_As():
        assert s.A[0:16] == 0x3456

  _test_model( Top )

# RD A[s] - A[t]|=x, WR x, not intersect
def test_connect_rd_As_wr_x_conn_At_disjoint():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      s.A[0:24] |= s.x

      @s.update
      def up_wr_x():
        s.x = Bits24( 0x123456 )

      @s.update
      def up_rd_As():
        assert s.A[24:32] == 0

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown no constraint exception.")

# WR A[s] - A|=x
def test_connect_wr_As_rd_x_conn_A_mark_writer():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      s.x |= s.A

      @s.update
      def up_wr_As():
        s.A[0:24] = Bits24( 0x123456 )

  _test_model( Top )

# WR A[s] - A|=x, WR x
def test_connect_wr_As_wr_x_conn_A_conflict():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      s.x |= s.A

      @s.update
      def up_wr_As():
        s.A[0:24] = Bits24( 0x123456 )

      @s.update
      def up_wr_x():
        s.x = Bits24( 0x654321 )

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown two-writer conflict exception.")

# WR A[s] - A[t]|=x, intersect
def test_connect_wr_As_rd_x_conn_At_mark_writer():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      s.x |= s.A[8:32]

      @s.update
      def up_wr_As():
        s.A[0:24] = Bits24( 0x123456 )

  _test_model( Top )

# WR A[s] - A[t]|=x, not intersect
def test_connect_wr_As_rd_x_conn_At_no_driver():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      s.x |= s.A[8:32]

      @s.update
      def up_wr_As():
        s.A[0:4] = Bits4( 0xf )

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown no driver exception.")

# WR A[s] - A[t]|=x, WR x, intersect
def test_connect_wr_As_wr_x_conn_At_conflict():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      s.x |= s.A[8:32]

      @s.update
      def up_wr_As():
        s.A[0:24] = Bits24( 0x123456 )

      @s.update
      def up_wr_x():
        s.x = Bits24( 0x654321 )

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown two-writer conflict exception.")

# WR A[s] - A[t]|=x, WR x, not intersect
def test_connect_wr_As_wr_x_conn_At_disjoint():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      s.x |= s.A[8:32]

      @s.update
      def up_wr_As():
        s.A[0:4] = Bits4( 0xf )

      @s.update
      def up_wr_x():
        s.x = Bits24( 0x654321 )

      @s.update
      def up_rd_A():
        assert s.A == 0x6543210f

  _test_model( Top )

# A[s]|=x, WR x - RD A
def test_connect_wr_x_conn_As_rd_A_impl():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      s.A[8:32] |= s.x

      @s.update
      def up_wr_x():
        s.x = Bits24( 0x123456 )

      @s.update
      def up_rd_A():
        assert s.A == 0x12345600

  _test_model( Top )

# A[s]|=x, WR x - WR A
def test_connect_wr_x_conn_As_wr_A_conflict():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.y  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      s.A[8:32] |= s.x
      s.x |= s.y

      @s.update
      def up_wr_x():
        s.x = Bits24( 0x123456 )

      @s.update
      def up_wr_A():
        s.A = Bits32( 0x12345678 )

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown two-writer conflict exception.")

# A[s]|=x - WR A
def test_connect_rd_x_conn_As_wr_A_mark_writer():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      s.A[8:32] |= s.x

      @s.update
      def up_wr_A():
        s.A = Bits32( 0x12345678 )

      @s.update
      def up_rd_x():
        assert s.x == 0x123456

  _test_model( Top )

# A[s]|=x, WR x - A|=y, WR y
def test_connect_wr_x_conn_As_wr_y_conn_A_conflict():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )
      s.y  = Wire( Bits32 )

      s.A[8:32] |= s.x
      s.A       |= s.y

      @s.update
      def up_wr_x():
        s.x = Bits24( 0x123456 )

      @s.update
      def up_wr_y():
        s.y = Bits32( 0x12345678 )

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown two-writer conflict exception.")

# A[s]|=x, WR x - A[t]|=y, WR y, intersect
def test_connect_wr_x_conn_As_wr_y_conn_At_conflict():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )
      s.y  = Wire( Bits16 )

      s.A[8:32] |= s.x
      s.A[0:16] |= s.y

      @s.update
      def up_wr_x():
        s.x = Bits24( 0x123456 )

      @s.update
      def up_wr_y():
        s.y = Bits16( 0x1234 )

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown two-writer conflict exception.")

# A[s]|=x, WR x - A[t]|=y, WR y, not intersect
def test_connect_wr_x_conn_As_wr_y_conn_At_disjoint():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )
      s.y  = Wire( Bits4 )

      s.A[8:32] |= s.x
      s.A[0:4]  |= s.y

      @s.update
      def up_wr_x():
        s.x = Bits24( 0x123456 )

      @s.update
      def up_wr_y():
        s.y = Bits4( 0xf )

      @s.update
      def up_rd_A():
        assert s.A == 0x1234560f

  _test_model( Top )

# A[s]|=x, WR x - A|=y, RD y
def test_connect_wr_x_conn_As_rd_y_conn_A_mark_writer():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )
      s.y  = Wire( Bits32 )

      s.A[8:32] |= s.x
      s.A       |= s.y

      @s.update
      def up_wr_x():
        s.x = Bits24( 0x123456 )

      @s.update
      def up_rd_y():
        assert s.y == 0x12345600

  _test_model( Top )

# A[s]|=x - A|=y, WR y
def test_connect_rd_x_conn_As_wr_y_conn_A_mark_writer():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )
      s.y  = Wire( Bits32 )

      s.A[8:32] |= s.x
      s.A       |= s.y

      @s.update
      def up_rd_x():
        assert s.x == 0x123456

      @s.update
      def up_wr_y():
        s.y = Bits32( 0x12345678 )

  _test_model( Top )

# A[s]|=x - A[t]|=y, WR y, intersect
def test_connect_rd_x_conn_As_wr_y_conn_At_mark_writer():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )
      s.y  = Wire( Bits16 )

      s.A[8:32] |= s.x
      s.A[0:16] |= s.y

      @s.update
      def up_rd_x():
        assert s.x == 0x12

      @s.update
      def up_wr_y():
        s.y = Bits16( 0x1234 )

  _test_model( Top )

# A[s]|=x - A[t]|=y, WR y, not intersect
def test_connect_rd_x_conn_As_wr_y_conn_no_driver():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )
      s.y  = Wire( Bits4 )

      s.A[8:32] |= s.x
      s.A[0:4 ] |= s.y

      @s.update
      def up_rd_x():
        assert s.x == 0

      @s.update
      def up_wr_y():
        s.y = Bits4( 0xf )

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown no driver exception.")

def test_iterative_find_nets():

  class Top(Updates):
    def __init__( s ):

      s.w  = Wire( Bits32 )
      s.x  = Wire( Bits32 )
      s.y  = Wire( Bits32 )
      s.z  = Wire( Bits32 )

      s.w[0:16]  |= s.x[8:24] # net1

      s.x[16:32] |= s.y[0:16] # net2

      s.y[8:24]  |= s.z[0:16] # net3

      @s.update
      def up_wr_s_w():
        s.w = Bits32( 0x12345678 )

  _test_model( Top )

def test_multiple_sibling_slices():

  class Top(Updates):
    def __init__( s ):

      s.A  = Wire( Bits32 )
      s.x  = Wire( Bits16 )
      s.y  = Wire( Bits16 )
      s.z  = Wire( Bits16 )

      s.A[0:16]  |= s.x # net1

      s.A[8:24]  |= s.y # net2

      s.A[16:32] |= s.z # net3

      @s.update
      def up_wr_s_w():
        s.x = Bits16( 0x1234 )

  try:
    _test_model( Top )
  except Exception as e:
    print "\nAssertion Error:", e
    return
  raise Exception("Should've thrown no driver exception.")
