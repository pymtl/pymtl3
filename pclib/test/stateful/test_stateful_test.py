#=========================================================================
# Tests for test_stateful using the reorder buffer
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

#-------------------------------------------------------------------------
# ReorderBufferCL
#-------------------------------------------------------------------------


class ReorderBufferCL( Component ):

  def construct( s, DataType, num_entries ):
    # We want to be a power of two so mod arithmetic is efficient
    idx_nbits = clog2( num_entries )
    assert 2**idx_nbits == num_entries
    s.num_entries = num_entries
    s.data = [ 0 ] * s.num_entries

    s.head = 0
    s.num = 0
    s.next_slot = 0

  @guarded_ifc( lambda s: s.num < s.num_entries )
  def alloc( s, value ):
    index = s.next_slot
    s.data[ index ] = value
    s.num += 1
    s.next_slot = ( s.next_slot + 1 ) % s.num_entries
    return index

  @guarded_ifc( lambda s: not s.empty() )
  def update_entry( s, index, value ):
    assert index >= 0 and index < s.num_entries
    s.data[ index ] = value

  @guarded_ifc( lambda s: not s.empty() )
  def remove( s ):
    head = s.head
    s.head = ( s.head + 1 ) % s.num_entries
    s.num -= 1
    return s.data[ head ]

  def empty( s ):
    return s.num == 0


#-------------------------------------------------------------------------
# clog2
#-------------------------------------------------------------------------


def clog2( num ):
  return int( math.ceil( math.log( num, 2 ) ) )


#-------------------------------------------------------------------------
# AllocIfcRTL
#-------------------------------------------------------------------------


class AllocIfcRTL( Interface ):

  def construct( s, Type, IndexType ):

    s.value = InPort( Type )
    s.index = OutPort( IndexType )
    s.en = InPort( int if Type is int else Bits1 )
    s.rdy = OutPort( int if Type is int else Bits1 )

  def line_trace( s ):
    return ""

  def __str__( s ):
    return s.line_trace()


#-------------------------------------------------------------------------
# UpdateIfcRTL
#-------------------------------------------------------------------------


class UpdateIfcRTL( Interface ):

  def construct( s, Type, IndexType ):

    s.value = InPort( Type )
    s.index = InPort( IndexType )
    s.en = InPort( int if Type is int else Bits1 )
    s.rdy = OutPort( int if Type is int else Bits1 )


#-------------------------------------------------------------------------
# RemoveIfcRTL
#-------------------------------------------------------------------------


class RemoveIfcRTL( Interface ):

  def construct( s, Type ):

    s.value = OutPort( Type )
    s.en = InPort( int if Type is int else Bits1 )
    s.rdy = OutPort( int if Type is int else Bits1 )


#-------------------------------------------------------------------------
# ReorderBuffer
#-------------------------------------------------------------------------


class ReorderBuffer( Component ):
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
    s.alloc = AllocIfcRTL( DataType, index_type )
    s.update_entry = UpdateIfcRTL( DataType, index_type )
    s.remove = RemoveIfcRTL( DataType )

    s.empty = Wire( Bits1 )

    @s.update
    def set_alloc_rdy():
      s.alloc.rdy = s.num < num_entries or s.remove.en  # Alloc rdy

    @s.update
    def set_update_entry_rdy():
      s.empty = s.num == 0
      s.update_entry.rdy = not s.empty
      s.remove.rdy = not s.empty

    @s.update_on_edge
    def update_head():
      if s.reset:
        s.head = 0
      else:
        s.head = index_type( s.head ) if s.remove.en else s.head

    @s.update_on_edge
    def update_tail():
      if s.reset:
        s.tail = 0
      else:
        s.tail = index_type( s.tail + 1 ) if s.alloc.en else s.tail

    @s.update
    def update_alloc():
      s.alloc.index = s.tail

    @s.update_on_edge
    def update_num():
      if s.reset:
        s.num = 0
      elif s.alloc.en and not s.remove.en:
        s.num = s.num + 1
      elif not s.alloc.en and s.remove.en:
        s.num = s.num - 1
      else:
        s.num = s.num

    @s.update_on_edge
    def handle_en():
      if s.reset:
        for i in range( num_entries ):
          s.data[ i ] = 0

      # Handle update
      if s.update_entry.en:
        s.data[ s.update_entry.index ] = s.update_entry.value

      if s.alloc.en:
        s.data[ s.tail ] = 1
        s.data[ s.tail ] = s.alloc.value

    @s.update
    def handle_remove_value():
      s.remove.value = s.data[ s.head ]

  def line_trace( s ):
    return ":".join([ "{}".format( x ).ljust( 8 ) for x in s.data ] )


#-------------------------------------------------------------------------
# test_state_machine
#-------------------------------------------------------------------------
def test_state_machine():
  test = run_test_state_machine(
      RTL2CLWrapper( ReorderBuffer( Bits16, 4 ) ), ReorderBufferCL( Bits16,
                                                                    4 ) )
