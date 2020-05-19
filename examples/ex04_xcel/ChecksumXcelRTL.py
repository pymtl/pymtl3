"""
==========================================================================
ChecksumXcelRTL.py
==========================================================================
Register transfer level implementation of a checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
from examples.ex02_cksum.ChecksumRTL import ChecksumRTL
from pymtl3 import *
from pymtl3.stdlib.ifcs import XcelMsgType, mk_xcel_msg, XcelMinionIfcRTL
from pymtl3.stdlib.queues import NormalQueueRTL
from pymtl3.stdlib.basic_rtl import Reg


# TODO: add more comments.
class ChecksumXcelRTL( Component ):
  def construct( s ):
    # Interface

    ReqType, RespType = mk_xcel_msg( 5, 32 )
    s.xcel = XcelMinionIfcRTL( ReqType, RespType )

    # State encoding

    s.XCFG = b2(0)
    s.WAIT = b2(1)
    s.BUSY = b2(2)

    # Components

    s.in_q = NormalQueueRTL( ReqType, num_entries=2 )
    s.reg_file = [ Reg( Bits32 ) for _ in range(6) ]
    s.checksum_unit = ChecksumRTL()

    s.state       = Wire( Bits2 )
    s.state_next  = Wire( Bits2 )
    s.start_pulse = Wire( Bits1 )


    # Connections

    s.xcel.req //= s.in_q.enq
    s.checksum_unit.recv.msg[0 :32 ] //= s.reg_file[0].out
    s.checksum_unit.recv.msg[32:64 ] //= s.reg_file[1].out
    s.checksum_unit.recv.msg[64:96 ] //= s.reg_file[2].out
    s.checksum_unit.recv.msg[96:128] //= s.reg_file[3].out

    # Logic

    @update
    def up_start_pulse():
      s.start_pulse @=   s.xcel.resp.en & \
                       ( s.in_q.deq.ret.type_ == XcelMsgType.WRITE ) & \
                       ( s.in_q.deq.ret.addr == 4 )

    @update
    def up_state_next():
      if s.state == s.XCFG:
        s.state_next @= (
          s.WAIT if s.start_pulse & ~s.checksum_unit.recv.rdy else
          s.BUSY if s.start_pulse &  s.checksum_unit.recv.rdy else
          s.XCFG
        )

      elif s.state == s.WAIT:
        s.state_next @= s.BUSY if s.checksum_unit.recv.rdy else s.WAIT

      else: # s.state == s.BUSY
        s.state_next @= s.XCFG if s.checksum_unit.send.en else s.BUSY

    @update_ff
    def up_state():
      if s.reset:
        s.state <<= s.XCFG
      else:
        s.state <<= s.state_next

    @update
    def up_fsm_output():
      if s.state == s.XCFG:
        s.in_q.deq.en  @= s.in_q.deq.rdy
        s.xcel.resp.en @= s.in_q.deq.rdy
        s.checksum_unit.recv.en  @= s.start_pulse & s.checksum_unit.recv.rdy
        s.checksum_unit.send.rdy @= 1

      elif s.state == s.WAIT:
        s.in_q.deq.en  @= 0
        s.xcel.resp.en @= 0
        s.checksum_unit.recv.en  @= s.checksum_unit.recv.rdy
        s.checksum_unit.send.rdy @= 1

      else: # s.state == s.BUSY:
        s.in_q.deq.en  @= 0
        s.xcel.resp.en @= 0
        s.checksum_unit.recv.en  @= 0
        s.checksum_unit.send.rdy @= 1

    @update
    def up_resp_msg():
      s.xcel.resp.msg.type_ @= s.in_q.deq.ret.type_
      s.xcel.resp.msg.data  @= 0
      if s.in_q.deq.ret.type_ == XcelMsgType.READ:
        s.xcel.resp.msg.data @= s.reg_file[ s.in_q.deq.ret.addr[0:3] ].out

    @update
    def up_wr_regfile():
      for i in range(6):
        s.reg_file[i].in_ @= s.reg_file[i].out

      if s.in_q.deq.en & (s.in_q.deq.ret.type_ == XcelMsgType.WRITE):
        for i in range(6):
          s.reg_file[i].in_ @= (
            s.in_q.deq.ret.data if b5(i) == s.in_q.deq.ret.addr else
            s.reg_file[i].out
          )

      if s.checksum_unit.send.en:
        s.reg_file[5].in_ @= s.checksum_unit.send.msg

  def line_trace( s ):
    state_str = (
      "XCFG" if s.state == s.XCFG else
      "WAIT" if s.state == s.WAIT else
      "BUSY" if s.state == s.BUSY else
      "XXXX"
    )
    return "{}(RTL:{}){}".format( s.xcel.req, state_str, s.xcel.resp )
