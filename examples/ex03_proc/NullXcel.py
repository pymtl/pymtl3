"""
==========================================================================
NullXcel.py
==========================================================================

Author : Shunning Jiang
  Date : June 14, 2019
"""
from pymtl3 import *
from pymtl3.stdlib.ifcs.xcel_ifcs import XcelMinionIfcRTL
from pymtl3.stdlib.ifcs.XcelMsg import XcelMsgType, mk_xcel_msg
from pymtl3.stdlib.rtl import RegEn
from pymtl3.stdlib.rtl.queues import NormalQueueRTL


class NullXcelRTL(Component):

  def construct( s, nbits=32 ):

    dtype = mk_bits(32)
    XcelMsgType_WRITE = XcelMsgType.WRITE
    xreq_class, xresp_class = mk_xcel_msg( 5,nbits )

    s.xcel = XcelMinionIfcRTL( xreq_class, xresp_class )

    s.xcelreq_q = NormalQueueRTL( xreq_class, 2 )( enq = s.xcel.req )

    s.xr0 = RegEn( dtype )( in_ = s.xcelreq_q.deq.msg.data )

    @s.update
    def up_null_xcel():

      if s.xcelreq_q.deq.rdy & s.xcel.resp.rdy:
        s.xcelreq_q.deq.en = b1(1)
        s.xcel.resp.en     = b1(1)
        s.xcel.resp.msg.type_ = s.xcelreq_q.deq.msg.type_

        if s.xcelreq_q.deq.msg.type_ == XcelMsgType_WRITE:
          s.xr0.en             = b1(1)
          s.xcel.resp.msg.data = dtype(0)
        else:
          s.xr0.en            = b1(0)
          s.xcel.resp.msg.data = s.xr0.out
      else:
        s.xcelreq_q.deq.en   = b1(0)
        s.xcel.resp.en       = b1(0)
        s.xr0.en             = b1(0)
        s.xcel.resp.msg.data = dtype(0)
        s.xcel.resp.msg.type_ = b1(0)

  def line_trace( s ):
    return str(s.xcel)
