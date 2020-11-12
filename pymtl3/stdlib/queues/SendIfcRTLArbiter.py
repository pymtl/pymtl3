#=========================================================================
# SendIfcRTLArbiter.py
#=========================================================================
# N-to-1 arbiter for SendIfcRTL. Internally all input packets are buffered
# before performing arbitration.
#
# Author : Peitian Pan
# Date   : Nov 12, 2020

from pymtl3 import *
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.basic_rtl import RoundRobinArbiterEn, Encoder
from pymtl3.stdlib.queues.valrdy_queues import NormalQueueRTL

class SendIfcRTLArbiter( Component ):

  def construct( s, MsgType, ninputs ):

    ninputs_width = clog2(ninputs)

    # Interfaces

    s.recv = [ RecvIfcRTL( MsgType ) for _ in range(ninputs) ]
    s.send = SendIfcRTL( MsgType )

    # Buffer

    s.buf = [ NormalQueueRTL( 2, MsgType ) for _ in range(ninputs) ]

    for i in range(ninputs):
      s.buf[i].enq.val //= s.recv[i].en
      s.buf[i].enq.rdy //= s.recv[i].rdy
      s.buf[i].enq.msg //= s.recv[i].msg

    # Arbiter

    s.arb = RoundRobinArbiterEn( ninputs )

    s.arb.en //= s.send.rdy

    for i in range(ninputs):
      s.arb.reqs[i] //= s.buf[i].deq.val
      s.arb.grants[i] //= s.buf[i].deq.rdy

    # Grant index

    s.grant_idx = Wire( ninputs_width )

    s.encoder = Encoder( ninputs, ninputs_width )
    s.encoder.in_ //= s.arb.grants
    s.encoder.out //= s.grant_idx

    # Output

    @update
    def send_ifc_arb_out():
      s.send.en @= s.arb.grants != 0
      s.send.msg @= s.buf[s.grant_idx].deq.msg

  def line_trace( s ):
    recv_trace = "|".join( str(x) for x in s.recv )
    return f"{recv_trace} > {s.send}"
