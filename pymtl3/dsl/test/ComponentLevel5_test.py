"""
========================================================================
ComponentLevel5_test.py
========================================================================

Author : Shunning Jiang
Date   : Jan 4, 2019
"""
from collections import deque

from pymtl3.dsl.ComponentLevel1 import update
from pymtl3.dsl.ComponentLevel3 import connect
from pymtl3.dsl.ComponentLevel4 import update_once
from pymtl3.dsl.ComponentLevel5 import ComponentLevel5, method_port
from pymtl3.dsl.Connectable import CalleePort, CallerPort, Interface
from pymtl3.dsl.ConstraintTypes import M, U

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
  return T

class SimpleTestSource( ComponentLevel5 ):

  def construct( s, msgs ):
    s.msgs = deque( msgs )

    s.req     = CallerPort()
    s.req_rdy = CallerPort()

    s.v = 0
    @update_once
    def up_src():
      s.v = None
      if s.req_rdy() and s.msgs:
        s.v = s.msgs.popleft()
        s.req( s.v )

  def done( s ):
    return not s.msgs

  def line_trace( s ):
    return "{:4}".format( "" if s.v is None else s.v )

class TestSinkError( Exception ):
  pass

class SimpleTestSink( ComponentLevel5 ):

  def resp_( s, msg ):
    ref = s.msgs[ s.idx ]
    s.idx += 1

    if msg != ref:
      raise TestSinkError( """
The test sink received an incorrect message!
- sink name    : {}
- msg number   : {}
- expected msg : {}
- actual msg   : {}
""".format( s, s.idx, ref, msg )
      )

  def resp_rdy_( s ):
    return True

  def construct( s, msgs ):
    s.msgs = list( msgs )
    s.idx  = 0

    s.resp     = CalleePort( method = s.resp_     )
    s.resp_rdy = CalleePort( method = s.resp_rdy_ )

  def done( s ):
    return s.idx >= len(s.msgs)

  def line_trace( s ):
    return ""

def test_simple_src_dumb_sink():

  class Top( ComponentLevel5 ):

    def construct( s ):
      s.src  = SimpleTestSource( [1,2,3,4] )
      s.sink = SimpleTestSink( [1,2,3,4] )

      s.src.req //= s.sink.resp
      connect( s.src.req_rdy, s.sink.resp_rdy )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return  s.src.line_trace() + " >>> " + s.sink.line_trace()


  assert _test_model( Top ) == 4 # regression: 4 cycles

class TestSinkUp( ComponentLevel5 ):

  def resp_rdy_( s ):
    return s.idx < len(s.msgs)

  def resp_( s, v ):
    s.queue.appendleft(v)

  def construct( s, msgs ):
    s.msgs  = list( msgs )
    s.queue = deque( maxlen=1 )
    s.idx  = 0

    s.resp     = CalleePort( method = s.resp_ )
    s.resp_rdy = CalleePort( method = s.resp_rdy_ )

    s.v = None

    @update_once
    def up_sink():
      s.v = None

      if s.queue:
        msg = s.queue.popleft()
        s.v = msg

        if s.idx >= len(s.msgs):
          raise TestSinkError( """
  The test sink received a message that !
  - sink name    : {}
  - msg number   : {}
  - actual msg   : {}
  """.format( s, s.idx, msg )
          )
        else:
          ref = s.msgs[ s.idx ]
          s.idx += 1

          if msg != ref:
            raise TestSinkError( """
  The test sink received an incorrect message!
  - sink name    : {}
  - msg number   : {}
  - expected msg : {}
  - actual msg   : {}
  """.format( s, s.idx, ref, msg )
          )

    s.add_constraints(
      U(up_sink) < M(s.resp_    ), # pipe behavior
      U(up_sink) < M(s.resp_rdy_),
    )

  def done( s ):
    return s.idx >= len(s.msgs)

  def line_trace( s ):
    return "{:4}".format( "" if s.v is None else s.v )

def test_simple_src_up_sink():

  class Top( ComponentLevel5 ):

    def construct( s ):
      s.src  = SimpleTestSource( [1,2,3,4] )
      s.sink = TestSinkUp( [1,2,3,4] )

      connect( s.src.req,     s.sink.resp )
      connect( s.src.req_rdy, s.sink.resp_rdy )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return  s.src.line_trace() + " >>> " + s.sink.line_trace()

  assert _test_model( Top ) == 5 # regression: 5 cycles

class PassThrough( ComponentLevel5 ):

  @method_port
  def req( s, msg ):
    assert s.resp_rdy()
    s.resp( msg )

  @method_port
  def req_rdy( s ):
    return s.resp_rdy()

  def construct( s ):
    s.resp     = CalleePort()
    s.resp_rdy = CalleePort()
    s.entry = None

    s.add_constraints(
      M(s.req) == M(s.resp),
      M(s.req_rdy) == M(s.resp_rdy),
    )

def test_constraint_equal_pass_through():

  class Top( ComponentLevel5 ):

    def construct( s ):
      s.src  = SimpleTestSource( [1,2,3,4] )
      s.mid  = PassThrough()
      s.sink = TestSinkUp( [1,2,3,4] )

      s.mid.req       //= s.src.req
      s.mid.req_rdy   //= s.src.req_rdy
      s.sink.resp     //= s.mid.resp
      s.sink.resp_rdy //= s.mid.resp_rdy

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return  s.src.line_trace() + " >>> " + s.sink.line_trace()

  assert _test_model( Top ) == 5 # regression: 5 cycles

def test_constraint_equal_pass_way_through():

  class Top( ComponentLevel5 ):

    def construct( s ):
      s.src  = SimpleTestSource( [1,2,3,4] )
      s.mid  = [ PassThrough() for _ in range(5) ]
      s.sink = TestSinkUp( [1,2,3,4] )


      connect( s.src.req,     s.mid[0].req )
      connect( s.src.req_rdy, s.mid[0].req_rdy )

      for i in range(4):
        s.mid[i].resp     //= s.mid[i+1].req
        s.mid[i].resp_rdy //= s.mid[i+1].resp_rdy

      s.mid[4].resp     //=  s.sink.resp
      s.mid[4].resp_rdy //= s.sink.resp_rdy

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return  s.src.line_trace() + " >>> " + s.sink.line_trace()

  assert _test_model( Top ) == 5 # regression: 5 cycles

def test_method_interface():

  class RecvIfcCL( Interface ):
    def construct( s, recv=None, rdy=None):
      s.recv = CalleePort( method = recv )
      s.rdy  = CalleePort( method = rdy )

    # Here we customize method interface connections
    def connect( s, other, parent ):
      if isinstance( other, SendIfcCL ):
        connect( s.recv, other.send )
        connect( s.rdy,  other.rdy )
        return True

      return False

  class SendIfcCL( Interface ):
    def construct( s ):
      s.send = CallerPort()
      s.rdy  = CallerPort()

    def connect( s, other, parent ):
      if isinstance( other, RecvIfcCL ):
        connect( s.send, other.recv )
        connect( s.rdy,  other.rdy )
        return True

      return False

  class SimpleTestSourceIfc( ComponentLevel5 ):

    def construct( s, msgs ):
      s.msgs = deque( msgs )

      s.req = SendIfcCL()

      s.v = 0
      @update_once
      def up_src():
        s.v = None
        if s.req.rdy() and s.msgs:
          s.v = s.msgs.popleft()
          s.req.send( s.v )

    def done( s ):
      return not s.msgs

    def line_trace( s ):
      return "{:4}".format( "" if s.v is None else s.v )

  class SimpleTestSinkIfc( ComponentLevel5 ):

    def resp_( s, msg ):
      ref = s.msgs[ s.idx ]
      s.idx += 1

      if msg != ref:
        raise TestSinkError( """
  The test sink received an incorrect message!
  - sink name    : {}
  - msg number   : {}
  - expected msg : {}
  - actual msg   : {}
  """.format( s, s.idx, ref, msg )
        )

    def resp_rdy_( s ):
      return True

    def construct( s, msgs ):
      s.msgs = list( msgs )
      s.idx  = 0

      s.resp = RecvIfcCL( recv = s.resp_, rdy = s.resp_rdy_ )

    def done( s ):
      return s.idx >= len(s.msgs)

    def line_trace( s ):
      return ""

  class Top( ComponentLevel5 ):

    def construct( s ):
      s.src  = SimpleTestSourceIfc( [1,2,3,4] )
      s.sink = SimpleTestSinkIfc( [1,2,3,4] )

      connect( s.src.req, s.sink.resp )

    def done( s ):
      return s.src.done() and s.sink.done()

    def line_trace( s ):
      return  s.src.line_trace() + " >>> " + s.sink.line_trace()

  assert _test_model( Top ) == 4 # regression: 4 cycles
