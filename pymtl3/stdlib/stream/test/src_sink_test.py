"""
========================================================================
src_sink_test
========================================================================
Tests for test sources and test sinks.

Author : Yanghui Ou
  Date : Mar 11, 2019
"""
import pytest

from pymtl3 import *

from pymtl3.stdlib.test_utils import run_sim
from pymtl3.stdlib.stream.StreamSinkFL import PyMTLTestSinkError, StreamSinkFL
from pymtl3.stdlib.stream.StreamSourceFL import StreamSourceFL

#-------------------------------------------------------------------------
# TestHarnessSimple
#-------------------------------------------------------------------------
# Test a single pair of test src/sink.

class TestHarnessSimple( Component ):

  def construct( s, MsgType, SrcType, SinkType, src_msgs, sink_msgs ):

    s.src  = SrcType ( MsgType, src_msgs  )
    s.sink = SinkType( MsgType, sink_msgs )

    connect( s.src.ostream, s.sink.istream )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{} > {}".format( s.src.line_trace(), s.sink.line_trace() )

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

# int_msgs = [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 ]
bit_msgs = [ Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ),
             Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ),
             Bits16( 0 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ) ]

arrival0 = [ 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 ]
arrival1 = [ 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22 ]
arrival2 = [ 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35 ]
arrival3 = [ 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35 ]
arrival4 = [ 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65 ]


@pytest.mark.parametrize(
  ('Type', 'msgs', 'src_init', 'src_intv', 'src_mode',
   'sink_init', 'sink_intv', 'sink_mode', 'arrival_time' ),
  [
    ( Bits16, bit_msgs,  0,  0, 'fixed',  0,  0, 'fixed',  arrival0 ),
    ( Bits16, bit_msgs, 10,  1, 'fixed',  0,  0, 'fixed',  arrival2 ),
    ( Bits16, bit_msgs, 10,  0, 'fixed',  0,  1, 'fixed',  arrival3 ),
    ( Bits16, bit_msgs,  3,  4, 'fixed',  5,  3, 'fixed',  arrival4 ),
    ( Bits16, bit_msgs,  0, 10, 'random', 0,  0, 'fixed',  None     ),
    ( Bits16, bit_msgs,  0, 40, 'random', 0,  0, 'fixed',  None     ),
    ( Bits16, bit_msgs,  0,  0, 'fixed',  0, 10, 'random', None     ),
    ( Bits16, bit_msgs,  0,  0, 'fixed',  0, 40, 'random', None     ),
    ( Bits16, bit_msgs,  0, 10, 'random', 0, 10, 'random', None     ),
    ( Bits16, bit_msgs,  0, 40, 'random', 0, 40, 'random', None     ),
  ]
)
def test_src_sink_rtl( Type, msgs, src_init, src_intv, src_mode,
                       sink_init, sink_intv, sink_mode, arrival_time ):
  th = TestHarnessSimple( Type, StreamSourceFL, StreamSinkFL, msgs, msgs )
  th.set_param( "top.src.construct",
    initial_delay       = src_init,
    interval_delay      = src_intv,
    interval_delay_mode = src_mode,
  )
  th.set_param( "top.sink.construct",
    initial_delay       = sink_init,
    interval_delay      = sink_intv,
    interval_delay_mode = sink_mode,
    arrival_time        = arrival_time,
  )
  run_sim( th )

#-------------------------------------------------------------------------
# Error message test
#-------------------------------------------------------------------------

def test_error_more_msg():
  try:
    th = TestHarnessSimple(
      Bits16, StreamSourceFL, StreamSinkFL,
      src_msgs  = [ b16(0xface), b16(0xface) ],
      sink_msgs = [ b16(0xface) ],
    )
    run_sim( th )
  except PyMTLTestSinkError as e:
    return
  raise Exception( 'Failed to detect error!' )

def test_error_wrong_msg():
  try:
    th = TestHarnessSimple(
      Bits16, StreamSourceFL, StreamSinkFL,
      src_msgs  = [ b16(0xface), b16(0xface) ],
      sink_msgs = [ b16(0xface), b16(0xdead) ],
    )
    run_sim( th )
  except PyMTLTestSinkError as e:
    return
  raise Exception( 'Fail to detect error!' )

def test_error_late_msg():
  try:
    th = TestHarnessSimple(
      Bits16, StreamSourceFL, StreamSinkFL,
      src_msgs  = [ b16(0xface), b16(0xface) ],
      sink_msgs = [ b16(0xface), b16(0xdead) ],
    )
    th.set_param( 'top.src.construct', initial_delay=5 )
    th.set_param( 'top.sink.construct', arrival_time=[1,2] )
    run_sim( th )
  except PyMTLTestSinkError as e:
    return
  raise Exception( 'Fail to detect error!')

#-------------------------------------------------------------------------
# Customized compare function test
#-------------------------------------------------------------------------

def test_customized_cmp():
  th = TestHarnessSimple(
    Bits4, StreamSourceFL, StreamSinkFL,
    src_msgs  = [ b4(0b1110), b4(0b1111) ],
    sink_msgs = [ b4(0b0010), b4(0b0011) ],
  )
  th.set_param( 'top.sink.construct', cmp_fn=lambda a, b: a[0:2] == b[0:2] )
  run_sim( th )

#-------------------------------------------------------------------------
# Test unordered sink
#-------------------------------------------------------------------------

def test_unordered_sink():
  th = TestHarnessSimple(
    Bits4, StreamSourceFL, StreamSinkFL,
    src_msgs  = [ b4(4), b4(3), b4(2), b4(1) ],
    sink_msgs = [ b4(1), b4(2), b4(3), b4(4) ],
  )
  th.set_param( 'top.sink.construct', ordered=False )
  run_sim( th )

def test_error_unordered_sink():
  try:
    th = TestHarnessSimple(
      Bits4, StreamSourceFL, StreamSinkFL,
      src_msgs  = [ b4(4), b4(3), b4(2), b4(1) ],
      sink_msgs = [ b4(1), b4(0), b4(3), b4(4) ],
    )
    th.set_param( 'top.sink.construct', ordered=False )
    run_sim( th )
  except PyMTLTestSinkError as e:
    return
  raise Exception( 'Fail to detect error!')

