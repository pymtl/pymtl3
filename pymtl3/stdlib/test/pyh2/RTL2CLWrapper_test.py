"""
==========================================================================
RTL2CLWrapper_test.py
==========================================================================
Test cases for RTL2CLWrapper.

Author : Yanghui Ou
  Date : July 10, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.passes import GenDAGPass, OpenLoopCLPass
from pymtl3.stdlib.rtl.queues import NormalQueueRTL

from .RTL2CLWrapper import RTL2CLWrapper


def test_wrapper():

  top = RTL2CLWrapper(
    NormalQueueRTL( Bits16, num_entries=2 ),
    { 'enq': None, 'deq': None }
  )
  top.elaborate()
  top.apply( SimulationPass )
  top.sim_reset()

  while not top.enq.rdy():
    print( top.line_trace() )
    top.tick()

  assert top.enq.rdy()
  top.enq( b16(0xffff) )
  print( top.line_trace() )
  top.tick()

  while not top.deq.rdy():
    print( top.line_trace() )
    top.tick()

  assert top.deq.rdy()
  ret = top.deq()
  print( top.line_trace() )
  assert ret == 0xffff

def test_wrapper_openloop():
  top = RTL2CLWrapper(
    NormalQueueRTL( Bits16, num_entries=2 ),
    { 'enq': None, 'deq': None }
  )
  top.elaborate()
  top.apply( GenDAGPass() )
  top.apply( OpenLoopCLPass() )
  top.lock_in_simulation()

  while not top.enq.rdy():
    pass

  top.enq( b16(0xffff) )
  top.enq( b16(0x1111) )
  print( top.enq.rdy() )
  top.enq( b16(0x2222) )
  top.enq( b16(0x3333) )

  assert top.deq() == 0xffff
  assert top.deq() == 0x1111
  assert top.deq() == 0x2222
  assert top.deq() == 0x3333
