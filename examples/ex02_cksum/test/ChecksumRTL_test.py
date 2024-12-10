"""
==========================================================================
 ChecksumRTL_test.py
==========================================================================
Test cases for RTL checksum unit.

Author : Yanghui Ou
  Date : June 6, 2019
"""
import pytest
import hypothesis
from hypothesis import strategies as st

from pymtl3 import *
from pymtl3.datatypes import strategies as pm_st
from pymtl3.passes.tracing import VcdGenerationPass, PrintTextWavePass
from pymtl3.stdlib.connects import connect_pairs
from pymtl3.stdlib.stream import StreamSinkFL, StreamSourceFL
from pymtl3.stdlib.test_utils.test_helpers import finalize_verilator, run_sim

from ..ChecksumFL import checksum
from ..ChecksumRTL import ChecksumRTL, StepUnit
from ..utils import b128_to_words, words_to_b128

#-------------------------------------------------------------------------
# Unit test the step unit
#-------------------------------------------------------------------------
# A very simple unit test for the step unit.

def test_step_unit():
  step_unit = StepUnit()
  step_unit.elaborate()
  step_unit.apply( DefaultPassGroup() )

  step_unit.word_in @= 1
  step_unit.sum1_in @= 1
  step_unit.sum2_in @= 1
  step_unit.sim_eval_combinational()
  assert step_unit.sum1_out == 2
  assert step_unit.sum2_out == 3

  step_unit.sim_tick()

#-------------------------------------------------------------------------
# Wrap RTL checksum unit into a function
#-------------------------------------------------------------------------
# Similar to [checksum_cl] in for the CL tests, [checksum_rtl] creates an
# RTL checksum unit, feeds in the input, ticks the checksum unit and gets
# the output.

def checksum_rtl( words ):
  bits_in = words_to_b128( words )

  # Create a simulator
  dut = ChecksumRTL()
  dut.elaborate()
  dut.apply( DefaultPassGroup() )
  dut.sim_reset()

  # Wait until the checksum unit is ready to receive input
  dut.ostream.rdy @= 1
  while not dut.istream.rdy:
    dut.istream.val @= 0
    dut.sim_tick()

  # Feed in the input
  dut.istream.val @= 1
  dut.istream.msg @= bits_in
  dut.sim_tick()

  # Wait until the checksum unit is about to send the message
  while not dut.ostream.val:
    dut.istream.val @= 0
    dut.sim_tick()

  # Return the result
  return dut.ostream.msg

#-------------------------------------------------------------------------
# Reuse functionality from FL test suite
#-------------------------------------------------------------------------
# Similar to what we did for FL tests, we can reuse FL test cases by
# inherit from the FL test class and overwrite cksum_func to use the rtl
# version instead.

from .ChecksumFL_test import ChecksumFL_Tests as BaseTests

@pytest.mark.usefixtures("cmdline_opts")
class ChecksumRTL_Tests( BaseTests ):

  def cksum_func( s, words ):
    return checksum_rtl( words )

  # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''
  # Use Hypothesis to test Checksum RTL
  # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
  #; Use Hypothesis to verify that ChecksumRTL has the same behavior as
  #; ChecksumFL. Simply uncomment the following test_hypothesis method
  #; and rerun pytest. Make sure that you fix the indentation so that
  #; this new test_hypothesis method is correctly indented with respect
  #; to the class ChecksumRTL_Tests
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
  #; the checksum_rtl to run a little simulation and compares the output to
  #; the checksum function from ChecksumFL.

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

    s.src  = StreamSourceFL( Bits128, src_msgs )
    s.dut  = DutType()
    s.sink = StreamSinkFL( Bits32, sink_msgs )

    connect_pairs(
      s.src.ostream, s.dut.istream,
      s.dut.ostream, s.sink.istream,
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
class ChecksumRTLSrcSink_Tests:

  # [setup_class] will be called by pytest before running all the tests in
  # the test class. Here we specify the type of the design under test
  # that is used in all test cases. We can easily reuse all the tests in
  # this class simply by creating a new test class that inherits from
  # this class and overwrite the setup_class to provide a different DUT
  # type.
  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumRTL

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
