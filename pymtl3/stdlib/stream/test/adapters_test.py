import pytest

from pymtl3 import *
from pymtl3.stdlib.stream import StreamSourceFL, StreamSinkFL
from pymtl3.stdlib.stream.ifcs import IStreamIfc, OStreamIfc
from pymtl3.stdlib.test_utils import run_sim

from ..IStreamNonBlockingAdapterFL import IStreamNonBlockingAdapterFL
from ..OStreamNonBlockingAdapterFL import OStreamNonBlockingAdapterFL
from ..IStreamBlockingAdapterFL import IStreamBlockingAdapterFL
from ..OStreamBlockingAdapterFL import OStreamBlockingAdapterFL

class SimpleNonBlockingPassthroughFL( Component ):
  def construct( s, Type ):
    s.istream = IStreamIfc( Type )
    s.ostream = OStreamIfc( Type )
    s.ideq_adapter = IStreamNonBlockingAdapterFL( Type )
    s.oenq_adapter = OStreamNonBlockingAdapterFL( Type )

    s.istream //= s.ideq_adapter.istream
    s.oenq_adapter.ostream //= s.ostream

    @update_once
    def up_passthrough():
      if s.ideq_adapter.deq.rdy() and s.oenq_adapter.enq.rdy():
        msg = s.ideq_adapter.deq()
        s.oenq_adapter.enq( msg )

  def line_trace( s ):
    return f"{s.ideq_adapter.line_trace()} | {s.oenq_adapter.line_trace()}"

class SimpleBlockingPassthroughFL( Component ):
  def construct( s, Type ):
    s.istream = IStreamIfc( Type )
    s.ostream = OStreamIfc( Type )
    s.ideq_adapter = IStreamBlockingAdapterFL( Type )
    s.oenq_adapter = OStreamBlockingAdapterFL( Type )

    s.istream //= s.ideq_adapter.istream
    s.oenq_adapter.ostream //= s.ostream

    @update_once
    def up_passthrough():
      msg = s.ideq_adapter.deq()
      s.oenq_adapter.enq( msg )

  def line_trace( s ):
    return f"{s.ideq_adapter.line_trace()} | {s.oenq_adapter.line_trace()}"

class TestHarness( Component ):
  def construct( s, DutClass, Type, src_msgs, sink_msgs ):
    s.src = StreamSourceFL( Type, src_msgs )
    s.sink = StreamSinkFL( Type, sink_msgs )
    s.dut = DutClass( Type )

    s.src.ostream //= s.dut.istream
    s.dut.ostream //= s.sink.istream

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return f"{s.src.line_trace()} ({s.dut.line_trace()}) {s.sink.line_trace()}"

bit_msgs = [ Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ),
             Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ),
             Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ) ]

arrival0 = [ 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 ]
arrival1 = [ 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22 ]
arrival2 = [ 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35 ]
arrival3 = [ 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35 ]
arrival4 = [ 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65 ]

@pytest.mark.parametrize(
  ('DutClass', 'Type', 'msgs', 'src_init',  'src_intv',
   'sink_init', 'sink_intv' ),
  [
    ( SimpleNonBlockingPassthroughFL, Bits16, bit_msgs,  0,  0, 0, 0 ),
    ( SimpleNonBlockingPassthroughFL, Bits16, bit_msgs, 10,  1, 0, 0 ),
    ( SimpleNonBlockingPassthroughFL, Bits16, bit_msgs, 10,  0, 0, 1 ),
    ( SimpleNonBlockingPassthroughFL, Bits16, bit_msgs,  3,  4, 5, 3 ),
    ( SimpleBlockingPassthroughFL,    Bits16, bit_msgs,  0,  0, 0, 0 ),
    ( SimpleBlockingPassthroughFL,    Bits16, bit_msgs, 10,  1, 0, 0 ),
    ( SimpleBlockingPassthroughFL,    Bits16, bit_msgs, 10,  0, 0, 1 ),
    ( SimpleBlockingPassthroughFL,    Bits16, bit_msgs,  3,  4, 5, 3 ),
  ]
)
def test_src_sink_fl_adapter( DutClass, Type, msgs, src_init, src_intv,
                              sink_init, sink_intv ):
  th = TestHarness( DutClass, Type, msgs, msgs )
  th.set_param( "top.src.construct",
    initial_delay  = src_init,
    interval_delay = src_intv,
  )
  th.set_param( "top.sink.construct",
    initial_delay  = sink_init,
    interval_delay = sink_intv,
  )
  run_sim( th )
