"""
========================================================================
DataStruct_test.py
========================================================================

Author : Shunning Jiang
Date   : Apr 16, 2018
"""
from pymtl3.datatypes import Bits16, Bits32, bitstruct
from pymtl3.dsl.ComponentLevel1 import update
from pymtl3.dsl.ComponentLevel2 import update_ff
from pymtl3.dsl.ComponentLevel3 import ComponentLevel3, connect
from pymtl3.dsl.Connectable import InPort, OutPort, Wire
from pymtl3.dsl.errors import (
    MultiWriterError,
    NoWriterError,
    UpdateFFBlockWriteError,
    UpdateFFNonTopLevelSignalError,
)

from .sim_utils import simple_sim_pass


@bitstruct
class SomeMsg:
  a: Bits32
  b: Bits32

def _test_model( cls ):
  A = cls()
  A.elaborate()
  simple_sim_pass( A, 0x123 )

  for i in range(10):
    A.tick()

# All situations when we allow nested data struct:
#
# 1. WR A.b, RD A (need to recognize implicit constraint between A.b and A)
#    WR A.b, WR A (detect 2-writer conflict)
#
# 2. WR A, RD A.b (need to recognize implicit constraint between A.b and A)
#    WR A, WR A.b (detect 2-writer conflict)
#
# 3. WR A.b, A|=y, RD y (need to mark A as writer in net {A,y})
#    WR A.b, A|=y, WR y (detect 2-writer conflict)
#
# 4. WR A, A.b|=y, RD y (need to mark A.b as writer in net {A.b,y})
#    WR A, A.b|=y, WR y (detect 2-writer conflict)
#
# 5. WR x, x|=A.b, RD A (need to recognize implicit constraint between A.b and A because the generated connection block has A.b = x)
#    WR x, x|=A.b, WR A (detect 2-writer conflict)
#
# 6. WR x, x|=A, RD A.b (need to recognize implicit constraint between A.b and A because the generated connection block has A = x)
#    WR x, x|=A, WR A.b (detect 2-writer conflict)
#
# 7. WR x, x|=A.b, A|=y, RD y (need to mark A as writer and recognize the implicit constraint)
#    WR x, x|=A.b, A|=y, WR y (detect 2-writer conflict)
#
# 8. WR x, x|=A, A.b|=y, RD y (need to mark A.b as writer and recognize the implicit constraint)
#    WR x, x|=A, A.b|=y, WR y (detect 2-writer conflict)
#
# We fix A.b and see what can A.b's ancestors do:
#
# RD A.b
#  - WR A       (A (=) A.b)
#  - WR x, x|=A (A (=) A.b, THE SAME AS the first case thanks to the generated upblk)
#
# WR A.b
#  - RD A       (A (=) A.b)
#  - WR A       (detect 2-writer conflict)
#  - A|=x       (mark A as writer in net {A,x})
#  - A|=x, WR x (detect 2-writer conflict, THE SAME AS the second case thanks to the generated upblk)
#
# A.b|=x
#  - WR A       (mark A.b as writer in net {A.b,y})
#  - A|=y, WR y (mark A.b as writer and recognize the implicit constraint)
#
# A.b|=x, WR(x)
#  - RD A       (A (=) A.b)
#  - WR A       (detect 2-writer conflict)
#  - A|=y       (mark A as writer and recognize the implicit constraint)
#  - A|=y, WR y (detect 2-writer conflict)

# RD A.b - WR A
def test_rd_A_b_wr_A_impl():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( SomeMsg )

      @update
      def up_wr_A():
        s.A @= SomeMsg( 12, 123 )

      @update
      def up_rd_A_b():
        assert s.A.a == 12 and s.A.b == 123

  _test_model( Top )

# WR A.b - WR A
def test_wr_A_b_wr_A_conflict():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( SomeMsg )

      @update
      def up_wr_A_b():
        s.A.b @= Bits32( 123 )

      @update
      def up_wr_A():
        s.A @= SomeMsg( 12, 123 )

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")

# WR A.b - RD A
def test_wr_A_b_rd_A_impl():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( SomeMsg )

      @update
      def up_wr_A_b():
        s.A.b @= 123

      @update
      def up_rd_A():
        z = s.A

  _test_model( Top )

# WR A.b - RD A, RD A.b
def test_wr_A_b_rd_A_rd_A_b_can_schedule():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( SomeMsg )

      @update
      def up_wr_A_b():
        s.A.b @= Bits32( 123 )

      @update
      def up_rd_A():
        z = s.A

      @update
      def up_rd_A_b():
        assert s.A.b == 123

  _test_model( Top )

# WR A - RD A.a, RD A.b
def test_wr_A_rd_fields_can_schedule():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( SomeMsg )

      @update
      def up_wr_A():
        s.A @= SomeMsg( 12, 123 )

      @update
      def up_rd_A_a():
        assert s.A.a == 12

      @update
      def up_rd_A_b():
        assert s.A.b == 123

  _test_model( Top )

# WR A.b - RD A, RD A.a
def test_wr_A_b_rd_A_rd_A_a_cannot_schedule():

  class Top( ComponentLevel3 ):
    def construct( s ):
      s.A  = Wire( SomeMsg )

      @update
      def up_wr_A_b():
        s.A.b @= Bits32( 123 )

      @update
      def up_rd_A():
        z = s.A

      @update
      def up_rd_A_a():
        assert s.A.a == 12

  m = Top()
  m.elaborate()
  simple_sim_pass( m, 0x123 )

  # assert len(m._all_constraints) == 1
  # x, y = list(m._all_constraints)[0]

  # assert  m._all_id_upblk[x].__name__ == "up_wr_A_b" and \
          # m._all_id_upblk[y].__name__ == "up_rd_A" # only one constraint

# RD A.b - WR x, x|=A
def test_connect_rd_A_b_wr_x_conn_A_impl():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( SomeMsg )
      s.A  = Wire( SomeMsg )

      connect( s.x, s.A )

      @update
      def up_wr_x():
        s.x @= SomeMsg( 12, 123 )

      @update
      def up_rd_A_b():
        assert s.A.b == 123

  _test_model( Top )

# WR A.b - A|=x
def test_connect_wr_A_b_rd_x_conn_A_mark_writer():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( SomeMsg )
      s.A  = Wire( SomeMsg )

      connect( s.x, s.A )

      @update
      def up_wr_A_b():
        s.A.b @= Bits32( 123 )

  _test_model( Top )

# FIXME
# WR A.b - A|=x, WR x.b
# def test_connect_wr_A_b_wr_x_b_conn_A_conflict():

  # class Top( ComponentLevel3 ):
    # def construct( s ):

      # s.x  = Wire( SomeMsg )
      # s.A  = Wire( SomeMsg )

      # s.x |= s.A

      # @update
      # def up_wr_A_b():
        # s.A.b = Bits32( 123 )

      # @update
      # def up_wr_x_b():
        # s.x.a = 12

  # _test_model( Top )

# WR A.b - A|=x, WR x
def test_connect_wr_A_b_wr_x_conn_A_conflict():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( SomeMsg )
      s.A  = Wire( SomeMsg )

      connect( s.x, s.A )

      @update
      def up_wr_A_b():
        s.A.b @= Bits32( 123 )

      @update
      def up_wr_x():
        s.x @= SomeMsg( 12, 123 )

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")

# A.b|=x, WR x - RD A
def test_connect_wr_x_conn_A_b_rd_A_impl():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( SomeMsg )

      connect( s.A.b, s.x )

      @update
      def up_wr_x():
        s.x @= Bits32( 123 )

      @update
      def up_rd_A():
        z = s.A

  _test_model( Top )

# A.b|=x, WR x - WR A
def test_connect_wr_x_conn_A_b_wr_A_conflict():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( SomeMsg )

      connect( s.A.b, s.x )

      @update
      def up_wr_x():
        s.x @= Bits32( 123 )

      @update
      def up_wr_A():
        s.A @= SomeMsg( 12, 123 )

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")

# A.b|=x, RD x - WR A
def test_connect_rd_x_conn_A_b_wr_A_mark_writer():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( SomeMsg )

      connect( s.A.b, s.x )

      @update
      def up_wr_A():
        s.A @= SomeMsg( 12, 123 )

      @update
      def up_rd_x():
        z = s.x

  _test_model( Top )

# A.b|=x, WR x - A|=y, WR y
def test_connect_wr_x_conn_A_b_wr_y_conn_A_conflict():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( SomeMsg )
      s.y  = Wire( SomeMsg )

      connect( s.A.b, s.x )
      connect( s.A,   s.y )

      @update
      def up_wr_x():
        s.x @= Bits32( 123 )

      @update
      def up_wr_y():
        s.y @= SomeMsg( 12, 123 )

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown MultiWriterError.")

# A.b|=x, WR x - A|=y, RD y
def test_connect_wr_x_conn_A_b_rd_y_conn_A_mark_writer():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( SomeMsg )
      s.y  = Wire( SomeMsg )

      connect( s.A.b, s.x )
      connect( s.A,   s.y )

      @update
      def up_wr_x():
        s.x @= Bits32( 123 )

      @update
      def up_rd_y():
        assert s.y == SomeMsg( 0, 123 )

  _test_model( Top )

# A.b|=x, RD x - A|=y, WR y
def test_connect_rd_x_conn_A_b_wr_y_conn_A_mark_writer():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( SomeMsg )
      s.y  = Wire( SomeMsg )

      connect( s.A.b, s.x )
      connect( s.A,   s.y )

      @update
      def up_rd_x():
        z = s.x

      @update
      def up_wr_y():
        s.y @= SomeMsg( 12, 123 )

  _test_model( Top )

def test_iterative_find_nets():

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.w  = Wire( SomeMsg )
      s.x  = Wire( SomeMsg )
      s.y  = Wire( SomeMsg )
      s.z  = Wire( SomeMsg )

      connect( s.w, s.x ) # net1
      connect( s.x.a, s.y.a ) # net2
      connect( s.y, s.z ) # net3

      @update
      def up_wr_s_w():
        s.w @= SomeMsg( 12, 123 )

  _test_model( Top )

def test_deep_connections():

  @bitstruct
  class Msg1:
    a: Bits16
    b: Bits32

  @bitstruct
  class Msg2:
    p: Msg1
    q: Msg1

  @bitstruct
  class Msg3:
    x: Msg1
    y: Msg2
    z: Bits16

  class Top( ComponentLevel3 ):
    def construct( s ):

      s.A  = Wire( Msg3 )
      s.x  = Wire( Msg1 )
      s.y  = Wire( Msg2 )
      s.z  = Wire( Msg3 )

      s.w  = Wire( 16 )

      connect( s.A.y.p, s.x )
      connect( s.A.z,   s.w )
      connect( s.A,     s.z )

      @update
      def up_z():
        yy = s.z

      @update
      def up_rd_x():
        zz = s.x

      @update
      def up_wr_y():
        s.w @= Msg2( 12, 123 )

  try:
    _test_model( Top )
  except NoWriterError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown NoWriterError.")

def test_struct_with_list_of_bits():

  @bitstruct
  class B:
    foo: [ Bits32 ] * 5

  class A( ComponentLevel3 ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits32 )
      # PyMTL mistakenly takes s.in_.foo[1] as a single bit!
      connect( s.out, s.in_.foo[1] )

  a = A()
  a.elaborate()

def test_nested_struct_2d_array_index():

  @bitstruct
  class C:
    bar: Bits16

  @bitstruct
  class B:
    foo: Bits32
    bar: [ [C]*5 ] * 5

  class A( ComponentLevel3 ):
    def construct( s ):
      s.struct = InPort( B )
      s.out    = OutPort( C )
      s.out2   = OutPort( Bits16 )
      connect( s.struct.bar[1][4], s.out )
      connect( s.struct.bar[1][4].bar, s.out2 )

      s.wire = Wire( B )
      @update_ff
      def ffs():
        s.wire.bar <<= 1

  a = A()
  try:
    a.elaborate()
  except UpdateFFNonTopLevelSignalError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown UpdateFFNonTopLevelSignalError.")

# TODO better error message?
def test_ff_cannot_write_to_struct_field():

  @bitstruct
  class C:
    bar: Bits16

  @bitstruct
  class B:
    foo: Bits32
    bar: [ [C]*5 ] * 5

  class A( ComponentLevel3 ):
    def construct( s ):
      s.wire = Wire( B )
      @update_ff
      def ffs():
        s.wire.bar <<= 1

  try:
    _test_model( A )
  except UpdateFFNonTopLevelSignalError as e:
    print("{} is thrown\n{}".format( e.__class__.__name__, e ))
    return
  raise Exception("Should've thrown UpdateFFNonTopLevelSignalError.")
