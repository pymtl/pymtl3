"""
==========================================================================
IncrMethodModular_test.py
==========================================================================
IncrMethodModular is an incrementer model with method ports for its input
and output interfaces. More specifically we are using a callee port which
is essentially a placeholder. We can connect a callee port to a method
port using the connect method, and then calling the callee port will
essentially call the method port. The framework can still automatically
infer the constraints between update blocks based on propagating
constraints along these connections. The IncrTestBench instantiates
IncrMethodModular as a child component and can then directly call methods
on this child component.

Author : Yanghui Ou
  Date : June 17, 2019

"""
from pymtl3 import *

#-------------------------------------------------------------------------
# Buffer
#-------------------------------------------------------------------------

class Buffer( Component ):
  def construct( s ):
    s.data = b8(0)

    # By scheduling writes before reads the buffer will model a wire. If
    # we reverse this constraint then the buffer will model a register.
    s.add_constraints( M(s.write) < M(s.read) )

  @method_port
  def write( s, value ):
    s.data = value

  @method_port
  def read( s ):
    return s.data

#-------------------------------------------------------------------------
# IncrMethodModular
#-------------------------------------------------------------------------

class IncrMethodModular( Component ):
  def construct( s ):

    s.write = CalleePort()
    s.read  = CalleePort()

    # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''
    # Implement the incrementer
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
    #; Declare two buffers named buf1 and buf2. Connect the write callee
    #; port to buf1's write method port and the read callee port to
    #; buf2's read method port. Then add an update block that reads data
    #; from buf1, increments it by one, and writes the result to buf1.

    s.buf1  = Buffer()
    s.buf2  = Buffer()

    # Connect the callee ports to buf1/buf2 write/read method ports
    connect( s.write, s.buf1.write )
    connect( s.read,  s.buf2.read  )

    # upB reads from buf1, increments the value by 1, and writes to buf2
    @update_once
    def upB():
      s.buf2.write( s.buf1.read() + b8(1) )

    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( int(s.buf1.data), int(s.buf2.data) )

#-------------------------------------------------------------------------
# IncrTestBench
#-------------------------------------------------------------------------

class IncrTestBench( Component ):
  def construct( s ):
    s.incr_in  = b8(10)
    s.incr_out = b8(0)

    # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''
    # Instantiate IncrMethodModular child component here
    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/

    s.incr     = IncrMethodModular()

    # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

    # UpA writes data to input
    @update_once
    def upA():
      s.incr.write( s.incr_in )
      s.incr_in += 10

    # UpC reads data from output
    @update_once
    def upC():
      s.incr_out = s.incr.read()

  def line_trace( s ):
    return "{}".format( s.incr.line_trace() )

#-------------------------------------------------------------------------
# Simulate the testbench
#-------------------------------------------------------------------------

def test_method_modular():
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
