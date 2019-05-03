#=========================================================================
# Tests for test_stateful using the queue
#=========================================================================
#
# Author: Yixiao Zhang
#   Date: May 2, 2019

from pymtl import *
from pclib.ifcs import EnqIfcRTL, DeqIfcRTL
from pymtl.dsl.test.sim_utils import simple_sim_pass
from pclib.ifcs.GuardedIfc import guarded_ifc
from pclib.test.stateful.test_stateful import run_test_state_machine, TestStateful
from pclib.test.stateful.test_wrapper import *
from collections import deque

#-------------------------------------------------------------------------
# SingleEntryPipeQueue
#-------------------------------------------------------------------------


class SingleEntryNormalQueue( Component ):

  def construct( s, EntryType ):

    # Interface

    s.enq = EnqIfcRTL( EntryType )
    s.deq = DeqIfcRTL( EntryType )

    # Component

    s.queue = Wire( EntryType )
    s.full = Wire( Bits1 )

    s.connect( s.queue, s.deq.msg )

    @s.update_on_edge
    def up_pq_reg():
      if s.reset:
        s.queue = EntryType()
      elif s.enq.en:
        s.queue = s.enq.msg
      else:
        s.queue = s.queue

    @s.update_on_edge
    def up_pq_full():
      if s.reset:
        s.full = Bits1( 0 )
      elif s.enq.en:
        s.full = Bits1( 1 )
      elif s.deq.en:
        s.full = Bits1( 0 )
      else:
        s.full = s.full

    @s.update
    def up_pq_enq_rdy():
      s.enq.rdy = not s.full

    @s.update
    def up_pq_deq_rdy():
      s.deq.rdy = s.full

  # Line trace
  def line_trace( s ):
    return "{}({}){}".format( s.enq, s.full, s.deq )


#-------------------------------------------------------------------------
# NormalQueueCL
#-------------------------------------------------------------------------


class NormalQueueCL( Component ):

  def construct( s, size=1 ):
    s.queue = deque( maxlen=size )
    s.enq_rdy = True
    s.deq_rdy = False

    @s.update
    def up_pulse():
      s.enq_rdy = len( s.queue ) < s.queue.maxlen
      s.deq_rdy = len( s.queue ) > 0

    s.add_constraints(
        U( up_pulse ) < M( s.enq.rdy ),
        U( up_pulse ) < M( s.deq.rdy ) )

  @guarded_ifc( lambda s: s.enq_rdy )
  def enq( s, msg ):
    s.queue.appendleft( msg )

  @guarded_ifc( lambda s: s.deq_rdy )
  def deq( s ):
    return s.queue.pop()


#-------------------------------------------------------------------------
# test_state_machine
#-------------------------------------------------------------------------
def test_state_machine():
  test_stateful = run_test_state_machine(
      RTL2CLWrapper( SingleEntryNormalQueue( Bits16 ) ), NormalQueueCL( 1 ) )
