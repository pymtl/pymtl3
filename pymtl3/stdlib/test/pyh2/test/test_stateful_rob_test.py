#=========================================================================
# test_stateful_rob_test
#=========================================================================
# Tests for test_stateful using a reorder buffer
#
# Author: Yixiao Zhang
#   Date: May 1, 2019


from pymtl3 import *
from ..RTL2CLWrapper import RTL2CLWrapper

from ..pyh2s import run_pyh2s


#-------------------------------------------------------------------------
# ReorderBufferCL
#-------------------------------------------------------------------------
class ReorderBufferCL( Component ):

  def construct( s, num_entries ):
    # We want to be a power of two so mod arithmetic is efficient
    idx_nbits = clog2( num_entries )
    assert 2**idx_nbits == num_entries
    s.num_entries = num_entries

    s.data = [ None ] * s.num_entries
    s.allocated = [ 0 ] * s.num_entries

    s.head = 0
    s.num = 0
    s.next_slot = 0

    s.add_constraints(
        M( s.update_entry ) < M( s.remove ),
        M( s.remove ) < M( s.alloc ) )

  @non_blocking( lambda s: s.num < s.num_entries )
  def alloc( s ):
    index = s.next_slot
    s.allocated[ s.next_slot ] = True
    s.num += 1
    s.next_slot = ( s.next_slot + 1 ) % s.num_entries
    return index

  @non_blocking( lambda s: not s.empty() )
  def update_entry( s, index, value ):
    assert index >= 0 and index < s.num_entries
    if s.allocated[ index ]:
      s.data[ index ] = value

  # testing returning multiple fields
  @non_blocking( lambda s: s.data[ s.head ] != None )
  def remove( s ):
    head = s.head
    data = s.data[ s.head ]
    s.data[ s.head ] = None
    s.allocated[ s.head ] = False
    s.head = ( s.head + 1 ) % s.num_entries
    s.num -= 1
    return head, data

  def empty( s ):
    return s.num == 0

  def line_trace( s ):
    return f"[{''.join( ['+' if x else ' ' for x in s.allocated ] )}]"

#-------------------------------------------------------------------------
# ReorderBuffer
#-------------------------------------------------------------------------

class ReorderBuffer( Component ):

  # This stores (key, value) pairs in a finite size FIFO queue

  def construct( s, DataType, num_entries ):

    # We want to be a power of two so mod arithmetic is efficient

    idx_nbits = clog2( num_entries )
    assert 2**idx_nbits == num_entries

    IndexType = mk_bits( idx_nbits )
    CapType   = mk_bits( idx_nbits+1 )

    ROBMsgType = mk_bitstruct( 'ROBMsg', {
      'index': IndexType,
      'value': DataType,
    })

    # These are the methods that can be performed
    # This order has to be consistent with CL

    s.alloc        = CalleeIfcRTL( en=True, rdy=True, RetType=IndexType )
    s.update_entry = CalleeIfcRTL( en=True, rdy=True, MsgType=ROBMsgType )
    s.remove       = CalleeIfcRTL( en=True, rdy=True, RetType=ROBMsgType )

    # Dealloc from head, add onto tail
    s.head = Wire( IndexType )
    s.tail = Wire( IndexType )
    s.size = Wire( CapType )

    s.data      = [ Wire( DataType ) for _ in range( num_entries ) ]
    s.valid     = [ Wire( Bits1 ) for _ in range( num_entries ) ]
    s.allocated = [ Wire( Bits1 ) for _ in range( num_entries ) ]

    @s.update
    def update_rdy():
      s.alloc.rdy        = s.size < num_entries or s.remove.en
      s.update_entry.rdy = (s.size != 0)
      s.remove.rdy       = s.valid[ s.head ] or (s.update_entry.en and s.update_entry.msg.index == s.head)

    @s.update
    def update_ret_alloc():
      s.alloc.ret = s.tail

    @s.update
    def update_en():
      if s.update_entry.en and s.update_entry.msg.index == s.head:
        s.remove.ret.value = s.update_entry.msg.value
      else:
        s.remove.ret.value = s.data[ s.head ]
      s.remove.ret.index = s.head

    @s.update_ff
    def up_pointers():
      if s.reset:
        s.size <<= CapType( 0 )
        s.head <<= IndexType(0)
        s.tail <<= IndexType(0)

      elif s.alloc.en:
        s.tail <<= s.tail + IndexType( 1 )
        if s.remove.en:
          s.head <<= s.head + 1
        else:
          s.size <<= s.size + 1

      elif s.remove.en: # alloc.en == False
        s.head <<= s.head + 1
        s.size <<= s.size - 1

    @s.update_ff
    def handle_data_and_flags():
      if s.reset:
        for i in range( num_entries ):
          s.data[ i ] <<= DataType(0)

      # Handle update
      if s.update_entry.en:
        if s.allocated[ s.update_entry.msg ]:
          s.data[ s.update_entry.msg.index ] <<= s.update_entry.msg.value
          s.valid[ s.update_entry.msg.index ] <<= 1

      if s.remove.en:
        s.valid[ s.head ] <<= IndexType(0)
        s.allocated[ s.head ] <<= IndexType(0)

      if s.alloc.en:
        s.allocated[ s.tail ] <<= IndexType(1)

  def line_trace( s ):
    return ":".join([
        "{}".format( s.data[ i ] if s.valid[ i ] else "......" if s
                     .allocated[ i ] else "-" ).ljust( 8 )
        for i in range( len( s.data ) )
    ] )


#-------------------------------------------------------------------------
# test_state_machine
#-------------------------------------------------------------------------
def test_state_machine():
  test = run_pyh2s( ReorderBuffer( Bits16, 4 ), ReorderBufferCL( 4 ) )
