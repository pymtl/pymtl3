#=========================================================================
# test_stateful
#=========================================================================
# Hypothesis stateful testing on RTL and CL model
#
# Author : Yixiao Zhang
#   Date : May 22, 2019

from pymtl import *
from pymtl.passes import OpenLoopCLPass, GenDAGPass
from hypothesis.stateful import *
from hypothesis import settings, given, seed, PrintSettings, Verbosity
import hypothesis.strategies as st

from test_wrapper import *
from test_stateful_queues_test import SingleEntryBypassQueue, BypassQueueCL

#-------------------------------------------------------------------------
# QueueMachine
#-------------------------------------------------------------------------


class QueueMachine( RuleBasedStateMachine ):

  def __init__( s ):
    super( QueueMachine, s ).__init__()
    s.dut = RTL2CLWrapper( SingleEntryBypassQueue( Bits16 ) )
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
    s.ref.hide_line_trace = True

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
  machine = QueueMachine
  machine.TestCase.settings = settings(
      max_examples=50,
      stateful_step_count=100,
      deadline=None,
      verbosity=Verbosity.verbose,
      database=None )
  run_state_machine_as_test( machine )
