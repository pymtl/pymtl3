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
from pymtl3.stdlib.xcel import XcelMsgType, mk_xcel_msg
from pymtl3.stdlib.xcel.ifcs import XcelResponderIfc
from pymtl3.stdlib.stream import StreamNormalQueue
from pymtl3.stdlib.primitive import Reg


# TODO: add more comments.
class ChecksumXcelRTL( Component ):
  def construct( s ):
    # Interface

    ReqType, RespType = mk_xcel_msg( 5, 32 )
    s.xcel = XcelResponderIfc( ReqType, RespType )

    # State encoding

    s.XCFG = b2(0)
    s.WAIT = b2(1)
    s.BUSY = b2(2)

    # Components

    s.in_q = StreamNormalQueue( ReqType, num_entries=2 )
    s.reg_file = [ Reg( Bits32 ) for _ in range(6) ]
    s.checksum_unit = ChecksumRTL()

    s.state       = Wire( Bits2 )
    s.state_next  = Wire( Bits2 )
    s.start_pulse = Wire( Bits1 )


    # Connections

    s.xcel.reqstream //= s.in_q.istream
    s.checksum_unit.istream.msg[0 :32 ] //= s.reg_file[0].out
    s.checksum_unit.istream.msg[32:64 ] //= s.reg_file[1].out
    s.checksum_unit.istream.msg[64:96 ] //= s.reg_file[2].out
    s.checksum_unit.istream.msg[96:128] //= s.reg_file[3].out

    # Logic

    @update
    def up_start_pulse():
      s.start_pulse @=   (s.xcel.respstream.val & s.xcel.respstream.rdy) & \
                       ( s.in_q.ostream.msg.type_ == XcelMsgType.WRITE ) & \
                       ( s.in_q.ostream.msg.addr == 4 )

    @update
    def up_state_next():
      if s.state == s.XCFG:
        s.state_next @= (
          s.WAIT if s.start_pulse & ~s.checksum_unit.istream.rdy else
          s.BUSY if s.start_pulse &  s.checksum_unit.istream.rdy else
          s.XCFG
        )

      elif s.state == s.WAIT:
        s.state_next @= s.BUSY if s.checksum_unit.istream.rdy else s.WAIT

      else: # s.state == s.BUSY
        s.state_next @= s.XCFG if s.checksum_unit.ostream.val else s.BUSY

    @update_ff
    def up_state():
      if s.reset:
        s.state <<= s.XCFG
      else:
        s.state <<= s.state_next

    @update
    def up_fsm_output():
      if s.state == s.XCFG:
        s.in_q.ostream.rdy @= s.in_q.ostream.val
        s.xcel.respstream.val @= s.in_q.ostream.val
        s.checksum_unit.istream.val @= s.start_pulse & s.checksum_unit.istream.rdy
        s.checksum_unit.ostream.rdy @= 1

      elif s.state == s.WAIT:
        s.in_q.ostream.rdy @= 0
        s.xcel.respstream.val @= 0
        s.checksum_unit.istream.val @= s.checksum_unit.istream.rdy
        s.checksum_unit.ostream.rdy @= 1

      else: # s.state == s.BUSY:
        s.in_q.ostream.rdy  @= 0
        s.xcel.respstream.val @= 0
        s.checksum_unit.istream.val @= 0
        s.checksum_unit.ostream.rdy @= 1

    @update
    def up_resp_msg():
      s.xcel.respstream.msg.type_ @= s.in_q.ostream.msg.type_
      s.xcel.respstream.msg.data  @= 0
      if s.in_q.ostream.msg.type_ == XcelMsgType.READ:
        s.xcel.respstream.msg.data @= s.reg_file[ s.in_q.ostream.msg.addr[0:3] ].out

    @update
    def up_wr_regfile():
      for i in range(6):
        s.reg_file[i].in_ @= s.reg_file[i].out

      if s.in_q.ostream.val & (s.in_q.ostream.msg.type_ == XcelMsgType.WRITE):
        for i in range(6):
          s.reg_file[i].in_ @= (
            s.in_q.ostream.msg.data if b5(i) == s.in_q.ostream.msg.addr else
            s.reg_file[i].out
          )

      if s.checksum_unit.ostream.val:
        s.reg_file[5].in_ @= s.checksum_unit.ostream.msg

  def line_trace( s ):
    state_str = (
      "XCFG" if s.state == s.XCFG else
      "WAIT" if s.state == s.WAIT else
      "BUSY" if s.state == s.BUSY else
      "XXXX"
    )
    return "{}(RTL:{}){}".format( s.xcel.reqstream, state_str, s.xcel.respstream )
