"""
=========================================================================
 StallCL.py
=========================================================================
 Models random stall

 Author : Shunning Jiang
 Date   : Feb 6, 2020
"""

from random import Random

from pymtl3 import *

# This stall is for testing purpose
# Recv side has a random stall

class StallCL( Component ):

  # ready <==> stall_rand > stall_prob
  @non_blocking( lambda s: s.stall_rgen.random() > s.stall_prob and s.send.rdy() )
  def recv( s, msg ):
    s.send( msg )

  def construct( s, stall_prob=0.5, stall_seed=0x1 ):

    s.send = CallerIfcCL()

    s.stall_prob = stall_prob
    s.stall_rgen = Random( stall_seed ) # Separate randgen for each injector

    s.add_constraints(
      M(s.recv)     == M(s.send),  # pass_through
      M(s.recv.rdy) == M(s.send.rdy),  # pass_through
    )


  def line_trace( s ):
    return f"{s.recv}"
