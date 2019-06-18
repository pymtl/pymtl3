"""
==========================================================================
IncrBuf_test.py
==========================================================================
Model an incrementer using PyMTL component with method ports and method
constraints.

Author : Yanghui Ou
  Date : June 17, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *

from .IncrBuf_test import Buffer

#-------------------------------------------------------------------------
# IncrMethodPorts
#-------------------------------------------------------------------------
# IncrValuePorts is a incrementer module with method ports as its
# interface.

class IncrMethodPorts( Component ):
  def construct( s ):

    s.write = CalleePort()
    s.read  = CalleePort()
    
    s.buf1 = Buffer()
    s.buf2 = Buffer()
    
    # Connect the write method port to buf1's write and the read port to
    # buf2's read.
    s.connect( s.write, s.buf1.write )
    s.connect( s.read,  s.buf2.read  )
    
    # upB reads from buf1, increment the balue by 1 and write to buf2.
    @s.update
    def upB():
      s.buf2.write( s.buf1.read() + 1 )

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( int(s.buf1.data), int(s.buf2.data) )

#-------------------------------------------------------------------------
# IncrMethodPortsTestBench
#-------------------------------------------------------------------------
# IncrMethodPortsTestBench is a testbench for IncrMethodPorts. It creates
# an IncrMethodPorts instance and interact with it via method ports. 

class IncrMethodPortsTestBench( Component ):
  def construct( s ):
    s.incr_input  = b8(10)
    s.incr        = IncrMethodPorts()      
    s.incr_output = b8(0)

    # UpA writes data to input
    @s.update
    def upA():
      s.incr.write( s.incr_input )
      s.incr_input += 10
    
    # UpC read data from output
    @s.update
    def upC():
      s.incr_output = s.incr.read()

  def line_trace( s ):
    return "{}".format( s.incr.line_trace() )

#-------------------------------------------------------------------------
# Simulate the testbench
#-------------------------------------------------------------------------

def test_mehod_ports():
  tb = IncrMethodPortsTestBench()
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
