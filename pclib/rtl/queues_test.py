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
from pclib.test.stateful.test_stateful import run_test_state_machine, TestStateful, TestStatefulWrapper
from pclib.test.stateful.test_wrapper import *
from pclib.cl.queues import PipeQueueCL, BypassQueueCL
from pclib.cl.queues_test import TestSrcCL, TestSinkCL, test_msgs, arrival_pipe, run_sim
from pymtl.passes.PassGroups import SimpleCLSim
from pymtl.dsl.ComponentLevel6 import method_port, ComponentLevel6
from pymtl.dsl.test.sim_utils import simple_sim_pass
import pytest
from pclib.ifcs.EnqDeqIfcs import EnqIfcRTL, DeqIfcRTL

#-------------------------------------------------------------------------
# EnqRTL2CL
#-------------------------------------------------------------------------


class EnqRTL2CL( ComponentLevel6 ):

  def construct( s, MsgType ):

    # Interface

    s.enq_rtl = EnqIfcRTL( MsgType ).inverse()

    s.enq_called = False
    s.enq_rdy = False
    s.enq_msg = 0

    @s.update
    def update_enq():
      s.enq_rtl.en = Bits1( 1 ) if s.enq_called else Bits1( 0 )
      s.enq_rtl.msg = s.enq_msg
      s.enq_called = False

    @s.update
    def update_enq_rdy():
      s.enq_rdy = True if s.enq_rtl.rdy else False

    s.add_constraints(
        U( update_enq_rdy ) < M( s.enq ),
        U( update_enq_rdy ) < M( s.enq.rdy ),
        M( s.enq.rdy ) < U( update_enq ),
        M( s.enq ) < U( update_enq ) )

  @method_port( lambda s: s.enq_rdy )
  def enq( s, msg ):
    s.enq_msg = msg
    s.enq_called = True


#-------------------------------------------------------------------------
# DeqRTL2CL
#-------------------------------------------------------------------------


class DeqRTL2CL( ComponentLevel6 ):

  def construct( s, MsgType ):

    # Interface

    s.deq_rtl = DeqIfcRTL( MsgType ).inverse()

    s.deq_called = False
    s.deq_rdy = False
    s.deq_msg = 0

    @s.update
    def update_deq():
      s.deq_rtl.en = Bits1( 1 ) if s.deq_called else Bits1( 0 )
      s.deq_called = False

    @s.update
    def update_deq_msg():
      s.deq_msg = s.deq_rtl.msg

    @s.update
    def update_deq_rdy():
      s.deq_rdy = True if s.deq_rtl.rdy else False

    s.add_constraints(
        U( update_deq_msg ) < M( s.deq ),
        U( update_deq_rdy ) < M( s.deq.rdy ),
        U( update_deq_rdy ) < M( s.deq ),
        M( s.deq.rdy ) < U( update_deq ),
        M( s.deq ) < U( update_deq ) )

  @method_port( lambda s: s.deq_rdy )
  def deq( s ):
    s.deq_called = True
    return s.deq_msg


#-------------------------------------------------------------------------
# ReferenceWrapper
#-------------------------------------------------------------------------
class ReferenceWrapper( ComponentLevel6 ):

  def construct( s, model, MsgType ):
    s.model = model( MsgType )

    s.enq_adapter = EnqRTL2CL( MsgType )
    s.connect( s.enq_adapter.enq_rtl, s.model.enq )
    s.deq_adapter = DeqRTL2CL( MsgType )
    s.connect( s.deq_adapter.deq_rtl, s.model.deq )
    s.deq = CalleePort()
    s.enq = CalleePort()
    s.connect( s.deq, s.deq_adapter.deq )
    s.connect( s.enq, s.enq_adapter.enq )

  def line_trace( s ):
    return s.model.line_trace()


#-------------------------------------------------------------------------
# test_wrapper
#-------------------------------------------------------------------------
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
  wrapper = ReferenceWrapper( QueueRTL, Bits16 )
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
  test_stateful = run_test_state_machine(
      RTL2CLWrapper( QueueRTL( Bits16 ) ), QueueCL( 1 ) )
