"""
==========================================================================
NullXcel.py
==========================================================================

Author : Shunning Jiang
  Date : June 14, 2019
"""
from pymtl3 import *
from pymtl3.stdlib.xcel import XcelMsgType, mk_xcel_msg
from pymtl3.stdlib.xcel.ifcs import XcelResponderIfc
from pymtl3.stdlib.primitive import RegEn
from pymtl3.stdlib.stream import StreamNormalQueue


class NullXcelRTL(Component):

  def construct( s, nbits=32 ):

    dtype = mk_bits(32)
    xreq_class, xresp_class = mk_xcel_msg( 5,nbits )

    s.xcel = XcelResponderIfc( xreq_class, xresp_class )

    s.xcelreq_q = StreamNormalQueue( xreq_class, 2 )
    s.xcelreq_q.istream //= s.xcel.reqstream

    s.xr0 = RegEn( dtype )
    s.xr0.in_ //= s.xcelreq_q.ostream.msg.data

    @update
    def up_null_xcel():

      if s.xcelreq_q.ostream.val & s.xcel.respstream.rdy:
        s.xcelreq_q.ostream.rdy     @= 1
        s.xcel.respstream.val       @= 1
        s.xcel.respstream.msg.type_ @= s.xcelreq_q.ostream.msg.type_

        if s.xcelreq_q.ostream.msg.type_ == XcelMsgType.WRITE:
          s.xr0.en                   @= 1
          s.xcel.respstream.msg.data @= 0
        else:
          s.xr0.en                   @= 0
          s.xcel.respstream.msg.data @= s.xr0.out
      else:
        s.xcelreq_q.ostream.rdy     @= 0
        s.xcel.respstream.val       @= 0
        s.xr0.en                    @= 0
        s.xcel.respstream.msg.data  @= 0
        s.xcel.respstream.msg.type_ @= 0

  def line_trace( s ):
    return str(s.xcel)
