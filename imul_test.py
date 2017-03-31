import random
from pymtl import *
from pclib.bundle import TestSource, TestSink, ValRdyBundle
from IntMulNstage import IntMulNstageInelastic
from IntMulVarLat import IntMulVarLat

class TestHarness( Updates ):

  def __init__( s, model, src_msgs, sink_msgs ):

    s.src  = TestSource( Bits64, src_msgs )
    s.imul = model
    s.sink = TestSink( Bits32, sink_msgs )

    s.imul.req.val  |= s.src.out.val
    s.imul.req.msg  |= s.src.out.msg
    s.src.out.rdy   |= s.imul.req.rdy

    s.sink.in_.val  |= s.imul.resp.val
    s.imul.resp.rdy |= s.sink.in_.rdy
    s.sink.in_.msg  |= s.imul.resp.msg

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.imul.line_trace()+" >>> "+s.sink.line_trace()

random.seed(0xdeadbeef)
src_msgs  = []
sink_msgs = []

for i in xrange(20):
  x = random.randint(0, 100)
  y = random.randint(0, 100)
  z = Bits64(0)
  z[0:32]  = x
  z[32:64] = y
  src_msgs.append( z )
  sink_msgs.append( Bits32( x * y ) )

def run_test( model ):
  th = TestHarness( model, src_msgs, sink_msgs )
  th.elaborate()
  while not th.done():
    th.cycle()
    print th.line_trace()

def test_nstage_inelastic():
  run_test( IntMulNstageInelastic(4) )

def test_varlat_connection():
  run_test( IntMulVarLat() )
