"""
==========================================================================
IncrPyObjs_test.py
==========================================================================
IncrPyObjs is an incrementer model that uses Python objects with method
calls for internal communication between update blocks. In this example,
we have implemented a Buffer as a regular Python object with read and
write methods. When using Python objects it is critical to explicitly
specify the desired scheduling constraints between update blocks.
Different constraints result in modeling different hardware. For example,
using the schedule upA < upB and upB < upC means buf1 and buf2 each model
a wire, while using the schedule upB < upA and upC < upB means buf1 and
buf2 each model a register.

Author : Yanghui Ou
  Date : June 17, 2019

"""
from pymtl3 import *

#-------------------------------------------------------------------------
# Buffer
#-------------------------------------------------------------------------

class Buffer:
  def __init__( s ):
    s.data = b8(0)

  def write( s, value ):
    s.data = value

  def read( s ):
    return s.data

#-------------------------------------------------------------------------
# IncrPyObjs
#-------------------------------------------------------------------------

class IncrPyObjs( Component ):
  def construct( s ):

    s.incr_in  = b8(10)
    s.incr_out = b8(0)

    s.buf1 = Buffer()
    s.buf2 = Buffer()

    # UpA writes data to buf1
    @update
    def upA():
      s.buf1.write( s.incr_in )
      s.incr_in += b8(10)

    # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''
    # Add upB update block here
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
    #; The upB update block should read data from buf1, increment it by
    #; one, and write the result to buf2 using method calls.

    @update
    def upB():
      tmp = s.buf1.read()
      s.buf2.write( tmp + b8(1) )

    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

    # UpC reads data from buf2
    @update
    def upC():
      s.incr_out = s.buf2.read()

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
    return "{:2} (+1) {:2}".format( int(s.buf1.data), int(s.buf2.data) )

#-------------------------------------------------------------------------
# Simulate the incrementer
#-------------------------------------------------------------------------

def test_py_objs():
  incr = IncrPyObjs()
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
