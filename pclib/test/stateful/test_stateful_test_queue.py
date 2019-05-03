#=========================================================================
# Tests for test_stateful using the queue
#=========================================================================
#
# Author: Yixiao Zhang
#   Date: May 2, 2019

from pymtl import *
from pclib.ifcs import EnqIfcRTL, DeqIfcRTL
from pclib.ifcs.GuardedIfc import guarded_ifc
from pclib.test.stateful.test_stateful import run_test_state_machine
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

  @guarded_ifc( lambda s: len( s.queue ) == 0 )
  def enq( s, msg ):
    s.queue.appendleft( msg )

  @guarded_ifc( lambda s: len( s.queue ) > 0 )
  def deq( s ):
    return s.queue.pop()


#-------------------------------------------------------------------------
# test_state_machine
#-------------------------------------------------------------------------
def test_state_machine():
  test_stateful = run_test_state_machine(
      RTL2CLWrapper( SingleEntryNormalQueue( Bits16 ) ), NormalQueueCL( 1 ) )
