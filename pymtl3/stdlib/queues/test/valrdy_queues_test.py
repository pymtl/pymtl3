from pymtl3 import *
from pymtl3.stdlib.ifcs import InValRdyIfc, OutValRdyIfc
from pymtl3.stdlib.test_utils import TestVectorSimulator

from ..valrdy_queues import *


def run_test_queue( model, test_vectors ):

  # Define functions mapping the test vector to ports in model

  def tv_in( model, tv ):
    model.enq.val @= tv[0]
    model.enq.msg @= tv[2]
    model.deq.rdy @= tv[4]

  def tv_out( model, tv ):
    if tv[1] != '?': assert model.enq.rdy == tv[1]
    if tv[3] != '?': assert model.deq.val == tv[3]
    if tv[5] != '?': assert model.deq.msg == tv[5]

  # Run the test

  sim = TestVectorSimulator( model, test_vectors, tv_in, tv_out )
  sim.run_test()

def test_bypass_Bits():

  B1  = mk_bits(1)
  B32 = mk_bits(32)
  run_test_queue( BypassQueue1RTL( Bits32 ), [
    # enq.val enq.rdy enq.msg  deq.val deq.rdy deq.msg
    [  B1(1) , B1(1) ,B32(123), B1(1) , B1(1) ,B32(123) ],
    [  B1(1) , B1(1) ,B32(345), B1(1) , B1(0) ,B32(345) ],
    [  B1(1) , B1(0) ,B32(567), B1(1) , B1(0) ,B32(345) ],
    [  B1(1) , B1(0) ,B32(567), B1(1) , B1(1) ,B32(345) ],
    [  B1(1) , B1(1) ,B32(567), B1(1) , B1(1) ,B32(567) ],
    [  B1(0) , B1(1) ,B32(0  ), B1(0) , B1(1) ,  '?'    ],
    [  B1(0) , B1(1) ,B32(0  ), B1(0) , B1(0) ,  '?'    ],
  ] )

def test_pipe_Bits():

  B1  = mk_bits(1)
  B32 = mk_bits(32)
  run_test_queue( PipeQueue1RTL( Bits32 ), [
    # enq.val enq.rdy enq.msg  deq.val deq.rdy deq.msg
    [  B1(1) , B1(1) ,B32(123), B1(0) , B1(1) ,  '?'    ],
    [  B1(1) , B1(0) ,B32(345), B1(1) , B1(0) ,B32(123) ],
    [  B1(1) , B1(0) ,B32(567), B1(1) , B1(0) ,B32(123) ],
    [  B1(1) , B1(1) ,B32(567), B1(1) , B1(1) ,B32(123) ],
    [  B1(1) , B1(1) ,B32(789), B1(1) , B1(1) ,B32(567) ],
    [  B1(0) , B1(1) ,B32(0  ), B1(1) , B1(1) ,B32(789) ],
    [  B1(0) , B1(1) ,B32(0  ), B1(0) , B1(0) ,  '?'    ],
  ] )

def test_normal_Bits():

  B1  = mk_bits(1)
  B32 = mk_bits(32)
  run_test_queue( NormalQueue1RTL( Bits32 ), [
    # enq.val enq.rdy enq.msg  deq.val deq.rdy deq.msg
    [  B1(1) , B1(1) ,B32(123), B1(0) , B1(1) ,  '?'    ],
    [  B1(1) , B1(0) ,B32(345), B1(1) , B1(0) ,B32(123) ],
    [  B1(1) , B1(0) ,B32(567), B1(1) , B1(0) ,B32(123) ],
    [  B1(1) , B1(0) ,B32(567), B1(1) , B1(1) ,B32(123) ],
    [  B1(1) , B1(1) ,B32(567), B1(0) , B1(1) ,B32(123) ],
    [  B1(0) , B1(0) ,B32(0  ), B1(1) , B1(1) ,B32(567) ],
    [  B1(0) , B1(1) ,B32(0  ), B1(0) , B1(0) ,  '?'    ],
  ] )

def test_2entry_normal_Bits():
  """Two Element Normal Queue."""
  B1  = mk_bits(1)
  B32 = mk_bits(32)
  run_test_queue( NormalQueueRTL( 2, Bits32 ), [
    # Enqueue one element and then dequeue it
    # enq_val enq_rdy enq_bits deq_val deq_rdy deq_bits
    [ B1(1), B1(1), B32(0x0001), B1(0), B1(1),      '?'    ],
    [ B1(0), B1(1), B32(0x0000), B1(1), B1(1), B32(0x0001) ],
    [ B1(0), B1(1), B32(0x0000), B1(0), B1(0),      '?'    ],

    # Fill in the queue and enq/deq at the same time
    # enq_val enq_rdy enq_bits deq_val deq_rdy deq_bits
    [ B1(1), B1(1), B32(0x0002), B1(0), B1(0),      '?'    ],
    [ B1(1), B1(1), B32(0x0003), B1(1), B1(0), B32(0x0002) ],
    [ B1(0), B1(0), B32(0x0003), B1(1), B1(0), B32(0x0002) ],
    [ B1(1), B1(0), B32(0x0003), B1(1), B1(0), B32(0x0002) ],
    [ B1(1), B1(0), B32(0x0003), B1(1), B1(1), B32(0x0002) ],
    [ B1(1), B1(1), B32(0x0004), B1(1), B1(0),      '?'    ],
    [ B1(1), B1(0), B32(0x0004), B1(1), B1(1), B32(0x0003) ],
    [ B1(1), B1(1), B32(0x0005), B1(1), B1(0),      '?'    ],
    [ B1(0), B1(0), B32(0x0005), B1(1), B1(1), B32(0x0004) ],
    [ B1(0), B1(1), B32(0x0005), B1(1), B1(1), B32(0x0005) ],
    [ B1(0), B1(1), B32(0x0005), B1(0), B1(1),      '?'    ],
  ])

def test_3entry_normal_Bits():
  """Three Element Queue."""
  B1  = mk_bits(1)
  B32 = mk_bits(32)
  run_test_queue( NormalQueueRTL( 3, Bits32 ), [
    # Enqueue one element and then dequeue it
    # enq_val enq_rdy enq_bits deq_val deq_rdy deq_bits
    [ B1(1), B1(1), B32(0x0001), B1(0), B1(1),      '?'    ],
    [ B1(0), B1(1), B32(0x0000), B1(1), B1(1), B32(0x0001) ],
    [ B1(0), B1(1), B32(0x0000), B1(0), B1(0),      '?'    ],

    # Fill in the queue and enq/deq at the same time
    # enq_val enq_rdy enq_bits deq_val deq_rdy deq_bits
    [ B1(1), B1(1), B32(0x0002), B1(0), B1(0),      '?'    ],
    [ B1(1), B1(1), B32(0x0003), B1(1), B1(0), B32(0x0002) ],
    [ B1(1), B1(1), B32(0x0004), B1(1), B1(0), B32(0x0002) ],
    [ B1(1), B1(0), B32(0x0005), B1(1), B1(0), B32(0x0002) ],
    [ B1(0), B1(0), B32(0x0005), B1(1), B1(0), B32(0x0002) ],
    [ B1(1), B1(0), B32(0x0005), B1(1), B1(1), B32(0x0002) ],
    [ B1(1), B1(1), B32(0x0005), B1(1), B1(1), B32(0x0003) ],
    [ B1(1), B1(1), B32(0x0006), B1(1), B1(1), B32(0x0004) ],
    [ B1(1), B1(1), B32(0x0007), B1(1), B1(1), B32(0x0005) ],
    [ B1(0), B1(1), B32(0x0000), B1(1), B1(1), B32(0x0006) ],
    [ B1(0), B1(1), B32(0x0000), B1(1), B1(1), B32(0x0007) ],
    [ B1(0), B1(1), B32(0x0000), B1(0), B1(1),      '?'    ],
  ])
