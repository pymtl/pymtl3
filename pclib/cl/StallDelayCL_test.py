#=========================================================================
# StallDelayCL_test.py
#=========================================================================
#
# Author : Shunning Jiang
# Date   : Mar 12, 2018
import pytest
import random
import struct

from pymtl      import *
from pclib.test import mk_test_case_table

from pclib.cl.TestSourceCL import TestSimpleSource
from pclib.cl.TestSinkCL   import TestSimpleSink
from StallDelayCL import StallDelayCL, DelayPipeCL

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( ComponentLevel6 ):

  def construct( s, dut_class, src_msgs, sink_msgs, stall_prob=0, latency=0 ):

    # Messge type

    # Instantiate models

    s.src  = TestSimpleSource( src_msgs )

    if dut_class is StallDelayCL:
      s.dut = StallDelayCL( stall_prob, latency )
    elif dut_class is DelayPipeCL:
      s.dut = DelayPipeCL( latency )

    s.sink = TestSimpleSink( sink_msgs )

    # Connect

    s.connect( s.src.req,       s.dut.recv     )
    s.connect( s.src.req_rdy,   s.dut.recv_rdy )
    s.connect( s.sink.resp,     s.dut.send     )
    s.connect( s.sink.resp_rdy, s.dut.send_rdy )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace(s ):
    return s.src.line_trace() + " >>> " + s.dut.line_trace() + " >>> " + s.sink.line_trace()

from pymtl.passes.PassGroups import SimpleCLSim

def run_cl_sim( th, max_cycles=5000 ):

  # Create a simulator

  th.apply( SimpleCLSim )

  # Reset model

  #  sim.reset()
  #  print()

  # Run simulation

  ncycles = 0
  print "{:3}:{}".format( ncycles, th.line_trace() )
  while not th.done() and ncycles < max_cycles:
    th.tick()
    ncycles += 1
    print "{:3}:{}".format( ncycles, th.line_trace() )

  # Force a test failure if we timed out

  assert ncycles < max_cycles

  th.tick()
  th.tick()
  th.tick()

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
  (                       "msg_func        stall lat "),
  [ "basic",              basic_msgs,      0,    0    ],
  [ "basic0.5_lat0",      basic_msgs,      0.5,  0    ],
  [ "basic0.0_lat4",      basic_msgs,      0,    4    ],
  [ "basic0.5_lat4",      basic_msgs,      0.5,  4    ],
]) )
def test_stall_delay( test_params, dump_vcd ):
  msgs = test_params.msg_func()
  run_cl_sim( TestHarness( StallDelayCL, msgs[::2], msgs[1::2],
                           stall_prob=test_params.stall,
                           latency=test_params.lat ) )


@pytest.mark.parametrize( **mk_test_case_table([
  (                      "msg_func        lat "),
  [ "basic",             basic_msgs,      0    ],
  [ "basic_lat1",        basic_msgs,      1    ],
  [ "basic_lat4",        basic_msgs,      4    ],
  [ "basic_lat10",       basic_msgs,      10   ],
]) )
def test_delay_pipe( test_params, dump_vcd ):
  msgs = test_params.msg_func()
  run_cl_sim( TestHarness( DelayPipeCL, msgs[::2], msgs[1::2],
                           latency=test_params.lat ) )
