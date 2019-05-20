#=========================================================================
# Tests for test_stateful using the queue
#=========================================================================
#
# Author: Yixiao Zhang
#   Date: May 20, 2019

from pymtl import *
from pclib.ifcs import EnqIfcRTL, DeqIfcRTL
from pymtl.dsl.test.sim_utils import simple_sim_pass
from pclib.ifcs.GuardedIfc import guarded_ifc
from pclib.test.stateful.test_stateful import run_test_state_machine
from pclib.test.stateful.test_wrapper import *
from collections import deque
import copy
import pytest


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
# NormalQueueCL
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

  @guarded_ifc( lambda s: len( s.queue ) < s.queue.maxlen )
  def enq( s, msg ):
    s.queue.appendleft( msg )

  @guarded_ifc( lambda s: len( s.queue ) > 0 )
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
# NormalQueueCL
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

  @guarded_ifc( lambda s: len( s.queue ) < s.queue.maxlen )
  def enq( s, msg ):
    s.queue.appendleft( msg )

  @guarded_ifc( lambda s: len( s.queue ) > 0 )
  def deq( s ):
    return s.queue.pop()

  def line_trace( s ):
    return str( s.queue )


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
        U( update_enq_rdy ) < M( s.enq.rdy ),
        M( s.enq.rdy ) < U( update_enq ),
        M( s.enq ) < U( update_enq ) )

  @guarded_ifc( lambda s: s.enq_rdy )
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
        U( update_deq_rdy ) < M( s.deq.rdy ),
        U( update_deq_rdy ) < M( s.deq ),
        M( s.deq.rdy ) < U( update_deq ),
        M( s.deq ) < U( update_deq ) )

  @guarded_ifc( lambda s: s.deq_rdy )
  def deq( s ):
    s.deq_called = True
    return s.deq_msg


#-------------------------------------------------------------------------
# ReferenceWrapper
#-------------------------------------------------------------------------


class ReferenceWrapper( Component ):
  model_name = "ref"

  def _construct( s ):
    Component._construct( s )

  def construct( s, model ):
    s.model = model
    s.method_specs = inspect_rtl( s.model )
    EnqRTL2CL = gen_adapter( s.model.enq, s.method_specs[ "enq" ] )
    s.enq_adapter = EnqRTL2CL( s.model.enq )
    DeqRTL2CL = gen_adapter( s.model.deq, s.method_specs[ "deq" ] )
    s.deq_adapter = DeqRTL2CL( s.model.deq )
    s.deq = GuardedCalleeIfc()
    s.enq = GuardedCalleeIfc()
    s.connect( s.deq, s.deq_adapter.deq )
    s.connect( s.enq, s.enq_adapter.enq )
    s.connect( s.enq_adapter.enq_rtl, s.model.enq )
    s.connect( s.deq_adapter.deq_rtl, s.model.deq )

  def line_trace( s ):
    return s.model.line_trace()


#-------------------------------------------------------------------------
# test_state_machine
#-------------------------------------------------------------------------
@pytest.mark.parametrize( "QueueCL, QueueRTL",
                          [( BypassQueueCL, SingleEntryBypassQueue ),
                           ( PipeQueueCL, SingleEntryPipeQueue ) ] )
def test_state_machine( QueueCL, QueueRTL ):
  # run_test_state_machine( ReferenceWrapper( QueueRTL( Bits16 ) ), QueueCL( 1 ) )
  run_test_state_machine( RTL2CLWrapper( QueueRTL( Bits16 ) ), QueueCL( 1 ) )
