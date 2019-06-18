"""
==========================================================================
IncrValuePorts_test.py
==========================================================================
Create an incrementer with value ports and use a test bench to simulate
the incrementer.

Author : Yanghui Ou
  Date : June 17, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *

#-------------------------------------------------------------------------
# IncrValuePorts
#-------------------------------------------------------------------------
# IncrValuePorts is a incrementer module with value ports as its
# interface.

class IncrValuePorts( Component ):
  def construct( s ):

    s.in_ = InPort ( Bits8 )
    s.out = OutPort( Bits8 )
    
    s.buf1 = Wire( Bits8 )
    s.buf2 = Wire( Bits8 )

    s.connect( s.in_, s.buf1 )
    s.connect( s.out, s.buf2 )

    @s.update
    def upB():
      s.out = s.in_ + b8(1)

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( int(s.in_), int(s.out) )

#-------------------------------------------------------------------------
# IncrWiresTestBench
#-------------------------------------------------------------------------
# IncrWiresTestBench is a testbench for IncrValuePorts module. It creates
# an IncrValuePorts instance and interact with it via value
# ports.

class IncrWiresTestBench( Component ):
  def construct( s ):
    s.incr_input  = b8(10)
    s.incr        = IncrValuePorts()      
    s.incr_output = 0

    # UpA writes data to input
    @s.update
    def upA():
      s.incr.in_ = s.incr_input
      s.incr_input += b8(10)
    
    # UpC read data from output
    @s.update
    def upC():
      s.incr_output = s.incr.out

  def line_trace( s ):
    return "{}".format( s.incr.line_trace() )

#-------------------------------------------------------------------------
# Simulate the testbench
#-------------------------------------------------------------------------

def test_wires_tb():
  tb = IncrWiresTestBench()
  tb.apply( SimpleSim )
  
  # Print out the update block schedule.
  print( "\n==== Schedule ====" )
  for blk in tb._sched.schedule:
    if not blk.__name__.startswith('s'):
      print( blk.__name__ )
  
  # Print out the simulation line trace.
  print( "\n==== Line trace ====" )
  print( "   in_     out")
  for i in range( 6 ):
    tb.tick()
    print( "{:2}: {}".format( i, tb.line_trace() ) )
