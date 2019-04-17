#=========================================================================
# Tests for CL queues
#=========================================================================
#
# Author: Yanghui Ou, Yixiao Zhang
#   Date: Mar 24, 2019

import pytest

from pymtl                    import *
from pymtl.dsl.test.sim_utils import simple_sim_pass
from pclib.test.test_srcs     import TestSrcCL
from pclib.test.test_sinks    import TestSinkRTL
from pclib.test               import TestVectorSimulator
from pymtl.passes.PassGroups  import SimpleCLSim
from queues import NormalQueueRTL

#-------------------------------------------------------------------------
# TestVectorSimulator test
#-------------------------------------------------------------------------

def run_tv_test( dut, test_vectors ):

  # Define input/output functions

  def tv_in( dut, tv ):
    dut.enq.en  = tv[0]
    dut.enq.msg = tv[2]
    dut.deq.en  = tv[3]

  def tv_out( dut, tv ):
    if tv[1] != '?': assert dut.enq.rdy == tv[1]
    if tv[4] != '?': assert dut.deq.rdy == tv[4]
    if tv[5] != '?': assert dut.deq.msg == tv[5]

  # Run the test

  sim = TestVectorSimulator( dut, test_vectors, tv_in, tv_out )
  sim.run_test()

def test_pipe_Bits():

  B1  = mk_bits(1)
  B32 = mk_bits(32)
  run_tv_test( NormalQueueRTL( Bits32, 2 ), [
    #  enq.en  enq.rdy enq.msg   deq.en  deq.rdy deq.msg
    [  B1(1),  B1(1),  B32(123), B1(0),  B1(0),    '?'    ],
    [  B1(1),  B1(1),  B32(345), B1(0),  B1(1),  B32(123) ],
    [  B1(0),  B1(0),  B32(567), B1(0),  B1(1),  B32(123) ],
    [  B1(0),  B1(0),  B32(567), B1(1),  B1(1),  B32(123) ],
    [  B1(0),  B1(1),  B32(567), B1(1),  B1(1),  B32(345) ],
    [  B1(1),  B1(1),  B32(567), B1(0),  B1(0),    '?'    ],
    [  B1(1),  B1(1),  B32(0  ), B1(1),  B1(1),  B32(567) ],
    [  B1(1),  B1(1),  B32(1  ), B1(1),  B1(1),  B32(0  ) ],
    [  B1(1),  B1(1),  B32(2  ), B1(1),  B1(1),  B32(1  ) ],
    [  B1(0),  B1(1),  B32(2  ), B1(1),  B1(1),  B32(2  ) ],
] )

#-------------------------------------------------------------------------
# TestHarness
#-------------------------------------------------------------------------

class TestHarness( Component ):

  def construct( s, MsgType, qsize, src_msgs, sink_msgs, src_initial, 
                 src_interval, sink_initial, sink_interval, 
                 arrival_time=None ):

    s.src  = TestSrcCL  ( src_msgs,  src_initial,  src_interval )
    s.dut  = NormalQueueRTL( MsgType, qsize )
    s.sink = TestSinkRTL( MsgType, sink_msgs, sink_initial, sink_interval, 
                          arrival_time )
    
    s.connect( s.src.send,    s.dut.enq       )
    s.connect( s.dut.deq.msg, s.sink.recv.msg )

    @s.update
    def up_deq_send():
      if s.dut.deq.rdy and s.sink.recv.rdy:
        s.dut.deq.en   = Bits1( 1 )
        s.sink.recv.en = Bits1( 1 )
      else:
        s.dut.deq.en   = Bits1( 0 )
        s.sink.recv.en = Bits1( 0 )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{} ({}) {}".format( 
      s.src.line_trace(), s.dut.line_trace(), s.sink.line_trace() )

#-------------------------------------------------------------------------
# run_sim 
#-------------------------------------------------------------------------

def run_sim( th, max_cycles=100 ):

  # Create a simulator
  # th.elaborate()
  # th.apply( simple_sim_pass )
  th.apply( SimpleCLSim )
  th.sim_reset()

  print ""
  ncycles = 0
  print "{:2}:{}".format( ncycles, th.line_trace() )
  while not th.done() and ncycles < max_cycles:
    th.tick()
    ncycles += 1
    print "{:2}:{}".format( ncycles, th.line_trace() )
  
  # Check timeout

  assert ncycles < max_cycles

  th.tick()
  th.tick()
  th.tick()

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

test_msgs = [ Bits16( 4 ), Bits16( 1 ), Bits16( 2 ), Bits16( 3 ) ]

arrival_pipe   = [ 2, 3, 4, 5 ]

def test_normal2_simple():
  th = TestHarness( Bits16, 2, test_msgs, test_msgs, 0, 0, 0, 0,
                    arrival_pipe )
  run_sim( th )

#-------------------------------------------------------------------------
# ReferenceRTLAdapter
#-------------------------------------------------------------------------

class ReferenceRTLAdapter( RTLComponent ):

  def construct( s, rtl_model, method_specs ):
    s.enq_rdy = OutVPort( Bits1 )
    s.enq_msg = InVPort( Bits16 )
    s.deq = InVPort( Bits1 )
    s.deq_rdy = OutVPort( Bits1 )
    s.deq_msg = OutVPort( Bits16 )

    @s.update
    def update_enq():
      if s.enq:
        s.enq_rdy = s.model.enq.rdy
        if s.model.enq.rdy:
          s.model.enq.en = 1
          s.model.enq.msg = s.enq_msg
        else:
          s.model.enq.en = 0
          s.model.enq.msg = 0
      else:
        s.model.enq.en = 0
        s.enq_rdy = 0

    @s.update
    def update_deq():
      if s.deq:
        s.deq_rdy = s.model.deq.rdy
        s.deq_msg = s.model.deq.msg
        if s.model.deq.rdy:
          s.model.deq.en = 1
        else:
          s.model.deq.en = 0
      else:
        s.model.deq.en = 0

  def line_trace( s ):
    return s.model.line_trace()

#-------------------------------------------------------------------------
# ReferenceWrapper
#-------------------------------------------------------------------------

class ReferenceWrapper( ComponentLevel6 ):

  def construct( s, model ):
    s.model = model
    s.enq_called = Bits1()
    s.enq_rdy = Bits16()
    s.enq_msg = Bits16()
    s.deq_called = Bits1()
    s.deq_rdy = Bits1()
    s.deq_msg = Bits16()
    s.reset_called = Bits1()
    s.method_specs = s.inspect( s.model )


    @s.update
    def update_enq_rdy():
      s.enq_rdy = s.model.enq.rdy

    @s.update
    def update_enq_msg():
      s.model.enq.msg = s.enq_msg

    @s.update
    def update_enq():
      if s.enq_called:
        if s.model.enq.rdy:
          s.model.enq.en = 1
        else:
          s.model.enq.en = 0
      else:
        s.model.enq.en = 0
      s.enq_called = 0

    @s.update
    def update_deq_rdy():
      s.deq_rdy = s.model.deq.rdy

    @s.update
    def update_deq_msg():
      s.deq_msg = s.model.deq.msg

    @s.update
    def update_deq():
      if s.deq_called:
        if s.model.deq.rdy:
          s.model.deq.en = 1
        else:
          s.model.deq.en = 0
      else:
        s.model.deq.en = 0
      s.deq_called = 0

    s.add_constraints(
        U( update_enq_rdy ) < M( s.enq ),
        U( update_enq_rdy ) < M( s.enq.rdy ),
        M( s.enq.rdy ) < U( update_enq ),
        M( s.enq ) < U( update_enq ),
        M( s.enq ) < U( update_enq_msg ),
        U( update_deq_msg ) < M( s.deq ),
        U( update_deq_rdy ) < M( s.deq.rdy ),
        U( update_deq_rdy ) < M( s.deq ),
        M( s.deq.rdy ) < U( update_deq ),
        M( s.deq ) < U( update_deq ) )

  @method_port( lambda s: s.enq_rdy )
  def enq( s, msg ):
    s.enq_called = 1
    s.enq_msg = msg

  @method_port( lambda s: s.deq_rdy )
  def deq( s ):
    s.deq_called = 1
    return s.deq_msg

  @method_port
  def reset_( self ):
    s.reset_called = 1

  def tick( self ):
    self.model.tick()

  def line_trace( s ):
    return s.model.line_trace()

  def inspect( s, rtl_model ):
    method_specs = {}

    for method, ifc in inspect.getmembers( rtl_model ):
      args = {}
      rets = {}
      if isinstance( ifc, Interface ):
        for name, port in inspect.getmembers( ifc ):
          if name == 'en' or name == 'rdy':
            continue
          if isinstance( port, InVPort ):
            args[ name ] = port._dsl.Type
          if isinstance( port, OutVPort ):
            rets[ name ] = port._dsl.Type

        method_specs[ method ] = Method(
            method_name=method, args=args, rets=rets )
    return method_specs

class TestHarness( ComponentLevel6 ):

  def construct( s,
                 Dut,
                 src_msgs,
                 sink_msgs,
                 src_initial,
                 src_interval,
                 sink_initial,
                 sink_interval,
                 arrival_time=None ):
    s.src = TestSrcCL( src_msgs, src_initial, src_interval )
    s.dut = Dut
    s.sink = TestSinkCL( sink_msgs, sink_initial, sink_interval, arrival_time )

    print "construct harness"
    s.connect( s.src.send, s.dut.enq )

    @s.update
    def up_deq_send():
      if s.dut.deq.rdy() and s.sink.recv.rdy():
        s.sink.recv( s.dut.deq() )

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return "{} ({}) {}".format( s.src.line_trace(), s.dut.line_trace(),
                                s.sink.line_trace() )

#-------------------------------------------------------------------------
# test_wrapper
#-------------------------------------------------------------------------

@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, BypassQueue1RTL ),
                           ( PipeQueueCL, PipeQueue1RTL ) ] )
def test_wrapper( QueueCL, QueueRTL ):
  wrapper = RTL2CLWrapper( QueueRTL( Bits16 ) )
  th = TestHarness( wrapper, test_msgs, test_msgs, 0, 0, 0, 0, arrival_pipe )
  run_sim( th )

#-------------------------------------------------------------------------
# test_cl
#-------------------------------------------------------------------------

def test_cl():
  test = BypassQueueCL( 1 )
  test.apply( SimpleCLSim )
  test.tick()
  test.enq( 2 )
  deq = test.deq()

#-------------------------------------------------------------------------
# test_state_machine
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, BypassQueue1RTL ),
                           ( PipeQueueCL, PipeQueue1RTL ) ] )
def test_state_machine( QueueCL, QueueRTL ):
  test_stateful = run_test_state_machine(  RTL2CLWrapper( QueueRTL( Bits16 ) ), QueueCL( 1 ) )
>>>>>>> wrapper for teststateful
