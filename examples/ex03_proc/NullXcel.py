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
from pymtl3.stdlib.basic_rtl import RegEn
from pymtl3.stdlib.queues import NormalQueueRTL


class NullXcelRTL(Component):

  def construct( s, nbits=32 ):

    dtype = mk_bits(32)
    xreq_class, xresp_class = mk_xcel_msg( 5,nbits )

    s.xcel = XcelMinionIfcRTL( xreq_class, xresp_class )

    s.xcelreq_q = NormalQueueRTL( xreq_class, 2 )
    s.xcelreq_q.enq //= s.xcel.req

    s.xr0 = RegEn( dtype )
    s.xr0.in_ //= s.xcelreq_q.deq.ret.data

    @update
    def up_null_xcel():

      if s.xcelreq_q.deq.rdy & s.xcel.resp.rdy:
        s.xcelreq_q.deq.en @= 1
        s.xcel.resp.en     @= 1
        s.xcel.resp.msg.type_ @= s.xcelreq_q.deq.ret.type_

        if s.xcelreq_q.deq.ret.type_ == XcelMsgType.WRITE:
          s.xr0.en             @= 1
          s.xcel.resp.msg.data @= 0
        else:
          s.xr0.en             @= 0
          s.xcel.resp.msg.data @= s.xr0.out
      else:
        s.xcelreq_q.deq.en    @= 0
        s.xcel.resp.en        @= 0
        s.xr0.en              @= 0
        s.xcel.resp.msg.data  @= 0
        s.xcel.resp.msg.type_ @= 0

  def line_trace( s ):
    return str(s.xcel)
