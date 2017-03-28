from pymtl import *

from pclib.bundle import TestSource
from pclib.bundle import TestSink
from pclib.bundle import ValRdyBundle

class SomeMsg( object ):

  def __init__( s, a=0, b=0 ):
    s.a = a
    s.b = Bits( 32, b )

def _test_model( model ):
  m = model()
  m.elaborate()
  m.print_schedule()

  for x in xrange(10):
    m.cycle()

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

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( SomeMsg )

      @s.update
      def up_wr_A():
        s.A = SomeMsg( 12, 123 )

      @s.update
      def up_rd_A_b():
        assert s.A.a == 12 and s.A.b == 123

  _test_model( Top )

# WR A.b - WR A
def test_wr_A_b_wr_A_conflict():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( SomeMsg )

      @s.update
      def up_wr_A_b():
        s.A.b = Bits( 32, 123 )

      @s.update
      def up_wr_A():
        s.A = SomeMsg( 12, 123 )

  try:
    _test_model( Top )
  except Exception:
    return
  raise Exception("Should've thrown two writer conflict exception.")

# WR A.b - RD A
def test_wr_A_b_rd_A_impl():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( SomeMsg )

      @s.update
      def up_wr_A_b():
        s.A.b = 123

      @s.update
      def up_rd_A():
        z = s.A

  _test_model( Top )

# WR A.b - RD A, RD A.b
def test_wr_A_b_rd_A_rd_A_b_can_schedule():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( SomeMsg )

      @s.update
      def up_wr_A_b():
        s.A.b = Bits( 32, 123 )

      @s.update
      def up_rd_A():
        z = s.A

      @s.update
      def up_rd_A_b():
        assert s.A.b == 123

  _test_model( Top )

# WR A - RD A.a, RD A.b
def test_wr_A_rd_fields_can_schedule():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( SomeMsg )

      @s.update
      def up_wr_A():
        s.A = SomeMsg( 12, 123 )

      @s.update
      def up_rd_A_a():
        assert s.A.a == 12

      @s.update
      def up_rd_A_b():
        assert s.A.b == 123

  _test_model( Top )

# WR A.b - RD A, RD A.a
def test_wr_A_b_rd_A_rd_A_a_cannot_schedule():

  class Top(Updates):
    def __init__( s ):
      s.A  = Wire( SomeMsg )

      @s.update
      def up_wr_A_b():
        s.A.b = Bits( 32, 123 )

      @s.update
      def up_rd_A():
        z = s.A

      @s.update
      def up_rd_A_a():
        assert s.A.a == 12

  try:
    _test_model( Top )
  except Exception:
    return
  raise Exception("Should've thrown no constraint exception.")

# RD A.b - WR x, x|=A
def test_connect_rd_A_b_wr_x_conn_A_impl():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( SomeMsg )
      s.A  = Wire( SomeMsg )

      s.x |= s.A

      @s.update
      def up_wr_x():
        s.x = SomeMsg( 12, 123 )

      @s.update
      def up_rd_A_b():
        assert s.A.b == 123

  _test_model( Top )

# WR A.b - A|=x
def test_connect_wr_A_b_rd_x_conn_A_mark_writer():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( SomeMsg )
      s.A  = Wire( SomeMsg )

      s.x |= s.A

      @s.update
      def up_wr_A_b():
        s.A.b = Bits( 32, 123 )

  _test_model( Top )

# FIXME
# WR A.b - A|=x, WR x.b
# def test_connect_wr_A_b_wr_x_b_conn_A_conflict():

  # class Top(Updates):
    # def __init__( s ):

      # s.x  = Wire( SomeMsg )
      # s.A  = Wire( SomeMsg )

      # s.x |= s.A

      # @s.update
      # def up_wr_A_b():
        # s.A.b = Bits( 32, 123 )

      # @s.update
      # def up_wr_x_b():
        # s.x.a = 12

  # _test_model( Top )

# WR A.b - A|=x, WR x 
def test_connect_wr_A_b_wr_x_conn_A_conflict():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( SomeMsg )
      s.A  = Wire( SomeMsg )

      s.x |= s.A

      @s.update
      def up_wr_A_b():
        s.A.b = Bits( 32, 123 )

      @s.update
      def up_wr_x():
        s.x = SomeMsg( 12, 123 )

  try:
    _test_model( Top )
  except Exception:
    return
  raise Exception("Should've thrown two writer conflict exception.")

# A.b|=x, WR x - RD A
def test_connect_wr_x_conn_A_b_rd_A_impl():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits )
      s.A  = Wire( SomeMsg )

      s.A.b |= s.x

      @s.update
      def up_wr_x():
        s.x = Bits( 32, 123 )

      @s.update
      def up_rd_A():
        z = s.A

  _test_model( Top )

# A.b|=x, WR x - WR A
def test_connect_wr_x_conn_A_b_wr_A_conflict():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits )
      s.A  = Wire( SomeMsg )

      s.A.b |= s.x

      @s.update
      def up_wr_x():
        s.x = Bits( 32, 123 )

      @s.update
      def up_wr_A():
        s.A = SomeMsg( 12, 123 )

  try:
    _test_model( Top )
  except Exception:
    return
  raise Exception("Should've thrown two writer conflict exception.")

# A.b|=x, RD x - WR A
def test_connect_rd_x_conn_A_b_wr_A_mark_writer():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits )
      s.A  = Wire( SomeMsg )

      s.A.b |= s.x

      @s.update
      def up_wr_A():
        s.A = SomeMsg( 12, 123 )

      @s.update
      def up_rd_x():
        z = s.x

  _test_model( Top )

# A.b|=x, WR x - A|=y, WR y
def test_connect_wr_x_conn_A_b_wr_y_conn_A_conflict():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits )
      s.A  = Wire( SomeMsg )
      s.y  = Wire( SomeMsg )

      s.A.b |= s.x
      s.A   |= s.y

      @s.update
      def up_wr_x():
        s.x = Bits( 32, 123 )

      @s.update
      def up_wr_y():
        s.y = SomeMsg( 12, 123 )

  try:
    _test_model( Top )
  except Exception:
    return
  raise Exception("Should've thrown two writer conflict exception.")

# A.b|=x, WR x - A|=y, RD y
def test_connect_wr_x_conn_A_b_rd_y_conn_A_mark_writer():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits )
      s.A  = Wire( SomeMsg )
      s.y  = Wire( SomeMsg )

      s.A.b |= s.x
      s.A   |= s.y

      @s.update
      def up_wr_x():
        s.x = Bits( 32, 123 )

      @s.update
      def up_rd_y():
        z = s.y

  _test_model( Top )

# A.b|=x, RD x - A|=y, WR y
def test_connect_rd_x_conn_A_b_wr_y_conn_A_mark_writer():

  class Top(Updates):
    def __init__( s ):

      s.x  = Wire( Bits )
      s.A  = Wire( SomeMsg )
      s.y  = Wire( SomeMsg )

      s.A.b |= s.x
      s.A   |= s.y

      @s.update
      def up_rd_x():
        z = s.x

      @s.update
      def up_wr_y():
        s.y = SomeMsg( 12, 123 )

  _test_model( Top )

def test_iterative_find_nets():

  class Top(Updates):
    def __init__( s ):

      s.w  = Wire( SomeMsg )
      s.x  = Wire( SomeMsg )
      s.y  = Wire( SomeMsg )
      s.z  = Wire( SomeMsg )

      s.w |= s.x # net1

      s.x.a |= s.y.a # net2

      s.y |= s.z # net3

      @s.update
      def up_wr_s_w():
        s.w = SomeMsg( 12, 123 )

  _test_model( Top )

def test_deep_connections():

  class Msg1( object ):
    def __init__( s, a=0, b=0 ):
      s.a = a
      s.b = Bits( 32, b )

  class Msg2( object ):
    def __init__( s, a=Msg1(), b=Msg1() ):
      s.p = a
      s.q = b

  class Msg3( object ):
    def __init__( s, x=Msg1(), y=Msg2(), z=0 ):
      s.x = x
      s.y = y
      s.z = z

  class Top(Updates):
    def __init__( s ):

      s.A  = Wire( Msg3 )
      s.x  = Wire( Msg1 )
      s.y  = Wire( Msg2 )
      s.z  = Wire( Msg3 )

      s.w  = Wire(int)

      s.A.y.p |= s.x
      s.A.z   |= s.w
      s.A     |= s.z

      @s.update
      def up_z():
        yy = s.z

      @s.update
      def up_rd_x():
        zz = s.x

      @s.update
      def up_wr_y():
        s.w = Msg2( 12, 123 )

  try:
    _test_model( Top )
  except Exception:
    return
  raise Exception("Should've thrown no driver exception.")
