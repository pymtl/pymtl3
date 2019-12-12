"""
==========================================================================
RTL2CLWrapper_test.py
==========================================================================
Test cases for RTL2CLWrapper.

Author : Yanghui Ou
  Date : July 10, 2019
"""
from pymtl3 import *
from pymtl3.passes import AutoTickSimPass
from pymtl3.stdlib.rtl.queues import NormalQueueRTL, PipeQueueRTL
from pymtl3.stdlib.test.pyh2.RTL2CLWrapper import RTL2CLWrapper
from pymtl3.stdlib.test.test_sinks import TestSinkCL
from pymtl3.stdlib.test.test_srcs import TestSrcCL


class TestHarness(Component):
  def construct( s, model ):
    s.src = TestSrcCL( Bits16, [b16(4),b16(3),b16(2),b16(1),b16(7),b16(6),b16(5)],
                       interval_delay=3, initial_delay=4 )

    s.dut = model( enq = s.src.send )

    s.sink = TestSinkCL( Bits16, [b16(4),b16(3),b16(2),b16(1),b16(7),b16(6),b16(5)],
                       interval_delay=4, initial_delay=5 )

    @s.update
    def up_adapt():
      if s.dut.deq.rdy() and s.sink.recv.rdy():
        s.sink.recv( s.dut.deq() )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return f"{s.src.line_trace()} >>> {s.dut.line_trace()} >>> {s.sink.line_trace()}"

def test_wrapper_normalqueue():
  top = TestHarness( RTL2CLWrapper( NormalQueueRTL( Bits16, num_entries=2 ) ) )
  top.apply( SimulationPass() )
  top.sim_reset()

  cycles = 0
  while not top.done() and cycles < 100:
    top.tick()
    print(cycles, top.line_trace())

  assert cycles < 100

def test_wrapper_openloop_pipequeue():
  top = RTL2CLWrapper( PipeQueueRTL( Bits16, num_entries=2 ) )
  top.apply( AutoTickSimPass() )

  while not top.enq.rdy():
    pass

  top.enq( b16(0xffff) )
  top.enq( b16(0x1111) )
  # print( top.enq.rdy() )
  top.enq( b16(0x2222) )
  top.enq( b16(0x3333) )
  top.enq( b16(0x3333) )
  top.enq( b16(0x3333) )
  top.enq( b16(0x3333) )
  top.enq( b16(0x3333) )
  top.enq( b16(0x3333) )
  top.enq( b16(0x3333) )

  assert top.deq() == 0xffff
  assert top.deq() == 0x1111
  assert not top.deq.rdy()

def test_wrapper_openloop_normalqueue():
  top = RTL2CLWrapper( NormalQueueRTL( Bits16, num_entries=2 ) )
  top.apply( AutoTickSimPass() )

  while not top.enq.rdy():
    pass

  top.enq( b16(0xffff) )
  top.enq( b16(0x1111) )
  # print( top.enq.rdy() )
  top.enq( b16(0x2222) )
  top.enq( b16(0x3333) )
  top.enq( b16(0x3333) )
  top.enq( b16(0x3333) )
  top.enq( b16(0x3333) )
  top.enq( b16(0x3333) )
  top.enq( b16(0x3333) )
  top.enq( b16(0x3333) )

  assert top.deq() == 0xffff
  assert top.deq() == 0x1111
  assert not top.deq.rdy()
