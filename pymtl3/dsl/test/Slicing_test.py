"""
========================================================================
Slicing_test.py
========================================================================

Author : Shunning Jiang
Date   : Aug 23, 2018
"""
from pymtl3.datatypes import Bits2, Bits4, Bits14, Bits16, Bits24, Bits32
from pymtl3.dsl.ComponentLevel1 import update
from pymtl3.dsl.ComponentLevel3 import ComponentLevel3, connect
from pymtl3.dsl.Connectable import Wire
from pymtl3.dsl.errors import MultiWriterError, NoWriterError

from .sim_utils import simple_sim_pass

# Shunning: Note that we now have @= as a hook for LHS, we can safely
# assigning constants
# >>> s.A[0:16] @= 0xff
# instead of s.A[0:16] @= Bits16( 0xff )

def _test_model( cls ):
  A = cls()
  A.elaborate()
  simple_sim_pass( A, 0x123 )

  for i in range(10):
    A.tick()

# write two disjoint slices
def test_write_two_disjoint_slices():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_0_16():
        s.A[0:16] @= Bits16( 0xff )

      @update
      def up_wr_16_30():
        s.A[16:30] @= Bits14( 0xff )

      @update
      def up_rd_12_30():
        assert s.A[12:30] == 0xff0

  _test_model( Top )

# write two disjoint slices, but one slice is not read at all
def test_write_two_disjoint_slices_no_reader():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_0_16():
        s.A[0:16] @= Bits16( 0xff )

      @update
      def up_wr_16_30():
        s.A[16:30] @= Bits14( 0xff )

      @update
      def up_rd_17_30():
        assert s.A[16:30] == 0xff

  m = Top()
  m.elaborate()
  simple_sim_pass( m, 0x123 )

  # assert len(m._all_constraints) == 1
  # x, y = list(m._all_constraints)[0]

  # assert  m._all_id_upblk[x].__name__ == "up_wr_16_30" and \
          # m._all_id_upblk[y].__name__ == "up_rd_17_30" # only one constraint


# write two overlapping slices
def test_write_two_overlapping_slices():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_0_24():
        s.A[0:24] @= Bits24( 0xff )

      @update
      def up_wr_8_32():
        s.A[8:32] @= Bits24( 0xff )

      @update
      def up_rd_A():
        x = s.A

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")

# write two slices and a single bit
def test_write_two_slices_and_bit():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_0_16():
        s.A[0:16] @= 0xff

      @update
      def up_wr_16_30():
        s.A[16:30] @= Bits14( 0xff )

      @update
      def up_wr_30_31():
        s.A[30] @= 1

      @update
      def up_rd_A():
        print(s.A[0:17])

  m = Top()
  m.elaborate()
  simple_sim_pass( m, 0x123 )

  # assert len(m._all_constraints) == 2
  # _, x = list(m._all_constraints)[0]
  # _, y = list(m._all_constraints)[1]

  # two constraints are: up_wr_0_16 < up_rd_A and up_wr_16_30 < up_rd_A
  # assert  m._all_id_upblk[x].__name__ == "up_rd_A" and \
          # m._all_id_upblk[y].__name__ == "up_rd_A"

# write a slice and a single bit, but they are overlapped
def test_write_slices_and_bit_overlapped():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_0_16():
        s.A[0:16] @= 0xff

      @update
      def up_wr_15():
        s.A[15] @= 1

      @update
      def up_rd_A():
        print(s.A[0:17])

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")

# write a slice and there are two reader
def test_multiple_readers():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_8_24():
        s.A[8:24] @= Bits16( 0x1234 )

      @update
      def up_rd_0_12():
        assert s.A[0:12] == 0x400

      @update
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

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_A():
        s.A @= Bits32( 123 )

      @update
      def up_rd_As():
        assert s.A[0:16] == 123

  _test_model( Top )

# RD A[s] - WR A[t], intersect
def test_rd_As_wr_At_impl_intersect():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_At():
        s.A[8:24] @= Bits16( 0xff )

      @update
      def up_rd_As():
        assert s.A[0:16] == 0xff00

  _test_model( Top )

# RD A[s] - WR A[t], not intersect
def test_rd_As_wr_At_impl_disjoint():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_At():
        s.A[16:32] @= Bits16( 0xff )

      @update
      def up_rd_As():
        assert s.A[0:16] == 0

  m = Top()
  m.elaborate()
  simple_sim_pass( m, 0x123 )

  # assert len(m._all_constraints) == 0 # no constraint at all!

# WR A[s] - WR A
def test_wr_As_wr_A_conflict():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_As():
        s.A[1:3] @= Bits2( 2 )

      @update
      def up_wr_A():
        s.A @= Bits32( 123 )

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")

# WR A[s] - WR A[t], intersect
def test_wr_As_wr_At_intersect():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_As():
        s.A[1:3] @= Bits2( 2 )

      @update
      def up_wr_At():
        s.A[2:4] @= Bits2( 2 )

      @update
      def up_rd_A():
        z = s.A

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")

# WR A[s] - WR A[t], not intersect
def test_wr_As_wr_At_disjoint():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_As():
        s.A[1:3] @= Bits2( 2 )

      @update
      def up_wr_At():
        s.A[5:7] @= Bits2( 2 )

      @update
      def up_rd_A():
        z = s.A

  _test_model( Top )

# WR A[s] - RD A
def test_wr_As_rd_A_impl():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_As():
        s.A[1:3] @= Bits2( 2 )

      @update
      def up_rd_A():
        z = s.A

  _test_model( Top )

# WR A[s] - RD A, RD A[t], intersect
def test_wr_As_rd_A_rd_At_can_schedule():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_As():
        s.A[1:3] @= Bits2( 2 )

      @update
      def up_rd_A():
        z = s.A

      @update
      def up_rd_As():
        assert s.A[2:4] == 1

  _test_model( Top )

# WR A[s] - RD A, RD A[t], not intersect
def test_wr_As_rd_A_rd_At_cannot_schedule():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_As():
        s.A[1:3] @= Bits2( 2 )

      @update
      def up_rd_A():
        z = s.A

      @update
      def up_rd_At():
        assert s.A[3:5] == 0

  m = Top()
  m.elaborate()
  simple_sim_pass( m, 0x123 )

  # assert len(m._all_constraints) == 1
  # x, y = list(m._all_constraints)[0]

  # assert  m._all_id_upblk[x].__name__ == "up_wr_As" and \
          # m._all_id_upblk[y].__name__ == "up_rd_A" # only one constraint

# WR A - RD A[s], RD A[t]
def test_wr_A_rd_slices_can_schedule():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_A():
        s.A @= 0x12345678

      @update
      def up_rd_As():
        assert s.A[0:16] == 0x5678

      @update
      def up_rd_At():
        assert s.A[8:24] == 0x3456

  _test_model( Top )

# WR A[s] - RD A, RD A[t], not intersect
def test_wr_As_rd_A_rd_At_bit_cannot_schedule():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( Bits32 )

      @update
      def up_wr_As():
        s.A[0:16] @= Bits16( 0x1234 )

      @update
      def up_rd_A():
        z = s.A

      @update
      def up_rd_At():
        assert s.A[16] == 0

  m = Top()
  m.elaborate()
  simple_sim_pass( m, 0x123 )

  # assert len(m._all_constraints) == 1
  # x, y = list(m._all_constraints)[0]

  # assert  m._all_id_upblk[x].__name__ == "up_wr_As" and \
          # m._all_id_upblk[y].__name__ == "up_rd_A" # only one constraint

# RD A[s] - A|=x, WR x
def test_connect_rd_As_wr_x_conn_A_impl():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( Bits32 )

      connect( s.A, s.x )

      @update
      def up_wr_x():
        s.x @= Bits32( 123 )

      @update
      def up_rd_As():
        assert s.A[0:16] == 123

  _test_model( Top )

# RD A[s] - A[t]|=x, WR x, intersect
def test_connect_rd_As_wr_x_conn_At_impl():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      connect( s.A[0:24], s.x )

      @update
      def up_wr_x():
        s.x @= Bits24( 0x123456 )

      @update
      def up_rd_As():
        assert s.A[0:16] == 0x3456

  _test_model( Top )

# RD A[s] - A[t]|=x, WR x, not intersect
def test_connect_rd_As_wr_x_conn_At_disjoint():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      connect( s.A[0:24], s.x )

      @update
      def up_wr_x():
        s.x @= Bits24( 0x123456 )

      @update
      def up_rd_As():
        assert s.A[24:32] == 0

  m = Top()
  m.elaborate()
  simple_sim_pass( m, 0x123 )

  # assert len(m._all_constraints) == 1
  # x, y = list(m._all_constraints)[0]

  # assert  m._all_id_upblk[x].__name__ == "up_wr_x" and \
          # m._all_id_upblk[y].__name__ == "s_x__1" # connection block

# WR A[s] - A|=x
def test_connect_wr_As_rd_x_conn_A_mark_writer():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( Bits32 )

      connect( s.x, s.A )

      @update
      def up_wr_As():
        s.A[0:24] @= Bits24( 0x123456 )

  _test_model( Top )

# WR A[s] - A|=x, WR x
def test_connect_wr_As_wr_x_conn_A_conflict():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( Bits32 )

      connect( s.x, s.A )

      @update
      def up_wr_As():
        s.A[0:24] @= Bits24( 0x123456 )

      @update
      def up_wr_x():
        s.x @= Bits32( 0x87654321 )

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")

# WR A[s] - A[t]|=x, intersect
def test_connect_wr_As_rd_x_conn_At_mark_writer():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      connect( s.x, s.A[8:32] )

      @update
      def up_wr_As():
        s.A[0:24] @= Bits24( 0x123456 )

  _test_model( Top )

# WR A[s] - A[t]|=x, not intersect
def test_connect_wr_As_rd_x_conn_At_no_driver():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      connect( s.x, s.A[8:32] )

      @update
      def up_wr_As():
        s.A[0:4] @= Bits4( 0xf )

  try:
    _test_model( Top )
  except NoWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown NoWriterError.")

# WR A[s] - A[t]|=x, WR x, intersect
def test_connect_wr_As_wr_x_conn_At_conflict():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      connect( s.x, s.A[8:32] )

      @update
      def up_wr_As():
        s.A[0:24] @= Bits24( 0x123456 )

      @update
      def up_wr_x():
        s.x @= Bits24( 0x654321 )

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")

# WR A[s] - A[t]|=x, WR x, not intersect
def test_connect_wr_As_wr_x_conn_At_disjoint():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      connect( s.x, s.A[8:32] )

      @update
      def up_wr_As():
        s.A[0:4] @= Bits4( 0xf )

      @update
      def up_wr_x():
        s.x @= Bits24( 0x654321 )

      @update
      def up_rd_A():
        assert s.A == 0x6543210f

  _test_model( Top )

# A[s]|=x, WR x - RD A
def test_connect_wr_x_conn_As_rd_A_impl():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      connect( s.A[8:32], s.x )

      @update
      def up_wr_x():
        s.x @= Bits24( 0x123456 )

      @update
      def up_rd_A():
        assert s.A == 0x12345600

  _test_model( Top )

# A[s]|=x, WR x - WR A
def test_connect_wr_x_conn_As_wr_A_conflict():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits24 )
      s.y  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      connect( s.A[8:32], s.x )
      connect( s.x, s.y )

      @update
      def up_wr_x():
        s.x @= Bits24( 0x123456 )

      @update
      def up_wr_A():
        s.A @= Bits32( 0x12345678 )

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")

# A[s]|=x - WR A
def test_connect_rd_x_conn_As_wr_A_mark_writer():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )

      connect( s.A[8:32], s.x )

      @update
      def up_wr_A():
        s.A @= Bits32( 0x12345678 )

      @update
      def up_rd_x():
        assert s.x == 0x123456

  _test_model( Top )

# A[s]|=x, WR x - A|=y, WR y
def test_connect_wr_x_conn_As_wr_y_conn_A_conflict():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )
      s.y  = Wire( Bits32 )

      connect( s.A[8:32], s.x )
      connect( s.A      , s.y )

      @update
      def up_wr_x():
        s.x @= Bits24( 0x123456 )

      @update
      def up_wr_y():
        s.y @= Bits32( 0x12345678 )

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")

# A[s]|=x, WR x - A[t]|=y, WR y, intersect
def test_connect_wr_x_conn_As_wr_y_conn_At_conflict():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )
      s.y  = Wire( Bits16 )

      connect( s.A[8:32], s.x )
      connect( s.A[0:16], s.y )

      @update
      def up_wr_x():
        s.x @= Bits24( 0x123456 )

      @update
      def up_wr_y():
        s.y @= Bits16( 0x1234 )

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")

# A[s]|=x, WR x - A[t]|=y, WR y, not intersect
def test_connect_wr_x_conn_As_wr_y_conn_At_disjoint():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )
      s.y  = Wire( Bits4 )

      connect( s.A[8:32], s.x )
      connect( s.A[0:4],  s.y )

      @update
      def up_wr_x():
        s.x @= Bits24( 0x123456 )

      @update
      def up_wr_y():
        s.y @= Bits4( 0xf )

      @update
      def up_rd_A():
        assert s.A == 0x1234560f

  _test_model( Top )

# A[s]|=x, WR x - A|=y, RD y
def test_connect_wr_x_conn_As_rd_y_conn_A_mark_writer():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )
      s.y  = Wire( Bits32 )

      connect( s.A[8:32], s.x )
      connect( s.A,       s.y )

      @update
      def up_wr_x():
        s.x @= Bits24( 0x123456 )

      @update
      def up_rd_y():
        assert s.y == 0x12345600

  _test_model( Top )

# A[s]|=x - A|=y, WR y
def test_connect_rd_x_conn_As_wr_y_conn_A_mark_writer():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )
      s.y  = Wire( Bits32 )

      connect( s.A[8:32], s.x )
      connect( s.A,       s.y )

      @update
      def up_rd_x():
        assert s.x == 0x123456

      @update
      def up_wr_y():
        s.y @= Bits32( 0x12345678 )

  _test_model( Top )

# A[s]|=x - A[t]|=y, WR y, intersect
def test_connect_rd_x_conn_As_wr_y_conn_At_mark_writer():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x = Wire( Bits24 )
      s.A = Wire( Bits32 )
      s.y = Wire( Bits16 )

      connect( s.A[8:32], s.x )
      connect( s.A[0:16], s.y )

      @update
      def up_rd_x():
        assert s.x == 0x12

      @update
      def up_wr_y():
        s.y @= Bits16( 0x1234 )

  _test_model( Top )

# A[s]|=x - A[t]|=y, WR y, not intersect
def test_connect_rd_x_conn_As_wr_y_conn_no_driver():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits24 )
      s.A  = Wire( Bits32 )
      s.y  = Wire( Bits4 )

      connect( s.A[8:32], s.x )
      connect( s.A[0:4 ], s.y )

      @update
      def up_rd_x():
        assert s.x == 0

      @update
      def up_wr_y():
        s.y @= Bits4( 0xf )

  try:
    _test_model( Top )
  except NoWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown NoWriterError.")

def test_iterative_find_nets():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.w  = Wire( Bits32 )
      s.x  = Wire( Bits32 )
      s.y  = Wire( Bits32 )
      s.z  = Wire( Bits32 )

      connect( s.w[0:16],  s.x[8:24] ) # net1
      connect( s.x[16:32], s.y[0:16] ) # net2
      connect( s.y[8:24],  s.z[0:16] ) # net3

      @update
      def up_wr_s_w():
        s.w @= Bits32( 0x12345678 )

  _test_model( Top )

def test_multiple_sibling_slices():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.A  = Wire( Bits32 )
      s.x  = Wire( Bits16 )
      s.y  = Wire( Bits16 )
      s.z  = Wire( Bits16 )

      connect( s.A[0:16], s.x ) # net1

      connect( s.A[8:24], s.y ) # net2

      connect( s.A[16:32], s.z ) # net3

      @update
      def up_wr_s_w():
        s.x @= Bits16( 0x1234 )

  try:
    _test_model( Top )
  except NoWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown NoWriterError.")

def test_multiple_write_same_slice():

  class A( ComponentLevel3 ):
    def construct( s ):
      s.out = Wire( Bits32 )
      s.wire = Wire( Bits32 )
      connect( s.out, s.wire[0:32] )

      @update
      def comb_upblk():
        s.wire[0:16]  @= 0
        s.wire[16:32] @= 1

  a = A()
  a.elaborate()

def test_multiple_write_same_slice_with_overlap():

  class A( ComponentLevel3 ):
    def construct( s ):
      s.out = Wire( Bits32 )
      s.wire = Wire( Bits32 )
      connect( s.out, s.wire[0:32] )

      s.wire2 = Wire( Bits24 )
      connect( s.wire2[0:24], s.wire[8:32] )

      @update
      def comb_upblk():
        s.wire[0:16]  @= 0
        s.wire2[0:24] @= 1

  try:
    _test_model( A )
  except MultiWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")
