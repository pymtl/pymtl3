#=========================================================================
# DelayPipeCL_test.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : May 7, 2018

import pytest

from pymtl3 import *
from pymtl3.stdlib.test_utils import TestSinkCL, TestSrcCL, mk_test_case_table, run_sim

from ..DelayPipeCL import DelayPipeDeqCL, DelayPipeSendCL

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, dut_class, src_msgs, sink_msgs, latency, src_lat, sink_lat ):

    # Messge type

    # Instantiate models

    s.src  = TestSrcCL( None, src_msgs, 0, src_lat )
    s.dut  = dut_class( latency )
    s.sink = TestSinkCL( None, sink_msgs, 0, sink_lat )

    # Connect

    connect( s.src.send,  s.dut.enq )

    if   dut_class is DelayPipeDeqCL:
      @update_once
      def up_adapt():
        if s.dut.deq.rdy() and s.sink.recv.rdy():
          s.sink.recv( s.dut.deq() )

    elif dut_class is DelayPipeSendCL:
      connect( s.dut.send, s.sink.recv )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace(s ):
    return s.src.line_trace() + " >>> " + s.dut.line_trace() + " >>> " + s.sink.line_trace()

#-------------------------------------------------------------------------
# Test Case Table
#-------------------------------------------------------------------------

def basic_msgs():
  return [
    1, 1,
    2, 2,
    3, 3,
    4, 4,
    5, 5,
    6, 6,
    7, 7,
    8, 8,
    9, 9,
    10, 10,
  ]

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **mk_test_case_table([
  (                      "msg_func        lat   src_lat sink_lat  "),
  [ "basic",             basic_msgs,      0,    0,      0          ],
  [ "basic_lat1",        basic_msgs,      1,    0,      0          ],
  [ "basic_lat2",        basic_msgs,      2,    0,      0          ],
  [ "basic_lat3",        basic_msgs,      3,    0,      0          ],
  [ "basic_lat4",        basic_msgs,      4,    0,      0          ],
  [ "basic_lat10",       basic_msgs,      10,   0,      0          ],
  [ "basic_3_14",        basic_msgs,      0,    3,      14         ],
  [ "basic_lat1_3_14",   basic_msgs,      1,    3,      14         ],
  [ "basic_lat4_3_14",   basic_msgs,      4,    3,      14         ],
  [ "basic_lat10_3_14",  basic_msgs,      10,   3,      14         ],
]) )
def test_delay_pipe_deq( test_params, cmdline_opts ):
  msgs = test_params.msg_func()
  run_sim( TestHarness( DelayPipeDeqCL, msgs[::2], msgs[1::2],
                           test_params.lat,
                           test_params.src_lat, test_params.sink_lat ) )

@pytest.mark.parametrize( **mk_test_case_table([
  (                      "msg_func        lat   src_lat sink_lat  "),
  [ "basic",             basic_msgs,      0,    0,      0          ],
  [ "basic_lat1",        basic_msgs,      1,    0,      0          ],
  [ "basic_lat2",        basic_msgs,      2,    0,      0          ],
  [ "basic_lat3",        basic_msgs,      3,    0,      0          ],
  [ "basic_lat4",        basic_msgs,      4,    0,      0          ],
  [ "basic_lat10",       basic_msgs,      10,   0,      0          ],
  [ "basic_3_14",        basic_msgs,      0,    3,      14         ],
  [ "basic_lat1_3_14",   basic_msgs,      1,    3,      14         ],
  [ "basic_lat4_3_14",   basic_msgs,      4,    3,      14         ],
  [ "basic_lat10_3_14",  basic_msgs,      10,   3,      14         ],
]) )
def test_delay_pipe_send( test_params, cmdline_opts ):
  msgs = test_params.msg_func()
  run_sim( TestHarness( DelayPipeSendCL, msgs[::2], msgs[1::2],
                           test_params.lat,
                           test_params.src_lat, test_params.sink_lat ) )
