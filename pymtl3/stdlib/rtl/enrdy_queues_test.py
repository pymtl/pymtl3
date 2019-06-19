"""
========================================================================
enrdy_queues_test.py
========================================================================

Author : Shunning Jiang
Date   : Mar 9, 2018
"""
from __future__ import absolute_import, division, print_function

import pytest

from pymtl3 import *
from pymtl3.stdlib.test import TestSinkCL, TestSrcCL

from .enrdy_queues import *

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, Type, q, src_msgs, sink_msgs, src_interval, sink_interval ):

    # Instantiate models

    s.src  = TestSrcCL( Type, src_msgs, interval_delay=src_interval )
    s.q    = q
    s.sink = TestSinkCL( Type, sink_msgs, interval_delay=sink_interval )

    # Connect

    s.connect( s.src.send, s.q.enq )
    s.connect( s.sink.recv, s.q.deq )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace(s ):
    return s.src.line_trace() + " " + s.q.line_trace() + " " + s.sink.line_trace()

def run_sim( model ):
  model.apply( SimpleSim )

  print()
  cycle = 0
  model.sim_reset()
  while not model.done() and cycle < 1000:
    model.tick()
    print( "{:3}: {}".format( cycle, model.line_trace() ) )
    cycle += 1

  assert cycle < 1000

  model.tick()
  model.tick()
  model.tick()


F = lambda x: Bits32(x)

req  = map( F, [1,2,3,4,5,6,7,8,9,10] )
resp = map( F, [1,2,3,4,5,6,7,8,9,10] )

def test_normal_queue():
  run_sim( TestHarness( Bits32, NormalQueue1RTL(Bits32), req, resp, 0, 0 ) )

def test_normal_queue_stall():
  run_sim( TestHarness( Bits32, NormalQueue1RTL(Bits32), req, resp, 3, 4 ) )

def test_pipe_queue():
  run_sim( TestHarness( Bits32, PipeQueue1RTL(Bits32), req, resp, 0, 0 ) )

def test_pipe_queue_stall():
  run_sim( TestHarness( Bits32, PipeQueue1RTL(Bits32), req, resp, 3, 4  ) )

def test_bypass_queue():
  run_sim( TestHarness( Bits32, BypassQueue1RTL(Bits32), req, resp, 0, 0 ) )

def test_bypass_queue_stall():
  run_sim( TestHarness( Bits32, BypassQueue1RTL(Bits32), req, resp, 3, 4  ) )

def test_bypass_queue2():
  run_sim( TestHarness( Bits32, BypassQueue2RTL(Bits32), req, resp, 0, 0 ) )

def test_bypass_queue2_stall():
  run_sim( TestHarness( Bits32, BypassQueue2RTL(Bits32), req, resp, 3, 4  ) )
