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

from .ChecksumCL import ChecksumCL
from .ChecksumFL import checksum
from .ChecksumFL_test import ChecksumFL_Tests as BaseTests
from .utils import b128_to_words, words_to_b128

#-------------------------------------------------------------------------
# Wrap CL component into a function
#-------------------------------------------------------------------------

class WrappedChecksumCL( Component ):

  def construct( s, DutType=ChecksumCL ):
    s.recv = NonBlockingCalleeIfc( Bits128 )
    s.give = NonBlockingCalleeIfc( Bits32  )
    
    s.checksum_unit = DutType()
    s.out_q = BypassQueueCL( num_entries=1 )

    s.connect( s.recv,               s.checksum_unit.recv )
    s.connect( s.checksum_unit.send, s.out_q.enq          )
    s.connect( s.out_q.deq,          s.give               )

def checksum_cl( words ):

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

class ChecksumCL_Tests( BaseTests ):
  
  def cksum_func( s, words ):
    return checksum_cl( words )    

  # Use hypothesis to compare the wrapped CL function against FL
  @hypothesis.given(
    words = st.lists( st.integers(0, 2**16-1), min_size=8, max_size=8 ) 
  )
  def test_hypothesis( s, words ):
    words = [ b16(x) for x in words ]
    assert s.cksum_func( words ) == checksum( words )

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

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

  def run_sim( s, max_cycles=1000 ):
    # Run simulation
    print("")
    ncycles = 0
    s.sim_reset()
    print("{:3}: {}".format( ncycles, s.line_trace() ))
    while not s.done() and ncycles < max_cycles:
      s.tick()
      ncycles += 1
      print("{:3}: {}".format( ncycles, s.line_trace() ))

    # Check timeout
    assert ncycles < max_cycles


#-------------------------------------------------------------------------
# Src/sink based tests
#-------------------------------------------------------------------------

class ChecksumCLSrcSink_Tests( object ):

  @classmethod
  def setup_class( cls ):
    cls.DutType = ChecksumCL
  
  # TODO: clean this up.
  def test_simple( s ):
    words = [ b16(x) for x in [ 1, 2, 3, 4, 5, 6, 7, 8 ] ]
    bits  = words_to_b128( words )

    result = b32( 0x00780024 )

    src_msgs  = [ bits   ]
    sink_msgs = [ result ]

    th = TestHarness( s.DutType, src_msgs, sink_msgs )
    th.apply( SimpleSim )
    th.run_sim()

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
    th.apply( SimpleSim )
    th.run_sim()

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
    th.apply( SimpleSim )
    th.run_sim()
  
  # TODO: clean this up with bits strategy.
  @hypothesis.given(
    input_msgs = st.lists( 
                   st.lists( st.integers(0, 2**16-1), min_size=8, max_size=8
                   ).map( lambda lst: [ b16(x) for x in lst ] ) 
                 ),
    nstages    = st.integers( 0, 8  ),
    src_init   = st.integers( 0, 10 ),
    src_intv   = st.integers( 0, 3  ),
    sink_init  = st.integers( 0, 10 ),
    sink_intv  = st.integers( 0, 3  ),
  )
  def test_hypothesis( s, input_msgs, nstages, src_init, src_intv, sink_init, sink_intv ):
    for words in input_msgs:
      words = [ b16(x) for x in words ]
    src_msgs  = [ words_to_b128( words ) for words in input_msgs ]
    sink_msgs = [ checksum( words ) for words in input_msgs ]

    th = TestHarness( s.DutType, src_msgs, sink_msgs  )
    th.set_param( "top.src.construct", initial_delay = src_init, interval_delay = src_intv )
    th.set_param( "top.sink.construct", initial_delay = sink_init, interval_delay = sink_intv )
    th.apply( SimpleSim )
    th.run_sim()