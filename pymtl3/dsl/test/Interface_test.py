"""
========================================================================
Interface_test.py
========================================================================

Author : Shunning Jiang, Yanghui Ou
Date   : Jan 1, 2018
"""
from __future__ import absolute_import, division, print_function

from collections import deque
from functools import reduce

from pymtl3.datatypes import *
from pymtl3.dsl import *

from .sim_utils import simple_sim_pass


def _test_model( cls ):
  A = cls()
  A.elaborate()
  simple_sim_pass( A, 0x123 )

  print()
  T, time = 0, 20
  while not A.done() and T < time:
    A.tick()
    print(A.line_trace())
    T += 1

def valrdy_to_str( msg, val, rdy ):

  str_   = "{}".format( msg )
  nchars = max( len( str_ ), 15 )

  if       val and not rdy:
    str_ = "#".ljust( nchars )
  elif not val and     rdy:
    str_ = " ".ljust( nchars )
  elif not val and not rdy:
    str_ = ".".ljust( nchars )

  return str_.ljust( nchars )

class InValRdyIfc( Interface ):

  def construct( s, Type ):

    s.msg = InPort( Type )
    s.val = InPort( int if Type is int else Bits1 )
    s.rdy = OutPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy )

class OutValRdyIfc( Interface ):

  def construct( s, Type ):

    s.msg = OutPort( Type )
    s.val = OutPort( int if Type is int else Bits1 )
    s.rdy = InPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return valrdy_to_str( s.msg, s.val, s.rdy )

class TestSourceValRdy( ComponentLevel3 ):

  def construct( s, Type, msgs ):
    assert type(msgs) == list, "TestSrc only accepts a list of inputs!"

    s.msgs    = msgs
    s.src_msgs = deque( msgs )
    s.default = Type()
    s.out     = OutValRdyIfc( Type )

    @s.update_on_edge
    def up_src():
      if (s.out.rdy & s.out.val) and s.src_msgs:
        s.src_msgs.popleft()
      s.out.val = Bits1( len(s.src_msgs) > 0 )
      s.out.msg = s.default if not s.src_msgs else s.src_msgs[0]

  def done( s ):
    return not s.src_msgs

  def line_trace( s ):
    return s.out.line_trace()

class TestSinkValRdy( ComponentLevel3 ):

  def construct( s, Type, msgs ):
    assert type(msgs) == list, "TestSink only accepts a list of outputs!"

    s.msgs = msgs
    s.sink_msgs = deque( s.msgs )

    s.in_ = InValRdyIfc( Type )

    @s.update_on_edge
    def up_sink():
      s.in_.rdy = Bits1( len(s.sink_msgs) > 0 )

      if s.in_.val and s.in_.rdy:
        ref = s.sink_msgs.popleft()
        ans = s.in_.msg

        assert ref == ans, "Expect %s, get %s instead" % (ref, ans)

  def done( s ):
    return not s.sink_msgs

  def line_trace( s ):
    return s.in_.line_trace()

def test_simple():

  class Top( ComponentLevel3 ):

    def construct( s ):

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

    def construct( s, Type=int ):
      s.msg = Wire( Type )
      s.val = Wire( Bits1 )
      s.rdy = Wire( Bits1 )

    def line_trace( s ):
      return valrdy_to_str( s.msg, s.val, s.rdy )

  class SuperBundle( Interface ):

    def construct( s ):
      s.req  = [ [ ValRdyBundle() for i in xrange(4) ] for j in xrange(4) ]

  class Top( ComponentLevel3 ):

    def construct( s ):

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

def test_customized_connect():

  class MockRecvIfc( Interface ):
    def construct( s ):
      s.recv_msg = InPort( Bits1 )
      s.recv_val = InPort( Bits1 )

    def connect( s, other, parent ):
      if isinstance( other, MockSendIfc ):
        parent.connect_pairs(
          s.recv_msg, other.send_msg,
          s.recv_val, other.send_val,
        )
        return True

      return False

  class MockSendIfc( Interface ):
    def construct( s ):
      s.send_msg = OutPort( Bits1 )
      s.send_val = OutPort( Bits1 )

    def connect( s, other, parent ):
      if isinstance( other, MockRecvIfc ):
        parent.connect_pairs(
          s.send_msg, other.recv_msg,
          s.send_val, other.recv_val,
        )
        return True

      return False

  class A( ComponentLevel3 ):
    def construct( s ):
      s.send = MockSendIfc()

      @s.update
      def up_send():
        s.send.send_msg = Bits1( 1 )
        s.send.send_val = Bits1( 1 )

  class B( ComponentLevel3 ):
    def construct( s ):
      s.recv = MockRecvIfc()

      @s.update
      def up_recv():
        print("recv_msg", s.recv.recv_msg, "recv_val", s.recv.recv_val)

  class Top( ComponentLevel3 ):

    def construct( s ):
      s.a = A()
      s.b = B()
      s.connect( s.a.send, s.b.recv )

    def done( s ):
      return False

    def line_trace( s ):
      return ""

  _test_model( Top )

#-------------------------------------------------------------------------
# Test customized connect with adapters
#-------------------------------------------------------------------------

def test_customized_connect_adapter():

  class MockAdapter( ComponentLevel3 ):

    count = 0

    def construct( s, InType, OutType ):

      s.in_ = InPort ( InType  )
      s.out = OutPort( OutType )

      @s.update
      def adapter_incr():
        s.out = s.in_ + OutType( 1 )

  class MockRecvIfc( Interface ):

    def construct( s, Type ):
      s.recv_msg = InPort( Type  )
      s.recv_val = InPort( Bits1 )

      s.Type = Type

    def connect( s, other, parent ):
      if isinstance( other, MockSendIfc ):

        MockAdapter.count += 1
        m = MockAdapter( other.Type, s.Type )
        setattr( parent, "mock_adapter_" + str( MockAdapter.count ), m )

        parent.connect_pairs(
          other.send_msg, m.in_,
          m.out,          s.recv_msg,
          other.send_val, s.recv_val
        )
        return True

      return False

  class MockSendIfc( Interface ):
    def construct( s, Type ):
      s.send_msg = OutPort( Type  )
      s.send_val = OutPort( Bits1 )

      s.Type = Type

    def connect( s, other, parent ):
      if isinstance( other, MockRecvIfc ):
        parent.connect_pairs(
          s.send_msg, other.recv_msg,
          s.send_val, other.recv_val,
        )
        return True

      return False

  class A( ComponentLevel3 ):
    def construct( s ):
      s.send = [ MockSendIfc( Bits8 ) for _ in range( 10 ) ]

      @s.update
      def up_send():
        for i in range( 10 ):
          s.send[i].send_msg = Bits1( 1 )
          s.send[i].send_val = Bits1( 1 )

  class B( ComponentLevel3 ):
    def construct( s ):
      s.recv = [ MockRecvIfc( Bits128 ) for _ in range( 10 ) ]

      @s.update
      def up_recv():
        for i in range( 10 ):
          print("recv_msg", i, s.recv[i].recv_msg, "recv_val", s.recv[i].recv_val)

  class Top( ComponentLevel3 ):

    def construct( s ):
      s.a = A()
      s.b = B()
      for i in range( 10 ):
        s.connect( s.b.recv[i], s.a.send[i] )

    def done( s ):
      return False

    def line_trace( s ):
      return ""

  _test_model( Top )
