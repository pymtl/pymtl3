"""
==========================================================================
IncrValueModular_test.py
==========================================================================
IncrValueModular is an incrementer model with value ports for its input and
output interfaces. We can connect ports and wires using the connect
method. Just as with wires, the framework can automatically infer the
constraints between update blocks to ensure that an update block that
writes value port X is scheduled before an update block that reads value
port X. The IncrTestBench instantiates IncrValueModular as a child
component and can then directly write this child component's input ports
and directly read this child component's output ports.

Author : Yanghui Ou
  Date : June 17, 2019

"""
from pymtl3 import *

#-------------------------------------------------------------------------
# IncrValueModular
#-------------------------------------------------------------------------

class IncrValueModular( Component ):
  def construct( s ):

    s.in_ = InPort ( Bits8 )
    s.out = OutPort( Bits8 )

    # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''
    # Implement the incrementer
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
    #; Declare two wires named buf1 and buf2. Connect the input port to
    #; buf1 and the output port to buf2. Then add an update block that
    #; reads data from buf1, increments it by one, and writes the result
    #; to buf2.

    s.buf1 = Wire( Bits8 )
    s.buf2 = Wire( Bits8 )

    connect( s.in_, s.buf1 )
    s.out //= s.buf2

    @update
    def upB():
      s.buf2 @= s.buf1 + b8(1)

    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( int(s.in_), int(s.out) )

#-------------------------------------------------------------------------
# IncrTestBench
#-------------------------------------------------------------------------

class IncrTestBench( Component ):
  def construct( s ):
    s.incr_in  = b8(10)
    s.incr_out = b8(0)

    # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''
    # Instantiate IncrValueModular child component here
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

    s.incr = IncrValueModular()

    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

    # UpA writes data to input
    @update
    def upA():
      s.incr.in_ @= s.incr_in
      s.incr_in  += b8(10)

    # UpC read data from output
    @update
    def upC():
      s.incr_out = s.incr.out

  def line_trace( s ):
    return "{}".format( s.incr.line_trace() )

#-------------------------------------------------------------------------
# Simulate the testbench
#-------------------------------------------------------------------------

def test_value_modular():
  tb = IncrTestBench()
  tb.apply( DefaultPassGroup() )

  # Print out the update block schedule.
  print( "\n==== Schedule ====" )
  for blk in tb._sched.update_schedule:
    if not blk.__name__.startswith('s'):
      print( blk.__name__ )

  # Print out the simulation line trace.
  print( "\n==== Line trace ====" )
  print( "   in_     out")
  tb.sim_reset()
  for i in range( 6 ):
    tb.sim_tick()
