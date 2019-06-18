"""
==========================================================================
IncrPyObj_test.py
==========================================================================
Model an incrementer using python objects.

Author : Yanghui Ou
  Date : June 17, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *

#-------------------------------------------------------------------------
# BufferObj
#-------------------------------------------------------------------------
# BufferObj is a normal python object that models a buffer. It exposes
# a read and a write method to access its stored data.

class BufferObj( object ):
  def __init__( s ):
    s.data = b8(0)
   
  def write( s, value ):
    s.data = value

  def read( s ):
    return s.data

#-------------------------------------------------------------------------
# IncrObj
#-------------------------------------------------------------------------
# IncrObj is a incrementer model that uses normal python objects
# (BufferObj) as internal buffer.

class IncrObj( Component ):
  def construct( s ):

    s.incr_input = b8(10)

    s.buf1 = BufferObj() 
    s.buf2 = BufferObj()

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
      s.buf2.write( tmp+b8(1) )
    
    # UpC read data from buf2.
    @s.update
    def upC():
      s.incr_output = s.buf2.read()
    
    # Specify the execution order of update blocks.
    s.add_constraints( U(upA) < U(upB) )
    s.add_constraints( U(upB) < U(upC) )

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( int(s.buf1.data), int(s.buf2.data) )

#-------------------------------------------------------------------------
# Simulate the incrementer
#-------------------------------------------------------------------------

def test_pyobj():
  incr = IncrObj()
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