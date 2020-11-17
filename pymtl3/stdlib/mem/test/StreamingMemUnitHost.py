#=========================================================================
# StreamingMemUnitHost.py
#=========================================================================
# Author : Peitian Pan
# Date   : Nov 10, 2020

from pymtl3 import *
from pymtl3.stdlib.ifcs import mk_xcel_msg, XcelMasterIfcRTL

# Registers
GO              = 0
STATUS          = 1
PADDING         = 2
SRC_BASE_ADDR   = 3
SRC_X_STRIDE    = 4
SRC_X_COUNT     = 5
SRC_Y_STRIDE    = 6
SRC_Y_COUNT     = 7
DST_BASE_ADDR   = 8
DST_ACK_ADDR    = 9
NUM_REGISTERS   = 10

# SMU host states
IDLE             = 0
WR_PADDING       = 1
WR_SRC_BASE_ADDR = 2
WR_SRC_X_STRIDE  = 3
WR_SRC_X_COUNT   = 4
WR_SRC_Y_STRIDE  = 5
WR_SRC_Y_COUNT   = 6
WR_DST_BASE_ADDR = 7
WR_DST_ACK_ADDR  = 8
WR_GO            = 9

class StreamingMemUnitHost( Component ):

  def construct( s, DataType, AddrType, StrideType, CountType,
                 padding, src_base_addr, src_x_stride, src_x_count,
                 src_y_stride, src_y_count, dst_base_addr, dst_ack_addr ):

    data_width = DataType.nbits

    CfgReq, CfgResp = mk_xcel_msg( 4, DataType.nbits )

    s.cfg = XcelMasterIfcRTL( CfgReq, CfgResp )

    s.state_r = Wire( 4 )
    s.state_n = Wire( 4 )

    @update_ff
    def smu_host_fsm_r():
      if s.reset:
        s.state_r <<= IDLE
      else:
        s.state_r <<= s.state_n

    @update
    def smu_host_fsm_n():
      s.state_n @= s.state_r
      if s.state_r == IDLE:
        s.state_n @= WR_SRC_BASE_ADDR
      elif s.state_r == WR_SRC_BASE_ADDR:
        if s.cfg.req.en:
          s.state_n @= WR_PADDING
      elif s.state_r == WR_PADDING:
        if s.cfg.req.en:
          s.state_n @= WR_SRC_X_STRIDE
      elif s.state_r == WR_SRC_X_STRIDE:
        if s.cfg.req.en:
          s.state_n @= WR_SRC_X_COUNT
      elif s.state_r == WR_SRC_X_COUNT:
        if s.cfg.req.en:
          s.state_n @= WR_SRC_Y_STRIDE
      elif s.state_r == WR_SRC_Y_STRIDE:
        if s.cfg.req.en:
          s.state_n @= WR_SRC_Y_COUNT
      elif s.state_r == WR_SRC_Y_COUNT:
        if s.cfg.req.en:
          s.state_n @= WR_DST_BASE_ADDR
      elif s.state_r == WR_DST_BASE_ADDR:
        if s.cfg.req.en:
          s.state_n @= WR_DST_ACK_ADDR
      elif s.state_r == WR_DST_ACK_ADDR:
        if s.cfg.req.en:
          s.state_n @= WR_GO
      elif s.state_r == WR_GO:
        if s.cfg.req.en:
          s.state_n @= IDLE

    @update
    def smu_host_msg():
      s.cfg.req.msg.type_ @= 1
      s.cfg.req.msg.addr @= 0
      s.cfg.req.msg.data @= 0
      s.cfg.req.en @= 0

      if s.state_r != IDLE:
        s.cfg.req.en @= s.cfg.req.rdy

      if s.state_r == WR_SRC_BASE_ADDR:
        s.cfg.req.msg.addr @= SRC_BASE_ADDR
        s.cfg.req.msg.data @= src_base_addr
      elif s.state_r == WR_PADDING:
        s.cfg.req.msg.addr @= PADDING
        s.cfg.req.msg.data @= zext( padding, data_width )
      elif s.state_r == WR_SRC_X_STRIDE:
        s.cfg.req.msg.addr @= SRC_X_STRIDE
        s.cfg.req.msg.data @= src_x_stride
      elif s.state_r == WR_SRC_X_COUNT:
        s.cfg.req.msg.addr @= SRC_X_COUNT
        s.cfg.req.msg.data @= src_x_count
      elif s.state_r == WR_SRC_Y_STRIDE:
        s.cfg.req.msg.addr @= SRC_Y_STRIDE
        s.cfg.req.msg.data @= src_y_stride
      elif s.state_r == WR_SRC_Y_COUNT:
        s.cfg.req.msg.addr @= SRC_Y_COUNT
        s.cfg.req.msg.data @= src_y_count
      elif s.state_r == WR_DST_BASE_ADDR:
        s.cfg.req.msg.addr @= DST_BASE_ADDR
        s.cfg.req.msg.data @= dst_base_addr
      elif s.state_r == WR_DST_ACK_ADDR:
        s.cfg.req.msg.addr @= DST_ACK_ADDR
        s.cfg.req.msg.data @= dst_ack_addr
      elif s.state_r == WR_GO:
        s.cfg.req.msg.addr @= GO
        s.cfg.req.msg.data @= 1

      s.cfg.resp.rdy @= 1
