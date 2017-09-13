from pymtl import *
from pymtl.model import ComponentLevel3
from pclib.rtl import TestSourceValRdy, TestSinkValRdy
from sim_utils import simple_sim_pass

def _test_model( cls ):
  A = cls()
  A.elaborate()
  simple_sim_pass( A, 0x123 )

  T, time = 0, 20
  while not A.done() and T < time:
    A.tick()
    print A.line_trace()
    T += 1

def test_simple():

  class Top( ComponentLevel3 ):

    def __init__( s ):

      s.src  = TestSourceValRdy( int, [ 0, 1, 2 ] )
      s.sink = TestSinkValRdy  ( int, [ 0, 1, 2 ] )( in_ = s.src.out )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return s.src.line_trace() + " >>> " + \
             " >>> " + s.sink.line_trace()

  _test_model( Top )

def test_nested_port_bundle():

  class ValRdyBundle( Interface ):

    def __init__( s, Type=int ):
      s.Type = Type

      s.msg = Wire( Type )
      s.val = Wire( Bits1 )
      s.rdy = Wire( Bits1 )

    def line_trace( s ):
      return valrdy_to_str( s.msg, s.val, s.rdy )

  class SuperBundle( Interface ):

    def __init__( s ):
      s.req  = [ [ ValRdyBundle() for i in xrange(4) ] for j in xrange(4) ]

  class Top( ComponentLevel3 ):

    def __init__( s ):

      s.src  = [ TestSourceValRdy( int, [ i,i+1,i+2,i,i+1,i+2 ] ) for i in xrange(4) ]
      # (0+1+2+3)*4=24, (1+2+3+4)*4=40, (2+3+4+5)*5=56
      s.sink = TestSinkValRdy  ( int, [ 24, 40, 56, 24, 40, 56] )

      s.sb = SuperBundle()
      s.wire = [ [ Wire(int) for i in xrange(4) ] for j in xrange(4) ]

      for i in xrange(4):
        s.connect( s.src[i].out.rdy, s.sink.in_.rdy )
        for j in xrange(4):
          s.connect( s.sb.req[i][j].msg, s.src[i].out.msg )
          s.connect( s.wire[i][j],       s.sb.req[i][j].msg )

      @s.update
      def up_from_req():
        s.sink.in_.val = 1
        s.sink.in_.msg = 0
        for i in xrange(4):
          for j in xrange(4):
            s.sink.in_.msg += s.wire[i][j]

    def done( s ):
      return reduce( lambda x,y: x or y.done(), s.src ) and s.sink.done()

    def line_trace( s ):
      return "|".join( [ x.line_trace() for x in s.src] ) + " >>> " + \
             " >>> " + s.sink.line_trace()

  _test_model( Top )
