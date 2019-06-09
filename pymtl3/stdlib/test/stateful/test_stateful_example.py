#=========================================================================
# test_stateful
#=========================================================================
# Hypothesis stateful testing on RTL and CL model
#
# Author : Yixiao Zhang
#   Date : May 22, 2019

from pymtl3 import *
from pymtl3.passes import OpenLoopCLPass, GenDAGPass
from hypothesis.stateful import *
from hypothesis import settings, Verbosity
import hypothesis.strategies as st

from .test_wrapper import *
from .test_stateful_test import SingleEntryBypassQueue, BypassQueueCL

#-------------------------------------------------------------------------
# EnqRTL2CL
#-------------------------------------------------------------------------


class EnqRTL2CL( Component ):

  def construct( s, enq ):

    enq_rtl = copy.deepcopy( enq )
    enq_rtl._dsl.constructed = False
    s.enq_rtl = enq_rtl.inverse()

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
        M( s.enq ) < U( update_enq ) )

  @non_blocking( lambda s: s.enq_rdy )
  def enq( s, msg ):
    s.enq_msg = msg
    s.enq_called = True


#-------------------------------------------------------------------------
# DeqRTL2CL
#-------------------------------------------------------------------------


class DeqRTL2CL( Component ):

  def construct( s, deq ):

    # Interface

    deq_rtl = copy.deepcopy( deq )
    deq_rtl._dsl.constructed = False
    s.deq_rtl = deq_rtl.inverse()

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
        U( update_deq_rdy ) < M( s.deq ),
        M( s.deq ) < U( update_deq ) )

  @non_blocking( lambda s: s.deq_rdy )
  def deq( s ):
    s.deq_called = True
    return s.deq_msg


#-------------------------------------------------------------------------
# ReferenceWrapper
#-------------------------------------------------------------------------


class ExampleWrapper( Component ):
  model_name = "ref"

  def _construct( s ):
    Component._construct( s )

  def construct( s, model ):
    s.model = model
    s.method_specs = inspect_rtl( s.model )
    s.enq_adapter = EnqRTL2CL( s.model.enq )
    s.deq_adapter = DeqRTL2CL( s.model.deq )
    s.deq = NonBlockingCalleeIfc()
    s.enq = NonBlockingCalleeIfc()
    s.connect( s.deq, s.deq_adapter.deq )
    s.connect( s.enq, s.enq_adapter.enq )
    s.connect( s.enq_adapter.enq_rtl, s.model.enq )
    s.connect( s.deq_adapter.deq_rtl, s.model.deq )

  def line_trace( s ):
    return s.model.line_trace()


#-------------------------------------------------------------------------
# QueueMachine
#-------------------------------------------------------------------------


class QueueMachine( RuleBasedStateMachine ):

  def __init__( s ):
    super( QueueMachine, s ).__init__()
    s.dut = ExampleWrapper( SingleEntryBypassQueue( Bits16 ) )
    s.ref = BypassQueueCL( 1 )

    # elaborate dut
    s.dut.elaborate()
    s.dut.apply( GenDAGPass() )
    s.dut.apply( OpenLoopCLPass() )
    s.dut.lock_in_simulation()

    # elaborate ref
    s.ref.elaborate()
    s.ref.apply( GenDAGPass() )
    s.ref.apply( OpenLoopCLPass() )
    s.ref.lock_in_simulation()

  def deq_rdy( s ):
    dut_rdy = s.dut.deq.rdy()
    ref_rdy = s.ref.deq.rdy()
    assert dut_rdy == ref_rdy
    return dut_rdy

  @precondition( lambda s: s.deq_rdy() )
  @rule()
  def deq( s ):
    assert s.dut.deq() == s.ref.deq()

  def enq_rdy( s ):
    dut_rdy = s.dut.enq.rdy()
    ref_rdy = s.ref.enq.rdy()
    assert dut_rdy == ref_rdy
    return dut_rdy

  @precondition( lambda s: s.enq_rdy() )
  @rule( msg=st.integers( min_value=0, max_value=15 ) )
  def enq( s, msg ):
    s.dut.enq( msg=msg )
    s.ref.enq( msg=msg )


#-------------------------------------------------------------------------
# test_stateful
#-------------------------------------------------------------------------


def test_stateful():
  run_state_machine_as_test( QueueMachine )
