from pymtl import *
from pymtl.model import ComponentLevel3
from pymtl.model.errors import MultiWriterError, NoWriterError
from sim_utils import simple_sim_pass

class SomeMsg( object ):

  def __init__( s ):
    s.a = int
    s.b = Bits32

  def __call__( s, a = 0, b = Bits1() ):
    x = s.__class__()
    x.a = x.a(a)
    x.b = x.b(b)
    return x

  def __eq__( s, other ):
    return s.a == other.a and s.b == other.b

def _test_model( cls ):
  A = cls()
  A.elaborate()
  simple_sim_pass( A, 0x123 )

  for i in xrange(10):
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
    def __init__( s ):
      s.A  = Wire( SomeMsg() )

      @s.update
      def up_wr_A():
        s.A = SomeMsg()( 12, 123 )

      @s.update
      def up_rd_A_b():
        assert s.A.a == 12 and s.A.b == 123

  _test_model( Top )

# WR A.b - WR A
def test_wr_A_b_wr_A_conflict():

  class Top( ComponentLevel3 ):
    def __init__( s ):
      s.A  = Wire( SomeMsg() )

      @s.update
      def up_wr_A_b():
        s.A.b = Bits32( 123 )

      @s.update
      def up_wr_A():
        s.A = SomeMsg()( 12, 123 )

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print "{} is thrown\n{}".format( e.__class__.__name__, e )
    return
  raise Exception("Should've thrown MultiWriterError.")

# WR A.b - RD A
def test_wr_A_b_rd_A_impl():

  class Top( ComponentLevel3 ):
    def __init__( s ):
      s.A  = Wire( SomeMsg() )

      @s.update
      def up_wr_A_b():
        s.A.b = 123

      @s.update
      def up_rd_A():
        z = s.A

  _test_model( Top )

# WR A.b - RD A, RD A.b
def test_wr_A_b_rd_A_rd_A_b_can_schedule():

  class Top( ComponentLevel3 ):
    def __init__( s ):
      s.A  = Wire( SomeMsg() )

      @s.update
      def up_wr_A_b():
        s.A.b = Bits32( 123 )

      @s.update
      def up_rd_A():
        z = s.A

      @s.update
      def up_rd_A_b():
        assert s.A.b == 123

  _test_model( Top )

# WR A - RD A.a, RD A.b
def test_wr_A_rd_fields_can_schedule():

  class Top( ComponentLevel3 ):
    def __init__( s ):
      s.A  = Wire( SomeMsg() )

      @s.update
      def up_wr_A():
        s.A = SomeMsg()( 12, 123 )

      @s.update
      def up_rd_A_a():
        assert s.A.a == 12

      @s.update
      def up_rd_A_b():
        assert s.A.b == 123

  _test_model( Top )

# WR A.b - RD A, RD A.a
def test_wr_A_b_rd_A_rd_A_a_cannot_schedule():

  class Top( ComponentLevel3 ):
    def __init__( s ):
      s.A  = Wire( SomeMsg() )

      @s.update
      def up_wr_A_b():
        s.A.b = Bits32( 123 )

      @s.update
      def up_rd_A():
        z = s.A

      @s.update
      def up_rd_A_a():
        assert s.A.a == 12

  m = Top()
  m.elaborate()
  simple_sim_pass( m, 0x123 )

  assert len(m._all_constraints) == 1
  x, y = list(m._all_constraints)[0]

  assert  m._all_id_upblk[x].__name__ == "up_wr_A_b" and \
          m._all_id_upblk[y].__name__ == "up_rd_A" # only one constraint

# RD A.b - WR x, x|=A
def test_connect_rd_A_b_wr_x_conn_A_impl():

  class Top( ComponentLevel3 ):
    def __init__( s ):

      s.x  = Wire( SomeMsg() )
      s.A  = Wire( SomeMsg() )

      s.connect( s.x, s.A )

      @s.update
      def up_wr_x():
        s.x = SomeMsg()( 12, 123 )

      @s.update
      def up_rd_A_b():
        assert s.A.b == 123

  _test_model( Top )

# WR A.b - A|=x
def test_connect_wr_A_b_rd_x_conn_A_mark_writer():

  class Top( ComponentLevel3 ):
    def __init__( s ):

      s.x  = Wire( SomeMsg() )
      s.A  = Wire( SomeMsg() )

      s.connect( s.x, s.A )

      @s.update
      def up_wr_A_b():
        s.A.b = Bits32( 123 )

  _test_model( Top )

# FIXME
# WR A.b - A|=x, WR x.b
# def test_connect_wr_A_b_wr_x_b_conn_A_conflict():

  # class Top( ComponentLevel3 ):
    # def __init__( s ):

      # s.x  = Wire( SomeMsg() )
      # s.A  = Wire( SomeMsg() )

      # s.x |= s.A

      # @s.update
      # def up_wr_A_b():
        # s.A.b = Bits32( 123 )

      # @s.update
      # def up_wr_x_b():
        # s.x.a = 12

  # _test_model( Top )

# WR A.b - A|=x, WR x 
def test_connect_wr_A_b_wr_x_conn_A_conflict():

  class Top( ComponentLevel3 ):
    def __init__( s ):

      s.x  = Wire( SomeMsg() )
      s.A  = Wire( SomeMsg() )

      s.connect( s.x, s.A )

      @s.update
      def up_wr_A_b():
        s.A.b = Bits32( 123 )

      @s.update
      def up_wr_x():
        s.x = SomeMsg()( 12, 123 )

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print "{} is thrown\n{}".format( e.__class__.__name__, e )
    return
  raise Exception("Should've thrown MultiWriterError.")

# A.b|=x, WR x - RD A
def test_connect_wr_x_conn_A_b_rd_A_impl():

  class Top( ComponentLevel3 ):
    def __init__( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( SomeMsg() )

      s.connect( s.A.b, s.x )

      @s.update
      def up_wr_x():
        s.x = Bits32( 123 )

      @s.update
      def up_rd_A():
        z = s.A

  _test_model( Top )

# A.b|=x, WR x - WR A
def test_connect_wr_x_conn_A_b_wr_A_conflict():

  class Top( ComponentLevel3 ):
    def __init__( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( SomeMsg() )

      s.connect( s.A.b, s.x )

      @s.update
      def up_wr_x():
        s.x = Bits32( 123 )

      @s.update
      def up_wr_A():
        s.A = SomeMsg()( 12, 123 )

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print "{} is thrown\n{}".format( e.__class__.__name__, e )
    return
  raise Exception("Should've thrown MultiWriterError.")

# A.b|=x, RD x - WR A
def test_connect_rd_x_conn_A_b_wr_A_mark_writer():

  class Top( ComponentLevel3 ):
    def __init__( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( SomeMsg() )

      s.connect( s.A.b, s.x )

      @s.update
      def up_wr_A():
        s.A = SomeMsg()( 12, 123 )

      @s.update
      def up_rd_x():
        z = s.x

  _test_model( Top )

# A.b|=x, WR x - A|=y, WR y
def test_connect_wr_x_conn_A_b_wr_y_conn_A_conflict():

  class Top( ComponentLevel3 ):
    def __init__( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( SomeMsg() )
      s.y  = Wire( SomeMsg() )

      s.connect( s.A.b, s.x )
      s.connect( s.A,   s.y )

      @s.update
      def up_wr_x():
        s.x = Bits32( 123 )

      @s.update
      def up_wr_y():
        s.y = SomeMsg()( 12, 123 )

  try:
    _test_model( Top )
  except MultiWriterError as e:
    print "{} is thrown\n{}".format( e.__class__.__name__, e )
    return
  raise Exception("Should've thrown MultiWriterError.")

# A.b|=x, WR x - A|=y, RD y
def test_connect_wr_x_conn_A_b_rd_y_conn_A_mark_writer():

  class Top( ComponentLevel3 ):
    def __init__( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( SomeMsg() )
      s.y  = Wire( SomeMsg() )

      s.connect( s.A.b, s.x )
      s.connect( s.A,   s.y )

      @s.update
      def up_wr_x():
        s.x = Bits32( 123 )

      @s.update
      def up_rd_y():
        z = s.y

  _test_model( Top )

# A.b|=x, RD x - A|=y, WR y
def test_connect_rd_x_conn_A_b_wr_y_conn_A_mark_writer():

  class Top( ComponentLevel3 ):
    def __init__( s ):

      s.x  = Wire( Bits32 )
      s.A  = Wire( SomeMsg() )
      s.y  = Wire( SomeMsg() )

      s.connect( s.A.b, s.x )
      s.connect( s.A,   s.y )

      @s.update
      def up_rd_x():
        z = s.x

      @s.update
      def up_wr_y():
        s.y = SomeMsg()( 12, 123 )

  _test_model( Top )

def test_iterative_find_nets():

  class Top( ComponentLevel3 ):
    def __init__( s ):

      s.w  = Wire( SomeMsg() )
      s.x  = Wire( SomeMsg() )
      s.y  = Wire( SomeMsg() )
      s.z  = Wire( SomeMsg() )

      s.connect( s.w, s.x ) # net1
      s.connect( s.x.a, s.y.a ) # net2
      s.connect( s.y, s.z ) # net3

      @s.update
      def up_wr_s_w():
        s.w = SomeMsg()( 12, 123 )

  _test_model( Top )

def test_deep_connections():

  class Msg1( object ):
    def __init__( s ):
      s.a = int
      s.b = Bits32

    def __call__( s, a = 0, b = Bits32(0) ):
      x = s.__class__()
      x.a = x.a(a)
      x.b = x.b(b)
      return x

  msg1 = Msg1()

  class Msg2( object ):
    def __init__( s ):
      s.p = msg1
      s.q = msg1

    def __call__( s, p = msg1(), q = msg1() ):
      x = s.__class__()
      x.p = p
      x.q = q
      return x

  msg2 = Msg2()

  class Msg3( object ):
    def __init__( s ):
      s.x = msg1
      s.y = msg2
      s.z = int

    def __call__( s, x = Msg1()(), y = Msg2()(), z=0 ):
      x = s.__class__()
      x.x = x
      x.y = y
      x.z = x.z(z)
      return x

  class Top( ComponentLevel3 ):
    def __init__( s ):

      msg3 = Msg3() # TODO find a good way to handle type equivalence

      s.A  = Wire( msg3 )
      s.x  = Wire( msg1 )
      s.y  = Wire( msg2 )
      s.z  = Wire( msg3 )

      s.w  = Wire(int)

      s.connect( s.A.y.p, s.x )
      s.connect( s.A.z,   s.w )
      s.connect( s.A,     s.z )

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
  except NoWriterError as e:
    print "{} is thrown\n{}".format( e.__class__.__name__, e )
    return
  raise Exception("Should've thrown NoWriterError.")
