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

#-------------------------------------------------------------------------
# Buffer
#-------------------------------------------------------------------------
# Buffer is a pymtl component that has two callee method ports, one for
# read and the ohter for write. It looks very similar to a normal python
# object.

class Buffer( Component ):
  def construct( s ):
    s.data = b8(0)

    # Here we specify that method write needs to happen before method
    # read, which models combinational behavior. If the constraint is
    # flipped, it models sequential behavior.
    s.add_constraints( M( s.write ) < M( s.read ) )
   
  @method_port
  def write( s, value ):
    s.data = value

  @method_port
  def read( s ):
    return s.data

#-------------------------------------------------------------------------
# IncrBuf
#-------------------------------------------------------------------------
# IncrBuf is an incrementer model that uses a PyMTL component (Buffer) as
# its internal buffer.

class IncrBuf( Component ):
  def construct( s ):

    s.incr_input = b8(10)

    s.buf1 = Buffer() 
    s.buf2 = Buffer()

    s.incr_output = b8(0)
    
    # UpA writes data to buf1
    @s.update
    def upA():
      s.buf1.write( s.incr_input )
      s.incr_input += b8(10)

    # UpB read data from buf1, increment it by 1, and write to buf2.
    @s.update
    def upB():
      tmp = s.buf1.read()
      s.buf2.write( tmp+1 )
    
    # UpC read data from buf2.
    @s.update
    def upC():
      s.incr_output = s.buf2.read()

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( int(s.buf1.data), int(s.buf2.data) )

#-------------------------------------------------------------------------
# Simulate the incrementer
#-------------------------------------------------------------------------

def test_buf():
  incr = IncrBuf()
  incr.apply( SimpleSim )

  # Print out the update block schedule.
  print( "\n==== Schedule ====" )
  for blk in incr._sched.schedule:
    if not blk.__name__.startswith('s'):
      print( blk.__name__ )
  
  # Print out the simulation line trace.
  print( "\n==== Line trace ====" )
  print( "   buf1    buf2")
  for i in range( 6 ):
    incr.tick()
    print("{:2}: {}".format( i, incr.line_trace() ))