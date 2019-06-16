"""
==========================================================================
ChecksumXcelRTL.py
==========================================================================
Register transfer level implementation of a checksum accelerator.

Author : Yanghui Ou
  Date : June 14, 2019
"""
from __future__ import absolute_import, division, print_function

from pymtl3 import *
from pymtl3.stdlib.ifcs import mk_xcel_msg, XcelMsgType
from pymtl3.stdlib.ifcs.xcel_ifcs import XcelMinionIfcRTL
from pymtl3.stdlib.rtl.queues import NormalQueueRTL
from pymtl3.stdlib.rtl.registers import Reg

from examples.ex02_cksum.ChecksumRTL import ChecksumRTL


class ChecksumXcelRTL( Component ):
  def construct( s ):
    
    # Interface

    ReqType, RespType = mk_xcel_msg( 5, 32 )
    s.xcel = XcelMinionIfcRTL( ReqType, RespType )

    # State encoding

    s.XCFG = b2(0) 
    s.WAIT = b2(1)
    s.BUSY = b2(2)

    # Local parameters

    RD = XcelMsgType.READ
    WR = XcelMsgType.WRITE

    # Components

    s.in_q = NormalQueueRTL( ReqType, num_entries=2 )
    s.reg_file = [ Reg( Bits32 ) for _ in range(6) ]
    s.checksum_unit = ChecksumRTL()
    
    s.state       = Wire( Bits2 )
    s.state_next  = Wire( Bits2 )
    s.start_pulse = Wire( Bits1 )
    
    
    # Connections

    s.connect( s.xcel.req, s.in_q.enq )
    s.connect( s.checksum_unit.recv.msg[0 :32 ], s.reg_file[0].out )
    s.connect( s.checksum_unit.recv.msg[32:64 ], s.reg_file[1].out )
    s.connect( s.checksum_unit.recv.msg[64:96 ], s.reg_file[2].out )
    s.connect( s.checksum_unit.recv.msg[96:128], s.reg_file[3].out )

    # Logic

    @s.update
    def up_start_pulse():
      s.start_pulse = (
        s.xcel.resp.en and 
        s.in_q.deq.msg.type_ == WR and 
        s.in_q.deq.msg.addr == b5(4) 
      )

    @s.update
    def up_state_next():
      if s.state == s.XCFG:
        s.state_next = (
          s.WAIT if s.start_pulse & ~s.checksum_unit.recv.rdy else
          s.BUSY if s.start_pulse &  s.checksum_unit.recv.rdy else
          s.XCFG 
        )

      elif s.state == s.WAIT:
        s.state_next = s.BUSY if s.checksum_unit.recv.rdy else s.WAIT

      else: # s.state == s.BUSY
        s.state_next = s.XCFG if s.checksum_unit.send.en else s.BUSY

    @s.update_on_edge
    def up_state():
      if s.reset:
        s.state = s.XCFG
      else:
        s.state = s.state_next
  
    @s.update
    def up_fsm_output():
      if s.state == s.XCFG:
        s.in_q.deq.en  = s.in_q.deq.rdy
        s.xcel.resp.en = s.in_q.deq.rdy
        s.checksum_unit.recv.en  = s.start_pulse & s.checksum_unit.recv.rdy
        s.checksum_unit.send.rdy = b1(1)

      elif s.state == s.WAIT:
        s.in_q.deq.en  = b1(0)
        s.xcel.resp.en = b1(0)
        s.checksum_unit.recv.en  = s.checksum_unit.recv.rdy
        s.checksum_unit.send.rdy = b1(1)

      elif s.state == s.BUSY:
        s.in_q.deq.en = b1(0)
        s.xcel.resp.en = b1(0)
        s.checksum_unit.recv.en  = b1(0)
        s.checksum_unit.send.rdy = b1(1)

    @s.update
    def up_resp_msg():
      s.xcel.resp.msg.type_ = s.in_q.deq.msg.type_
      s.xcel.resp.msg.data  = b32(0) 
      if s.in_q.deq.msg.type_ == RD: 
        s.xcel.resp.msg.data = s.reg_file[ s.in_q.deq.msg.addr ].out

    @s.update
    def up_wr_regfile():
      if s.in_q.deq.en and s.in_q.deq.msg.type_ == WR:
        for i in range(6):
          s.reg_file[i].in_ = (
            s.in_q.deq.msg.data if b5(i) == s.in_q.deq.msg.addr else
            s.reg_file[i].out
          )

      if s.checksum_unit.send.en:
        s.reg_file[5].in_ = s.checksum_unit.send.msg

  def line_trace( s ):
    state_str = (
      "XCFG" if s.state == s.XCFG else
      "WAIT" if s.state == s.WAIT else
      "BUSY" if s.state == s.BUSY else
      "XXXX"
    )
    return "{}({}){}".format( s.xcel.req, state_str, s.xcel.resp )
