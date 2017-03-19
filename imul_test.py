import random
from pymtl import *
from pclib.update import TestSourceValRdy, TestSinkValRdy
from IntMulNstage     import IntMulNstageInelastic
from IntMulVarLatFlat import IntMulVarLatFlat
from IntMulVarLatConn import IntMulVarLatConn

class TestHarness( Updates ):

  def __init__( s, model, src_msgs, sink_msgs ):

    s.src  = TestSourceValRdy( 2, src_msgs )
    s.imul = model
    s.sink = TestSinkValRdy( sink_msgs )

    s.imul.req_val   |= s.src.val
    s.imul.req_msg_a |= s.src.msg[0]
    s.imul.req_msg_b |= s.src.msg[1]
    s.src.rdy        |= s.imul.req_rdy

    s.sink.val       |= s.imul.resp_val
    s.imul.resp_rdy  |= s.sink.rdy
    s.sink.msg       |= s.imul.resp_msg

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.imul.line_trace()+" >>> "+s.sink.line_trace()

random.seed(0xdeadbeef)
src_msgs  = []
sink_msgs = []

for i in xrange(20):
  x = random.randint(0,100)
  y = random.randint(0,100)
  z = x*y
  src_msgs.append( (x,y) )
  sink_msgs.append(z)

def run_test( model ):
  th = TestHarness( model, src_msgs, sink_msgs )
  th.elaborate()
  while not th.done():
    th.cycle()
    print th.line_trace()

def test_nstage_inelastic():
  run_test( IntMulNstageInelastic(4) )

def test_varlat_connection():
  run_test( IntMulVarLatConn() )

def test_varlat_flat():
  run_test( IntMulVarLatFlat() )
