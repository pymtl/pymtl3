#=========================================================================
# test_stateful_qeueues_test
#=========================================================================
# Tests for test_stateful using single entry queue
#
# Author: Yixiao Zhang
#   Date: May 20, 2019

from __future__ import absolute_import, division, print_function

from collections import deque

import pytest

from pymtl3 import *
from pymtl3.dsl.test.sim_utils import simple_sim_pass
from pymtl3.passes import GenDAGPass, OpenLoopCLPass
from pymtl3.stdlib.ifcs import DeqIfcRTL, EnqIfcRTL

from .test_stateful import run_test_state_machine
from .test_wrapper import *


#-------------------------------------------------------------------------
# SingleEntryPipeQueue
#-------------------------------------------------------------------------
class SingleEntryPipeQueue( Component ):

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
      elif not s.full and s.enq.en:
        s.full = Bits1( 1 )
      elif s.full and not s.enq.en and s.deq.en:
        s.full = Bits1( 0 )
      else:
        s.full = s.full

    @s.update
    def up_pq_enq_rdy():
      if not s.full or ( s.full and s.deq.en ):
        s.enq.rdy = Bits1( 1 )
      else:
        s.enq.rdy = Bits1( 0 )

    @s.update
    def up_pq_deq_rdy():
      s.deq.rdy = s.full

  # Line trace

  def line_trace( s ):
    return "{}({}){}".format( s.enq, s.full, s.deq )


#-------------------------------------------------------------------------
# PipeQueueCL
#-------------------------------------------------------------------------
class PipeQueueCL( Component ):

  def construct( s, size=1 ):
    s.queue = deque( maxlen=size )
    s.enq_rdy = True
    s.deq_rdy = False

    @s.update
    def up_pulse():
      s.enq_rdy = len( s.queue ) < s.queue.maxlen
      s.deq_rdy = len( s.queue ) > 0

    s.add_constraints( M( s.deq ) < M( s.enq ) )

  @non_blocking( lambda s: len( s.queue ) < s.queue.maxlen )
  def enq( s, msg ):
    s.queue.appendleft( msg )

  @non_blocking( lambda s: len( s.queue ) > 0 )
  def deq( s ):
    return s.queue.pop()

  def line_trace( s ):
    return str( s.queue )


#-------------------------------------------------------------------------
# SingleEntryBypassQueue
#-------------------------------------------------------------------------
class SingleEntryBypassQueue( Component ):

  def construct( s, EntryType ):

    # Interface

    s.enq = EnqIfcRTL( EntryType )
    s.deq = DeqIfcRTL( EntryType )

    # Component

    s.queue = Wire( EntryType )
    s.full = Wire( Bits1 )

    @s.update_on_edge
    def up_pq_reg():
      if s.reset:
        s.queue = EntryType()
      elif s.enq.en and not s.deq.en:
        s.queue = s.enq.msg
      else:
        s.queue = s.queue

    @s.update_on_edge
    def up_bq_full():
      if s.reset:
        s.full = Bits1( 0 )
      elif not s.full and s.enq.en and not s.deq.en:
        s.full = Bits1( 1 )
      elif s.full and not s.enq.en and s.deq.en:
        s.full = Bits1( 0 )
      else:
        s.full = s.full

    @s.update
    def up_bq_enq_rdy():
      s.enq.rdy = not s.full

    @s.update
    def up_bq_deq_rdy():
      s.deq.rdy = s.full or s.enq.en

    @s.update
    def up_bq_deq_msg():
      s.deq.msg = s.enq.msg if s.enq.en else s.queue

  # Line trace

  def line_trace( s ):
    return "{}({}){}".format( s.enq, s.full, s.deq )


#-------------------------------------------------------------------------
# BypassQueueCL
#-------------------------------------------------------------------------
class BypassQueueCL( Component ):

  def construct( s, size=1 ):
    s.queue = deque( maxlen=size )
    s.enq_rdy = True
    s.deq_rdy = False

    @s.update
    def up_pulse():
      s.enq_rdy = len( s.queue ) < s.queue.maxlen
      s.deq_rdy = len( s.queue ) > 0

    s.add_constraints( M( s.enq ) < M( s.deq ) )

  @non_blocking( lambda s: len( s.queue ) < s.queue.maxlen )
  def enq( s, msg ):
    s.queue.appendleft( msg )

  @non_blocking( lambda s: len( s.queue ) > 0 )
  def deq( s ):
    return s.queue.pop()

  def line_trace( s ):
    return str( s.queue )


#-------------------------------------------------------------------------
# test_state_machine
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, SingleEntryBypassQueue ),
                           ( PipeQueueCL, SingleEntryPipeQueue ) ] )
def test_state_machine( QueueCL, QueueRTL ):
  run_test_state_machine( RTL2CLWrapper( QueueRTL( Bits16 ) ), QueueCL( 1 ) )
