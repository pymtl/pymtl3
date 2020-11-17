#=========================================================================
# ReorderQueue.py
#=========================================================================
# Reorder out-of-order enq messages based on the opaque field, and only
# allows in-order dequeue.
#
# Author : Peitian Pan
# Date   : Nov 11, 2020

from pymtl3 import *
from pymtl3.stdlib.basic_rtl import RegisterFile
from pymtl3.stdlib.queues import EnqIfcRTL, DeqIfcRTL
from pymtl3.stdlib.connects import connect_pairs

#=========================================================================
# Control unit
#=========================================================================

class ReorderQueueCtrl( Component ):

  def construct( s, num_elems ):

    # Sanity check

    ptr_width = clog2( num_elems )

    assert num_elems == 2**ptr_width, "num_elems has to be a power of 2!"

    # Interfaces

    s.enq_en  = InPort()
    s.enq_rdy = OutPort()

    s.deq_en  = InPort()
    s.deq_rdy = OutPort()

    s.enq_go = OutPort()

    s.deq_ptr = OutPort( ptr_width )
    s.enq_ptr = InPort( ptr_width )

    # Dequeue pointer

    @update_ff
    def reorder_q_deq_ptr_r():
      if s.reset:
        s.deq_ptr <<= 0
      else:
        if s.deq_rdy & s.deq_en:
          s.deq_ptr <<= s.deq_ptr + 1

    # Valid bits

    s.buf_valid_r = Wire( num_elems )
    s.buf_valid_n = Wire( num_elems )

    @update_ff
    def reorder_q_buf_valid_r():
      if s.reset:
        s.buf_valid_r <<= 0
      else:
        s.buf_valid_r <<= s.buf_valid_n

    @update
    def reorder_q_buf_valid_n():
      s.buf_valid_n @= s.buf_valid_r
      if s.deq_en & s.deq_rdy:
        s.buf_valid_n[s.deq_ptr] @= 0
      if s.enq_en & s.enq_rdy:
        s.buf_valid_n[s.enq_ptr] @= 1

    # Control signals

    s.enq_rdy //= lambda: reduce_or( ~s.buf_valid_r )
    s.deq_rdy //= lambda: s.buf_valid_r[s.deq_ptr]
    s.enq_go  //= lambda: s.enq_en & s.enq_rdy

  def line_trace( s ):
    return f"ENQ@{s.enq_ptr}:{s.buf_valid_r.bin()}:DEQ@{s.deq_ptr}"

#=========================================================================
# Data path
#=========================================================================

class ReorderQueueDpath( Component ):

  def construct( s, MsgType, num_elems, field ):

    # Sanity check

    ptr_width = clog2( num_elems )

    assert num_elems == 2**ptr_width, "num_elems has to be a power of 2!"

    # Interfaces

    s.enq_msg = InPort( MsgType )
    s.deq_msg = OutPort( MsgType )

    s.enq_go = InPort()
    s.deq_ptr = InPort( ptr_width )
    s.enq_ptr = OutPort( ptr_width )

    # Components

    s.buf = RegisterFile( MsgType, num_elems )

    # Connections

    if field == 'opaque':
      @update
      def reorder_q_dpath_opaque():
        s.enq_ptr @= s.enq_msg.opaque[0:ptr_width]
    elif field == 'reg_id':
      @update
      def reorder_q_dpath_reg_id():
        s.enq_ptr @= s.enq_msg.reg_id[0:ptr_width]
    else:
      raise ValueError

    s.buf.raddr[0] //= s.deq_ptr
    s.buf.rdata[0] //= s.deq_msg
    s.buf.wen[0]   //= s.enq_go
    s.buf.waddr[0] //= s.enq_ptr
    s.buf.wdata[0] //= s.enq_msg

#=========================================================================
# Main reorder queue
#=========================================================================

class ReorderQueue( Component ):

  def construct( s, MsgType, num_elems=32, field='opaque' ):

    assert field in ['opaque', 'reg_id']

    # Interfaces

    s.enq = EnqIfcRTL( MsgType )
    s.deq = DeqIfcRTL( MsgType )

    # Components

    s.ctrl  = ReorderQueueCtrl( num_elems )
    s.dpath = ReorderQueueDpath( MsgType, num_elems, field )

    # Connections

    connect_pairs(
        s.enq.en,       s.ctrl.enq_en,
        s.enq.rdy,      s.ctrl.enq_rdy,
        s.enq.msg,      s.dpath.enq_msg,
        s.deq.en,       s.ctrl.deq_en,
        s.deq.rdy,      s.ctrl.deq_rdy,
        s.deq.ret,      s.dpath.deq_msg,

        s.ctrl.enq_go,  s.dpath.enq_go,
        s.ctrl.deq_ptr, s.dpath.deq_ptr,
        s.ctrl.enq_ptr, s.dpath.enq_ptr,
    )

  def line_trace( s ):
    return f"{s.enq}|({s.ctrl.line_trace()})|{s.deq}"
