"""
==========================================================================
IncrMethodPorts_test.py
==========================================================================
IncrMethodPorts is an incrementer model that uses PyMTL components with
method ports for internal communication between update blocks. In this
example, we have implemented a Buffer as a PyMTL component with read and
write methods that are marked as method ports. The buffer internally
specifies constraints on the order read and write method ports can be
called. If we use method ports, then the framework can automatically
infer the constraints between update blocks based on the propagating the
constraints specified internally in the Buffer. If the Buffer specifies
that the read method should be scheduled before the write method, then an
update block that calls the write method will also be scheduled before an
update block that calls the read method. This means the Buffer models a
wire. If instead the Buffer specifies that the write method should be
scheduled _after_ the read method, then an update block that calls the
write method will also be scheduled _after_ the read method. This means
the Buffer models a register.

Author : Yanghui Ou
  Date : June 17, 2019

"""
from pymtl3 import *

#-------------------------------------------------------------------------
# Buffer
#-------------------------------------------------------------------------

# ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Implement the buffer using method ports
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
#; Buffer should inheret from Component. Implement construct, read, and
#; write methods. Use the @method_port decorator to indicate that the
#; read and write methods are method ports. Add a constraint in construct
#; to specify that writes should be scheduled before reads.

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

# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

#-------------------------------------------------------------------------
# IncrMethodPorts
#-------------------------------------------------------------------------

class IncrMethodPorts( Component ):
  def construct( s ):

    s.incr_in  = b8(10)
    s.incr_out = b8(0)

    s.buf1 = Buffer()
    s.buf2 = Buffer()

    # UpA writes data to buf1
    @update_once
    def upA():
      s.buf1.write( s.incr_in )
      s.incr_in += b8(10)

    # UpB reads data from buf1, increments it by 1, and writes to buf2
    @update_once
    def upB():
      tmp = s.buf1.read()
      s.buf2.write( tmp + b8(1) )

    # UpC reads data from buf2
    @update_once
    def upC():
      s.incr_out = s.buf2.read()

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( int(s.buf1.data), int(s.buf2.data) )

#-------------------------------------------------------------------------
# Simulate the incrementer
#-------------------------------------------------------------------------

def test_method_ports():
  incr = IncrMethodPorts()
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
