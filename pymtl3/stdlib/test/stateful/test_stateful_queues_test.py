#=========================================================================
# test_stateful_qeueues_test
#=========================================================================
# Tests for test_stateful using single entry queue
#
# Author: Yixiao Zhang
#   Date: June 10, 2019

from __future__ import absolute_import, division, print_function

from collections import deque

import pytest

from pymtl3 import *
from pymtl3.dsl.test.sim_utils import simple_sim_pass
from pymtl3.passes import GenDAGPass, OpenLoopCLPass
from pymtl3.stdlib.ifcs import CalleeIfcRTL

from .test_stateful import run_test_state_machine
from .test_wrapper import *


#-------------------------------------------------------------------------
# SingleEntryPipeQueue
#-------------------------------------------------------------------------
class SingleEntryPipeQueue( Component ):

  def construct( s, EntryType ):

    # Interface

    s.enq = CalleeIfcRTL( ArgTypes=[( 'msg', EntryType ) ] )
    s.deq = CalleeIfcRTL( RetTypes=[( 'msg', EntryType ) ] )

    # Component

    s.queue = Wire( EntryType )
    s.full = Wire( Bits1 )

    s.connect( s.queue, s.deq.rets.msg )

    @s.update_on_edge
    def up_pq_reg():
      if s.reset:
        s.queue = EntryType()
      elif s.enq.en:
        s.queue = s.enq.args.msg
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
    return "{} ({}) {}".format( s.enq.args.msg, s.full, s.deq.rets.msg )


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

    s.enq = CalleeIfcRTL( ArgTypes=[( 'msg', EntryType ) ] )
    s.deq = CalleeIfcRTL( RetTypes=[( 'msg', EntryType ) ] )

    # Component

    s.queue = Wire( EntryType )
    s.full = Wire( Bits1 )

    @s.update_on_edge
    def up_pq_reg():
      if s.reset:
        s.queue = EntryType()
      elif s.enq.en and not s.deq.en:
        s.queue = s.enq.args.msg
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
      s.deq.rets.msg = s.enq.args.msg if s.enq.en else s.queue

  # Line trace

  def line_trace( s ):
    return "{} ({}) {}".format( s.enq.args.msg if s.enq.en else "", s.full,
                                s.deq.rets.msg if s.deq.en else "" )


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
# test_stateful_simple
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, SingleEntryBypassQueue ),
                           ( PipeQueueCL, SingleEntryPipeQueue ) ] )
def test_stateful_simple( QueueCL, QueueRTL ):
  run_test_state_machine( RTL2CLWrapper( QueueRTL( Bits16 ) ), QueueCL( 1 ) )


#-------------------------------------------------------------------------
# test_stateful_bits_struct
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, SingleEntryBypassQueue ),
                           ( PipeQueueCL, SingleEntryPipeQueue ) ] )
def test_stateful_bits_struct( QueueCL, QueueRTL ):
  Msg1Type = mk_bit_struct( "Msg1Type", [( 'msg0', Bits8 ),
                                         ( 'msg1', Bits8 ) ] )
  run_test_state_machine(
      RTL2CLWrapper(
          QueueRTL(
              mk_bit_struct( "MsgType", [( 'msg0', Bits8 ),
                                         ( 'msg1', Msg1Type ) ] ) ) ),
      QueueCL( 1 ) )


#-------------------------------------------------------------------------
# test_stateful_overwrite
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, SingleEntryBypassQueue ),
                           ( PipeQueueCL, SingleEntryPipeQueue ) ] )
def test_stateful_overwrite( QueueCL, QueueRTL ):
  run_test_state_machine(
      RTL2CLWrapper( QueueRTL( Bits32 ) ),
      QueueCL( 1 ),
      argument_strategy=[( 'enq.msg', st.integers( min_value=0,
                                                   max_value=11 ) ) ] )


#-------------------------------------------------------------------------
# test_stateful_overwrite_nested
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, SingleEntryBypassQueue ),
                           ( PipeQueueCL, SingleEntryPipeQueue ) ] )
def test_stateful_overwrite_nested( QueueCL, QueueRTL ):
  Msg1Type = mk_bit_struct( "Msg1Type", [( 'msg0', Bits8 ),
                                         ( 'msg1', Bits8 ) ] )
  run_test_state_machine(
      RTL2CLWrapper(
          QueueRTL(
              mk_bit_struct( "MsgType", [( 'msg0', Bits8 ),
                                         ( 'msg1', Msg1Type ) ] ) ) ),
      QueueCL( 1 ),
      argument_strategy=[( 'enq.msg.msg0',
                           st.integers( min_value=100, max_value=100 ) ),
                         ( 'enq.msg.msg1.msg0',
                           st.integers( min_value=200, max_value=200 ) ) ] )
