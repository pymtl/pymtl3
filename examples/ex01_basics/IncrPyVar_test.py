"""
==========================================================================
IncrPyVar_test.py
==========================================================================
Model an incrementer using python varibales. 

Author : Yanghui Ou
  Date : June 17, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *

#-------------------------------------------------------------------------
# IncrPyVar
#-------------------------------------------------------------------------
# IncrPyVar is an incrementer model that uses python variables as internal
# buffer.

class IncrPyVar( Component ):
  def construct( s ):

    s.incr_input = b8(10)

    s.buf1 = b8(0)
    s.buf2 = b8(0)

    s.incr_output = b8(0)

    # UpA writes data to buf1
    @s.update
    def upA():
      s.buf1 = s.incr_input
      s.incr_input += b8(10)
    
    # UpB read data from buf1, increment it by 1, and write to buf2.
    @s.update
    def upB():
      s.buf2 = s.buf1 + b8(1)
    
    # UpC read data from buf2.
    @s.update
    def upC():
      s.incr_output = s.buf2

    s.add_constraints( U(upA) < U(upB) )
    s.add_constraints( U(upB) < U(upC) )

  def line_trace( s ):
    return "{:2} (+1) {:2}".format( int(s.buf1), int(s.buf2) )

#-------------------------------------------------------------------------
# Simulate the incrementer
#-------------------------------------------------------------------------

def test_pyvar():
  incr = IncrPyVar()
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
