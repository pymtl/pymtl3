#=========================================================================
# queues_test
#=========================================================================
# Use cl and rtl queues as example to test hypothesis stateful
#
# Author : Yixiao Zhang
#   Date : March 24, 2019

from pymtl import *
from pymtl.dsl import *
from pymtl.passes.PassGroups import SimpleCLSim
from pclib.rtl.queues import PipeQueue1RTL, BypassQueue1RTL
from pclib.test.stateful.test_stateful import run_test_state_machine, TestStateful
from pclib.test.stateful.test_wrapper import *
from pclib.cl.Queue import PipeQueue, BypassQueue
import pytest

#-------------------------------------------------------------------------
# ReferenceRTLAdapter
#-------------------------------------------------------------------------


class ReferenceRTLAdapter( RTLComponent ):

  def construct( s, rtl_model, method_specs ):
    s.model = rtl_model
    s.enq = InVPort( Bits1 )
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
class ReferenceWrapper( object ):

  def __init__( self, model ):
    self.model = model
    self.model.apply( SimpleSim )
    self.enq_result = Result()
    self.deq_result = Result()

  def enq( self, msg ):
    self.model.enq = 1
    self.model.enq_msg = msg
    return self.enq_result

  def deq( self ):
    self.model.deq = 1
    return self.deq_result

  def cycle( self ):
    self.model.tick()
    self.enq_result.rdy = self.model.enq_rdy
    self.deq_result.rdy = self.model.deq_rdy
    self.deq_result.msg = self.model.deq_msg
    self.model.deq = 0
    self.model.enq = 0

  def reset( s ):
    pass


#-------------------------------------------------------------------------
# test_wrapper
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueue, BypassQueue1RTL ),
                           ( PipeQueue, PipeQueue1RTL ) ] )
def test_wrapper( QueueCL, QueueRTL ):
  specs = TestStateful.inspect( QueueRTL( Bits16 ), QueueCL( 1 ) )
  wrapper = RTLWrapper( RTLAdapter( QueueRTL( Bits16 ), specs ) )
  reference = ReferenceWrapper(
      ReferenceRTLAdapter( QueueRTL( Bits16 ), specs ) )
  wrapper_enq = wrapper.enq( msg=2 )
  wrapper_deq = wrapper.deq()
  reference_enq = reference.enq( msg=2 )
  reference_deq = reference.deq()
  wrapper.cycle()
  reference.cycle()
  assert wrapper_enq == reference_enq
  assert wrapper_deq == wrapper_deq


#-------------------------------------------------------------------------
# test_cl
#-------------------------------------------------------------------------
def test_cl():
  test = BypassQueue( 1 )
  test.apply( SimpleCLSim )
  test.tick()
  print test.enq_rdy(), test.deq_rdy()
  test.enq( 2 )
  deq = test.deq()
  print deq


#-------------------------------------------------------------------------
# test_state_machine
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL, order",
                          [( BypassQueue, BypassQueue1RTL, [ 'enq', 'deq' ] ),
                           ( PipeQueue, PipeQueue1RTL, [ 'deq', 'enq' ] ) ] )
def test_state_machine( QueueCL, QueueRTL, order ):
  test = run_test_state_machine(
      QueueRTL, ( Bits16,), QueueCL( 1 ), order=order )
