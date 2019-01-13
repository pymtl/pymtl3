#=========================================================================
# NullCacheCL_test.py
#=========================================================================

import pytest
import random
import struct

from pymtl      import *
from pclib.test import mk_test_case_table

from pclib.cl.MemMsg import mk_mem_msg
from pclib.cl.TestMemoryCL import TwoPortTestMemoryCL
from pclib.cl.TestSourceCL import TestSimpleSource
from pclib.cl.TestSinkCL   import TestSimpleSink
from StallDelayCL import StallDelayCL

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( ComponentLevel5 ):

  def construct( s, src_msgs, sink_msgs, stall_prob, latency, src_lat, sink_lat ):

    # Messge type

    # Instantiate models

    s.src  = TestSimpleSource( src_msgs )
    s.dut  = StallDelayCL( stall_prob, latency )
    s.sink = TestSimpleSink  ( sink_msgs )

    # Connect

    s.connect( s.src.req,       s.dut.recv     )
    s.connect( s.src.req_rdy,   s.dut.recv_rdy )
    s.connect( s.sink.resp,     s.dut.send     )
    s.connect( s.sink.resp_rdy, s.dut.send_rdy )

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

test_case_table = mk_test_case_table([
  (                       "msg_func        stall lat src sink"),
  [ "basic",              basic_msgs,      0,    0,  0,  0    ],
  [ "basic0.5_lat0",      basic_msgs,      0.5,  0,  0,  0    ],
  [ "basic0.0_lat4",      basic_msgs,      0,    4,  0,  0    ],
  [ "basic0.5_lat4",      basic_msgs,      0.5,  4,  0,  0    ],
])

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------
from pymtl.passes.PassGroups import SimpleCLSim

def run_cl_sim( th, max_cycles=5000 ):

  # Create a simulator

  th.apply( SimpleCLSim )

  # Reset model

  #  sim.reset()
  #  print()

  # Run simulation

  ncycles = 0
  print "{}:{}".format( ncycles, th.line_trace() )
  while not th.done() and ncycles < max_cycles:
    th.tick()
    ncycles += 1
    print "{}:{}".format( ncycles, th.line_trace() )

  # Force a test failure if we timed out

  assert ncycles < max_cycles

  # Extra ticks to make VCD easier to read

  th.tick()
  th.tick()
  th.tick()

@pytest.mark.parametrize( **test_case_table )
def test_1port( test_params, dump_vcd ):
  msgs = test_params.msg_func()
  run_cl_sim( TestHarness( msgs[::2], msgs[1::2],
                        test_params.stall, test_params.lat,
                        test_params.src, test_params.sink ) )

