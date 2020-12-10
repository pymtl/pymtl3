#=========================================================================
# ReorderQueueHost.py
#=========================================================================
# Credit-based transaction generator.
#
# Author : Peitian Pan
# Date   : Nov 11, 2020

from pymtl3 import *
from pymtl3.stdlib.queues import EnqIfcRTL, DeqIfcRTL

class ReorderQueueHost( Component ):

  def construct( s, MsgType, num_elems, num_reqs ):

    # Sanity check

    ptr_width = clog2( num_elems )
    cnt_width = ptr_width + 1

    addr_width = MsgType.get_field_type('addr').nbits
    data_width = MsgType.get_field_type('data').nbits
    opaque_width = MsgType.get_field_type('opaque').nbits

    assert num_elems == 2**ptr_width, "num_elems has to be a power of 2!"

    # Interfaces

    s.deq = DeqIfcRTL( MsgType )

    s.reorder_q_deq_go = InPort()

    # Credit counter

    s.deq_go = Wire()
    s.deq_go //= lambda: s.deq.en & s.deq.rdy

    s.credit_r = Wire( cnt_width )

    @update_ff
    def reorder_q_host_credit_r():
      if s.reset:
        s.credit_r <<= num_elems
      else:
        if s.deq_go & ~s.reorder_q_deq_go:
          s.credit_r <<= s.credit_r - 1
        if ~s.deq_go & s.reorder_q_deq_go:
          s.credit_r <<= s.credit_r + 1

    # Other counters

    s.packets_left = Wire( 32 )
    s.addr_r = Wire( addr_width )
    s.opaque_r = Wire( opaque_width )

    @update_ff
    def reorder_q_host_counters():
      if s.reset:
        s.packets_left <<= num_reqs
        s.addr_r <<= 0
        s.opaque_r <<= 0
      else:
        if s.deq_go:
          s.packets_left <<= s.packets_left - 1
          s.addr_r <<= s.addr_r + 4
          s.opaque_r <<= s.opaque_r + 1

    # Outward packets

    s.deq.rdy //= lambda: (s.credit_r != 0) & (s.packets_left != 0)

    @update
    def reorder_q_host_packet():
      s.deq.ret.type_  @= 1
      s.deq.ret.addr   @= s.addr_r
      s.deq.ret.data   @= zext( s.addr_r, data_width ) >> 2
      s.deq.ret.opaque @= s.opaque_r
