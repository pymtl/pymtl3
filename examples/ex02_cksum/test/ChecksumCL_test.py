"""
==========================================================================
ChecksumCL_test.py
==========================================================================
Test cases for CL checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""

import pytest
import hypothesis
from hypothesis import strategies as st

from pymtl3 import *
from pymtl3.datatypes import strategies as pm_st
from pymtl3.stdlib.queues import BypassQueueCL
from pymtl3.stdlib.connects import connect_pairs
from pymtl3.stdlib.test_utils import TestSinkCL, TestSrcCL, run_sim

from ..ChecksumCL import ChecksumCL
from ..ChecksumFL import checksum
from ..utils import b128_to_words, words_to_b128

#-------------------------------------------------------------------------
# WrappedChecksumCL
#-------------------------------------------------------------------------
# WrappedChecksumCL is a simple wrapper around the CL checksum unit. It
# simply appends an output queue to the send side of the checksum unit.
# In this way it only exposes callee interfaces which can be directly
# called by the outside world.

class WrappedChecksumCL( Component ):

  def construct( s, DutType=ChecksumCL ):
    s.recv = CalleeIfcCL( Type=Bits128 )
    s.give = CalleeIfcCL( Type=Bits32  )

    s.checksum_unit = DutType()
    s.out_q = BypassQueueCL( num_entries=1 )

    connect_pairs(
      s.recv,               s.checksum_unit.recv,
      s.checksum_unit.send, s.out_q.enq,
      s.out_q.deq,          s.give,
    )

#-------------------------------------------------------------------------
# Wrap CL component into a function
#-------------------------------------------------------------------------
# [checksum_cl] takes a list of 16-bit words, converts it to bits, creates
# a checksum unit instance and feed in the input. It then ticks the
# checksum unit until the output is ready to be taken.

def checksum_cl( words ):

  # Create a simulator
  dut = WrappedChecksumCL()
  dut.elaborate()
  dut.apply( DefaultPassGroup() )
  dut.sim_reset()

  # Wait until recv ready
  while not dut.recv.rdy():
    dut.sim_tick()

  # Call recv on dut
  dut.recv( words_to_b128( words ) )
  dut.sim_tick()

  # Wait until dut is ready to give result
  while not dut.give.rdy():
    dut.sim_tick()

  return dut.give()

#-------------------------------------------------------------------------
# Reuse FL tests
#-------------------------------------------------------------------------
# By directly inhering from the FL test class, we can easily reuse all the
# FL tests. We only need to overwrite the cksum_func that is used in all
# test cases. Here we also extend the test case by adding a hypothesis
# test that compares the CL implementation against the FL as reference.

from .ChecksumFL_test import ChecksumFL_Tests as BaseTests

class ChecksumCL_Tests( BaseTests ):

  def cksum_func( s, words ):
    return checksum_cl( words )

  # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''
  # Use Hypothesis to test Checksum CL
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
  #; Use Hypothesis to verify that ChecksumCL has the same behavior as
  #; ChecksumFL. Simply uncomment the following test_hypothesis method
  #; and rerun pytest. Make sure that you fix the indentation so that
  #; this new test_hypothesis method is correctly indented with respect
  #; to the class ChecksumCL_Tests
  #;
  #;   @hypothesis.settings( deadline=None )
  #;   @hypothesis.given(
  #;     words=st.lists( pm_st.bits(16), min_size=8, max_size=8 )
  #;   )
  #;   def test_hypothesis( s, words ):
  #;     print( [ int(x) for x in words ] )
  #;     assert s.cksum_func( words ) == checksum( words )
  #;
  #; This new test uses Hypothesis to generate random inputs, then uses
  #; the checksum_cl to run a little simulation and compares the output to
  #; the checksum function from ChecksumFL.
  #;
  #; To really see Hypothesis in action, go back to ChecksumCL and
  #; corrupt one word of the input by forcing it to always be zero. For
  #; example, change the update block in the CL implementation to be
  #; something like this:
  #;
  #;   @update
  #;   def up_checksum_cl():
  #;     if s.pipe.enq.rdy() and s.in_q.deq.rdy():
  #;       bits = s.in_q.deq()
  #;       words = b128_to_words( bits )
  #;       words[5] = b16(0) # <--- INJECT A BUG!
  #;       result = checksum( words )
  #;       s.pipe.enq( result ) !\vspace{0.07in}!
  #;     if s.send.rdy() and s.pipe.deq.rdy():
  #;       s.send( s.pipe.deq() )

  @hypothesis.settings( deadline=None )
  @hypothesis.given(
    words = st.lists( pm_st.bits(16), min_size=8, max_size=8 )
  )
  def test_hypothesis( s, words ):
    print( [ int(x) for x in words ] )
    assert s.cksum_func( words ) == checksum( words )

  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

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

    connect_pairs(
      s.src.send, s.dut.recv,
      s.dut.send, s.sink.recv,
    )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{}>{}>{}".format(
      s.src.line_trace(), s.dut.line_trace(), s.sink.line_trace()
    )

#=========================================================================
# Src/sink based tests
#=========================================================================
# We use source/sink based tests to stress test the checksum unit.

@pytest.mark.usefixtures("cmdline_opts")
class ChecksumCLSrcSink_Tests:

  # [setup_class] will be called by pytest before running all the tests in
  # the test class. Here we specify the type of the design under test
  # that is used in all test cases. We can easily reuse all the tests in
  # this class simply by creating a new test class that inherits from
  # this class and overwrite the setup_class to provide a different DUT
  # type.
  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumCL

  #-----------------------------------------------------------------------
  # run_sim
  #-----------------------------------------------------------------------
  # A helper function in the test suite that creates a simulator and
  # runs test. We can overwrite this function when inheriting from the
  # test class to apply different passes to the DUT.

  def run_sim( s, th ):
    run_sim( th, s.__class__.cmdline_opts )

  #-----------------------------------------------------------------------
  # test_srcsink_simple
  #-----------------------------------------------------------------------
  # is a simple test case with only 1 input.

  def test_srcsink_simple( s ):
    words = [ b16(x) for x in [ 1, 2, 3, 4, 5, 6, 7, 8 ] ]
    bits  = words_to_b128( words )

    result = b32( 0x00780024 )

    src_msgs  = [ bits   ]
    sink_msgs = [ result ]

    th = TestHarness( s.DutType, src_msgs, sink_msgs )
    s.run_sim( th )

  #-----------------------------------------------------------------------
  # test_srcsink_pipeline
  #-----------------------------------------------------------------------
  # test the checksum unit with a sequence of inputs.

  def test_srcsink_pipeline( s ):
    words0  = [ b16(x) for x in [ 1, 2, 3, 4, 5, 6, 7, 8 ] ]
    words1  = [ b16(x) for x in [ 8, 7, 6, 5, 4, 3, 2, 1 ] ]
    bits0   = words_to_b128( words0 )
    bits1   = words_to_b128( words1 )

    result0 = b32( 0x00780024 )
    result1 = b32( 0x00cc0024 )

    src_msgs  = [ bits0, bits1, bits0, bits1 ]
    sink_msgs = [ result0, result1, result0, result1 ]

    th = TestHarness( s.DutType, src_msgs, sink_msgs )
    s.run_sim( th )

  #-----------------------------------------------------------------------
  # test_srcsink_backpressure
  #-----------------------------------------------------------------------
  # test the checksum unit with a large sink delay.

  def test_srcsink_backpressure( s ):
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
    s.run_sim( th )

  # '''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\//
  # Cutting out this hypothesis test since in the new flow we only want
  # the attendees to write a single hypothesis test above ... and we
  # don't want them to get confused by this additional hypothesis test.

  # This hypothesis test not only generates a sequence of input to the
  # the checksum unit but it also configure the test source and sink with
  # different initial and interval delays.
  @hypothesis.given(
    input_msgs = st.lists( st.lists( pm_st.bits(16), min_size=8, max_size=8 ) ),
    src_init   = st.integers( 0, 10 ),
    src_intv   = st.integers( 0, 3  ),
    sink_init  = st.integers( 0, 10 ),
    sink_intv  = st.integers( 0, 3  ),
  )
  @hypothesis.settings( deadline=None, max_examples=50 )
  def test_srcsink_hypothesis( s, input_msgs, src_init, src_intv, sink_init, sink_intv ):
    src_msgs  = [ words_to_b128( words ) for words in input_msgs ]
    sink_msgs = [ checksum( words ) for words in input_msgs ]

    th = TestHarness( s.DutType, src_msgs, sink_msgs  )
    th.set_param( "top.src.construct", initial_delay = src_init, interval_delay = src_intv )
    th.set_param( "top.sink.construct", initial_delay = sink_init, interval_delay = sink_intv )
    s.run_sim( th )
