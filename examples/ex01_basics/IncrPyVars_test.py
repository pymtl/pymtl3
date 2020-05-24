"""
==========================================================================
IncrPyVars_test.py
==========================================================================
IncrPyVars is an incrementer model that uses Python variables for internal
communication between update blocks. When using Python variables it is
critical to explicitly specify the desired scheduling constraints between
update blocks. Different constraints result in modeling different
hardware. For example, using the schedule upA < upB and upB < upC means
buf1 and buf2 each model a wire, while using the schedule upB < upA and
upC < upB means buf1 and buf2 each model a register.

Author : Yanghui Ou
  Date : June 17, 2019

"""
from pymtl3 import *

#-------------------------------------------------------------------------
# IncrPyVars
#-------------------------------------------------------------------------

class IncrPyVars( Component ):
  def construct( s ):

    s.incr_in  = b8(10)
    s.incr_out = b8(0)

    s.buf1 = b8(0)
    s.buf2 = b8(0)

    # UpA writes data to buf1
    @update
    def upA():
      s.buf1 = s.incr_in
      s.incr_in += b8(10)

    # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add upB update block here
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
    #; The upB update block should read data from buf1, increment it by
    #; one, and write the result to buf2

    @update
    def upB():
      s.buf2 = s.buf1 + b8(1)

    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

    # UpC reads data from buf2
    @update
    def upC():
      s.incr_out = s.buf2

    # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add appropriate constrints here
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
    #; Start by adding constraints to ensure upA is scheduled before upB
    #; and that upB is schedule before upC. This will model combinational
    #; communication (i.e., wires) between update blocks. After simulating
    #; this design, experiment with reversing the constraints. This will
    #; model registers between update blocks. Observe the change in the
    #; line trace.

    s.add_constraints( U(upA) < U(upB), U(upB) < U(upC) )

    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( int(s.buf1), int(s.buf2) )

#-------------------------------------------------------------------------
# Simulate the incrementer
#-------------------------------------------------------------------------

def test_py_vars():
  incr = IncrPyVars()
  incr.apply( DefaultPassGroup() )

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
