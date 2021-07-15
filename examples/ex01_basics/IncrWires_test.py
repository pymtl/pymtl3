"""
==========================================================================
IncrWires_test.py
==========================================================================
IncrWires is an incrementer model that uses wires for internal
communication between update blocks. If we use wires, then the framework
can automatically infer the constraints between update blocks to ensure
that an update block that writes wire X is scheduled before an update
block that reads wire X. Using update_on_edge instead of update indicates
that the framework should schedule an update block that reads wire X
_before_ an update block that writes wire X. This will enable modeling
sequential state.

Author : Yanghui Ou
  Date : June 17, 2019

"""
from pymtl3 import *

#-------------------------------------------------------------------------
# IncrWires
#-------------------------------------------------------------------------

class IncrWires( Component ):
  def construct( s ):

    s.incr_in  = b8(10)
    s.incr_out = b8(0)

    s.buf1 = Wire( Bits8 )
    s.buf2 = Wire( Bits8 )

    # UpA writes data to buf1
    @update
    def upA():
      s.buf1 @= s.incr_in
      s.incr_in += b8(10)

    # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add upB update block here
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
    #; The upB update block should read data from buf1, increment it by
    #; one, and write the result to buf2. After simulating this design,
    #; experiment with change all three update blocks to update_on_edge
    #; and observe the change in the line trace.

    @update
    def upB():
      s.buf2 @= s.buf1 + b8(1)

    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

    # UpC read data from buf2
    @update
    def upC():
      s.incr_out = s.buf2

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( int(s.buf1), int(s.buf2) )

#-------------------------------------------------------------------------
# Simulate the incrementer
#-------------------------------------------------------------------------

def test_wires():
  incr = IncrWires()
  incr.apply( DefaultPassGroup(linetrace=True) )

  # Print out the update block schedule.
  print( "\n==== Schedule ====" )
  for blk in incr._sched.update_schedule:
    if not blk.__name__.startswith('s'):
      print( blk.__name__ )

  # Print out the simulation line trace.
  print( "\n==== Line trace ====" )
  print( "   buf1    buf2")
  incr.sim_reset()
  for i in range( 6 ):
    incr.sim_tick()
