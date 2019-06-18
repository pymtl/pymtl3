"""
==========================================================================
 ChecksumCL_test.py
==========================================================================
Test cases for CL checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""
from __future__ import absolute_import, division, print_function

import hypothesis
from hypothesis import strategies as st

from pymtl3 import *
from pymtl3.stdlib.cl.queues import BypassQueueCL
from pymtl3.stdlib.test import TestSinkCL, TestSrcCL

from ..ChecksumCL import ChecksumCL
from ..ChecksumFL import checksum
from ..utils import b128_to_words, words_to_b128
from .ChecksumFL_test import ChecksumFL_Tests as BaseTests

#-------------------------------------------------------------------------
# WrappedChecksumCL
#-------------------------------------------------------------------------
# WrappedChecksumCL is a simple wrapper around the CL checksum unit. It
# simply appends an output queue to the send side of the checksum unit.
# In this way it only exposes callee interfaces which can be directly
# called by the outside world.

class WrappedChecksumCL( Component ):

  def construct( s, DutType=ChecksumCL ):
    s.recv = NonBlockingCalleeIfc( Bits128 )
    s.give = NonBlockingCalleeIfc( Bits32  )
    
    s.checksum_unit = DutType()
    s.out_q = BypassQueueCL( num_entries=1 )

    s.connect( s.recv,               s.checksum_unit.recv )
    s.connect( s.checksum_unit.send, s.out_q.enq          )
    s.connect( s.out_q.deq,          s.give               )

#-------------------------------------------------------------------------
# Wrap CL component into a function
#-------------------------------------------------------------------------
# [checksum_cl] takes a list of 16-bit words, converts it to bits, creates
# a checksum unit instance and feed in the input. It then ticks the
# checksum unit until the output is ready to be taken.

def checksum_cl( words ):
  
  # Create a simulator
  dut = WrappedChecksumCL()
  dut.apply( SimpleSim )
  
  # Wait until recv ready
  while not dut.recv.rdy():
    dut.tick()
  
  # Call recv on dut
  dut.recv( words_to_b128( words ) )
  dut.tick()
  
  # Wait until dut is ready to give result
  while not dut.give.rdy():
    dut.tick()

  return dut.give()

#-------------------------------------------------------------------------
# Reuse FL tests
#-------------------------------------------------------------------------
# By directly inhering from the FL test class, we can easily reuse all the
# FL tests. We only need to overwrite the cksum_func that is used in all
# test cases. Here we also extend the test case by adding a hypothesis
# test that compares the CL implementation against the FL as reference.

class ChecksumCL_Tests( BaseTests ):
  
  def cksum_func( s, words ):
    return checksum_cl( words )    

  # Use hypothesis to compare the wrapped CL function against FL
  @hypothesis.given(
    words = st.lists( st.integers(0, 2**16-1), min_size=8, max_size=8 ) 
  )
  @hypothesis.settings( deadline=None )
  def test_hypothesis( s, words ):
    print( words )
    words = [ b16(x) for x in words ]
    assert s.cksum_func( words ) == checksum( words )

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------
# TestHarness is used for more advanced source/sink based testing. It
# hooks a test source to the input of the design under test and a test
# sink to the output of the DUT. Test source feeds data into the DUT 
# while test sink drains data from the DUT and verifies it.

class TestHarness( Component ):
  def construct( s, DutType, src_msgs, sink_msgs ):

    s.src  = TestSrcCL( Bits128, src_msgs )
    s.dut  = DutType()
    s.sink = TestSinkCL( Bits32, sink_msgs )

    s.connect_pairs(
      s.src.send, s.dut.recv,
      s.dut.send, s.sink.recv,
    )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{}>{}>{}".format(
      s.src.line_trace(), s.dut.line_trace(), s.sink.line_trace()
    )

#-------------------------------------------------------------------------
# Src/sink based tests
#-------------------------------------------------------------------------
# We use source/sink based tests to stress test the checksum unit.

class ChecksumCLSrcSink_Tests( object ):
  
  # [setup_class] will be called by pytest before running all the tests in
  # the test class. Here we specify the type of the design under test
  # that is used in all test cases. We can easily reuse all the tests in
  # this class simply by creating a new test class that inherits from
  # this class and overwrite the setup_class to provide a different DUT
  # type.
  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumCL
  
  # [run_sim] is a helper function in the test suite that creates a
  # simulator and runs test.
  def rum_sim( s, th, max_cycles=1000 ):

    # Create a simulator
    th.apply( SimpleSim )
    ncycles = 0
    th.sim_reset()
    print( "" )
    
    # Tick the simulator
    print("{:3}: {}".format( ncycles, th.line_trace() ))
    while not th.done() and ncycles < max_cycles:
      th.tick()
      ncycles += 1
      print("{:3}: {}".format( ncycles, th.line_trace() ))

    # Check timeout
    assert ncycles < max_cycles

  def test_simple( s ):
    words = [ b16(x) for x in [ 1, 2, 3, 4, 5, 6, 7, 8 ] ]
    bits  = words_to_b128( words )

    result = b32( 0x00780024 )

    src_msgs  = [ bits   ]
    sink_msgs = [ result ]

    th = TestHarness( s.DutType, src_msgs, sink_msgs )
    s.rum_sim( th )

  def test_pipeline( s ):
    words0  = [ b16(x) for x in [ 1, 2, 3, 4, 5, 6, 7, 8 ] ]
    words1  = [ b16(x) for x in [ 8, 7, 6, 5, 4, 3, 2, 1 ] ]
    bits0   = words_to_b128( words0 )
    bits1   = words_to_b128( words1 )

    result0 = b32( 0x00780024 )
    result1 = b32( 0x00cc0024 )

    src_msgs  = [ bits0, bits1, bits0, bits1 ]
    sink_msgs = [ result0, result1, result0, result1 ]

    th = TestHarness( s.DutType, src_msgs, sink_msgs )
    s.rum_sim( th )

  def test_backpressure( s ):
    words0  = [ b16(x) for x in [ 1, 2, 3, 4, 5, 6, 7, 8 ] ]
    words1  = [ b16(x) for x in [ 8, 7, 6, 5, 4, 3, 2, 1 ] ]
    result0 = b32( 0x00780024 )
    result1 = b32( 0x00cc0024 )

    bits0 = words_to_b128( words0 )
    bits1 = words_to_b128( words1 )

    src_msgs  = [ bits0, bits1, bits0, bits1 ]
    sink_msgs = [ result0, result1, result0, result1 ]

    th = TestHarness( s.DutType, src_msgs, sink_msgs )
    th.set_param( "top.sink.construct", initial_delay=10 )
    s.rum_sim( th )
  
  # This hypothesis test not only generates a sequence of input to the
  # the checksum unit but it also configure the test source and sink with
  # different initial and interval delays.
  @hypothesis.given(
    input_msgs = st.lists( 
                   st.lists( st.integers(0, 2**16-1), min_size=8, max_size=8
                   ).map( lambda lst: [ b16(x) for x in lst ] ) 
                 ),
    src_init   = st.integers( 0, 10 ),
    src_intv   = st.integers( 0, 3  ),
    sink_init  = st.integers( 0, 10 ),
    sink_intv  = st.integers( 0, 3  ),
  )
  @hypothesis.settings( deadline=None, max_examples=16 )
  def test_hypothesis( s, input_msgs, src_init, src_intv, sink_init, sink_intv ):
    src_msgs  = [ words_to_b128( words ) for words in input_msgs ]
    sink_msgs = [ checksum( words ) for words in input_msgs ]

    th = TestHarness( s.DutType, src_msgs, sink_msgs  )
    th.set_param( "top.src.construct", initial_delay = src_init, interval_delay = src_intv )
    th.set_param( "top.sink.construct", initial_delay = sink_init, interval_delay = sink_intv )
    s.rum_sim( th )