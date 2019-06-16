"""
==========================================================================
ChecksumXcelCL.py
==========================================================================
Cycle level implementation of a checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.stdlib.cl.queues import BypassQueueCL
from pymtl3.stdlib.ifcs import mk_xcel_msg, XcelMsgType
from pymtl3.stdlib.ifcs.xcel_ifcs import XcelMinionIfcCL

from examples.ex02_cksum.ChecksumCL import ChecksumCL
from examples.ex02_cksum.ChecksumRTL import ChecksumRTL
from examples.ex02_cksum.utils import words_to_b128


class ChecksumXcelCL( Component ):

  def construct( s ):

    # Interface

    ReqType, RespType = mk_xcel_msg( 3, 32 )
    s.xcel = XcelMinionIfcCL( ReqType, RespType, s.req, s.req_rdy )

    s.RespType = RespType

    # Components

    s.reg_file = [ b32(0) for _ in range(6) ]
    s.busy = False
    s.resp_msg = None

    s.checksum_unit = ChecksumCL()
    
    # TODO: replace out_q with a combinational adapter
    s.out_q = BypassQueueCL( num_entries=1 )
    s.connect( s.checksum_unit.send, s.out_q.enq )

    @s.update
    def up_start():
      if s.reg_file[4]:
        s.busy = True
        s.reg_file[4] = b32(0)

        words = []
        for i in range( 4 ):
          words.append( s.reg_file[i][0 :16] )
          words.append( s.reg_file[i][16:32] )

        s.checksum_unit.recv( words_to_b128( words ) )

    @s.update
    def up_resp():
      if s.resp_msg is not None and s.xcel.resp.rdy(): 
        s.xcel.resp( s.resp_msg )
        s.resp_msg = None

      if s.out_q.deq.rdy():
        s.reg_file[5] = s.out_q.deq()
        s.busy = False

    s.add_constraints( U( up_start ) < M( s.xcel.req     ) )
    s.add_constraints( U( up_resp  ) > M( s.xcel.req.rdy ) )

  def req( s, msg ):
    if msg.type_ == XcelMsgType.READ:
      s.resp_msg = s.RespType( XcelMsgType.READ, s.reg_file[ int(msg.addr) ] )

    elif msg.type_ == XcelMsgType.WRITE:
      s.reg_file[ int(msg.addr) ] = msg.data
      s.resp_msg = s.RespType( XcelMsgType.WRITE, 0 )

  def req_rdy( s ):
    return not s.busy 

  def line_trace( s ):
    return "{}({}){}".format( s.xcel.req, '#' if s.busy else ' ', s.xcel.resp )
