#=========================================================================
# Tests for test_stateful using a queue
#=========================================================================
#
# Author: Yixiao Zhang
#   Date: May 1, 2019

from pymtl import *
from pclib.ifcs.GuardedIfc import guarded_ifc
from pclib.rtl import RegEnRst, RegRst, RegEn
from pclib.test.stateful.test_stateful import run_test_state_machine
from pclib.test.stateful.test_wrapper import *
import math
from collections import deque

#-------------------------------------------------------------------------
# EnqIfcRTL
#-------------------------------------------------------------------------


class EnqIfcRTL( Interface ):

  def construct( s, Type, IndexType ):

    s.value = InPort( Type )
    s.en = InPort( Bits1 )
    s.rdy = OutPort( Bits1 )

  def line_trace( s ):
    return ""

  def __str__( s ):
    return s.line_trace()



#-------------------------------------------------------------------------
# DeqIfcRTL
#-------------------------------------------------------------------------


class DeqIfcRTL( Interface ):

  def construct( s, Type ):

    s.value = OutPort( Type )
    s.en = InPort( Bits1 )
    s.rdy = OutPort( Bits1 )


#-------------------------------------------------------------------------
# ReorderBuffer
#-------------------------------------------------------------------------


class NormalQueueRTL( Component ):
  # This stores (key, value) pairs in a finite size FIFO queue
  def construct( s, DataType, num_entries ):
    # We want to be a power of two so mod arithmetic is efficient
    idx_nbits = clog2( num_entries )
    assert 2**idx_nbits == num_entries
    # Dealloc from head, add onto tail
    index_type = mk_bits( idx_nbits )
    s.head = Wire( index_type )
    s.tail = Wire( index_type )
    s.num = Wire( mk_bits( idx_nbits + 1 ) )
    s.data = [ Wire( DataType ) for _ in range( num_entries ) ]

    # These are the methods that can be performed
    s.enq = EnqIfcRTL( DataType, index_type )
    s.deq = DeqIfcRTL( DataType )

    s.empty = Wire( Bits1 )

    @s.update
    def set_enq_rdy():
      s.enq.rdy = s.num < num_entries

    @s.update
    def set_deq_rdy():
      s.empty = s.num == 0
      s.deq.rdy = not s.empty

    @s.update_on_edge
    def update_head():
      if s.reset:
        s.head = 0
      else:
        s.head = index_type( s.head + 1 ) if s.deq.en else s.head

    @s.update_on_edge
    def update_tail():
      if s.reset:
        s.tail = 0
      else:
        s.tail = index_type( s.tail + 1 ) if s.enq.en else s.tail

    @s.update_on_edge
    def update_num():
      if s.reset:
        s.num = 0
      elif s.enq.en and not s.deq.en:
        s.num = s.num + 1
      elif not s.enq.en and s.deq.en:
        s.num = s.num - 1
      else:
        s.num = s.num

    @s.update_on_edge
    def handle_data():
      if s.reset:
        for i in range( num_entries ):
          s.data[ i ] = 0

      if s.enq.en:
        s.data[ s.tail ] = s.enq.value

    @s.update
    def handle_deq_value():
      s.deq.value = s.data[ s.head ]

  def line_trace( s ):
    return ":".join([ "{}".format( x ).ljust( 8 ) for x in s.data ] )



#-------------------------------------------------------------------------
# QueueFL
#-------------------------------------------------------------------------

class QueueFL( Component ):

  def construct( s, maxsize ):
    s.q = deque( maxlen=maxsize )

  @guarded_ifc( lambda s: len(s.q) < s.q.maxlen )
  def enq( s, value ):
    s.q.appendleft( value )

  @guarded_ifc( lambda s: len(s.q) > 0 )
  def deq( s ):
    return s.q.pop()




#-------------------------------------------------------------------------
# test_state_machine
#-------------------------------------------------------------------------
def test_state_machine():
  test_stateful = run_test_state_machine(  RTL2CLWrapper( NormalQueueRTL( Bits16, 4 ) ), QueueFL( 4 ) )