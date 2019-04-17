#=========================================================================
# queues_test
#=========================================================================
# Use cl and rtl queues as example to test hypothesis stateful
#
# Author : Yixiao Zhang
#   Date : March 24, 2019

from pymtl import *
from pymtl.dsl import *
from pclib.rtl.queues import PipeQueue1RTL, BypassQueue1RTL
from pclib.test.stateful.test_stateful import run_test_state_machine, TestStateful
from pclib.test.stateful.test_wrapper import *
from pclib.cl.queues import PipeQueueCL, BypassQueueCL
from pclib.cl.queues_test import TestSrcCL, TestSinkCL, test_msgs, arrival_pipe, run_sim
from pymtl.passes.PassGroups import SimpleCLSim
from pymtl.dsl.ComponentLevel6 import method_port, ComponentLevel6
from pymtl.dsl.test.sim_utils import simple_sim_pass
import pytest

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