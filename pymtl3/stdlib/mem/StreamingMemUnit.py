#=========================================================================
# StreamingMemUnit.py
#=========================================================================
# Configurable DMA unit that streams data from source to destination.
#
# Registers (currently supporting square gather operation):
# 0. Go
# 1. Status
# 2. Source base address
# 3. Source x address stride
# 4. Source x access count
# 5. Source y address stride
# 6. Source y access count
# 7. Destination base address
# 8. Destination ack address
#
# Author : Peitian Pan
# Date   : Oct 28, 2020

from pymtl3 import *
from pymtl3.stdlib.basic_rtl import RegEnRst
from pymtl3.stdlib.ifcs import mk_xcel_msg, XcelMinionIfcRTL
from pymtl3.stdlib.mem import mk_mem_msg, MemMasterIfcRTL
from pymtl3.stdlib.connects import connect_pairs

GO              = 0
STATUS          = 1
SRC_BASE_ADDR   = 2
SRC_X_STRIDE    = 3
SRC_X_COUNT     = 4
SRC_Y_STRIDE    = 5
SRC_Y_COUNT     = 6
DST_BASE_ADDR   = 7
DST_ACK_ADDR    = 8
NUM_REGISTERS   = 9

#=========================================================================
# Control unit
#=========================================================================

class StreamingMemUnitCtrl( Component ):

  def construct( s ):

    s.cfg_req_en   = InPort()
    s.cfg_req_rdy  = OutPort()
    s.cfg_resp_en  = OutPort()
    s.cfg_resp_rdy = InPort()

    s.remote_req_en   = OutPort()
    s.remote_req_rdy  = InPort()
    s.remote_resp_en  = InPort()
    s.remote_resp_rdy = OutPort()

    s.local_req_en   = OutPort()
    s.local_req_rdy  = InPort()
    s.local_resp_en  = InPort()
    s.local_resp_rdy = OutPort()

    s.is_cfg_msg_go = InPort()
    s.remote_req_all_sent = InPort()
    s.local_req_all_sent = InPort()

    s.cfg_go = OutPort()
    s.is_ack_state = OutPort()
    s.remote_sent = OutPort()
    s.local_sent = OutPort()

    #---------------------------------------------------------------------
    # FSM
    #---------------------------------------------------------------------

    IDLE = 0
    WORK = 1
    ACK  = 2

    s.state = Wire( 2 )
    s.state_next = Wire( 2 )

    s.smu_go = Wire()
    s.smu_work_done = Wire()
    s.smu_ack_sent = Wire()

    @update
    def smu_ctrl_fsm_comb_signals():
      s.smu_go        @= s.cfg_req_en & s.cfg_req_rdy & s.is_cfg_msg_go
      s.smu_work_done @= (s.state == WORK) & s.local_req_all_sent
      s.smu_ack_sent  @= (s.state == ACK) & s.local_req_en & s.local_req_rdy

    @update_ff
    def smu_ctrl_fsm():
      if s.reset:
        s.state <<= IDLE
      else:
        s.state <<= s.state_next

    @update
    def smu_ctrl_next_state():
      s.state_next @= s.state
      if s.state == IDLE:
        if s.smu_go:
          s.state_next @= WORK
      elif s.state == WORK:
        if s.smu_work_done:
          s.state_next @= ACK
      elif s.state == ACK:
        if s.smu_ack_sent:
          s.state_next @= IDLE

    #---------------------------------------------------------------------
    # Control signals
    #---------------------------------------------------------------------

    s.cfg_go //= lambda: s.cfg_req_en & s.cfg_req_rdy
    s.is_ack_state //= lambda: s.state == ACK

    s.remote_sent //= lambda: s.remote_req_en & s.remote_req_rdy
    s.local_sent //= lambda: s.local_req_en & s.local_req_rdy

    s.cfg_req_rdy //= lambda: s.state == IDLE
    s.cfg_resp_en //= 0

    s.remote_req_en //= lambda: s.remote_req_rdy & (s.state == WORK) & ~s.remote_req_all_sent
    s.remote_resp_rdy //= s.local_req_rdy

    s.local_req_en //= lambda: s.local_req_rdy & (((s.state == WORK) & ~s.local_req_all_sent & s.remote_resp_en) | (s.state == ACK))
    s.local_resp_rdy //= 1

  def line_trace( s ):
    if s.state == 0:
      state = 'IDLE'
    elif s.state == 1:
      state = 'WORK'
    elif s.state == 2:
      state = 'ACK '
    else:
      state = '????'
    return f"{state}:CFG{s.cfg_req_en}{s.cfg_req_rdy}:"\
           f"R{s.remote_req_en}{s.remote_req_rdy}:"\
           f"L{s.local_req_en}{s.local_req_rdy}"\

#=========================================================================
# Datapath
#=========================================================================

class StreamingMemUnitDpath( Component ):

  def construct( s, DataType, AddrType, StrideType, CountType ):

    data_width   = DataType.nbits
    addr_width   = AddrType.nbits
    stride_width = StrideType.nbits
    count_width  = CountType.nbits

    CfgReq, CfgResp = mk_xcel_msg( addr_width, data_width )
    RemoteReq, RemoteResp = mk_mem_msg( 1, addr_width, data_width )
    LocalReq, LocalResp = mk_mem_msg( 1, addr_width, data_width )

    #---------------------------------------------------------------------
    # Interfaces
    #---------------------------------------------------------------------

    s.cfg_req_msg = InPort( CfgReq )
    s.cfg_resp_msg = OutPort( CfgResp )

    s.remote_req_msg = OutPort( RemoteReq )
    s.remote_resp_msg = InPort( RemoteResp )

    s.local_req_msg = OutPort( LocalReq )
    s.local_resp_msg = InPort( LocalResp )

    s.is_cfg_msg_go = OutPort()
    s.remote_req_all_sent = OutPort()
    s.local_req_all_sent = OutPort()

    s.cfg_go = InPort()
    s.is_ack_state = InPort()
    s.remote_sent = InPort()
    s.local_sent = InPort()

    #---------------------------------------------------------------------
    # Registers
    #---------------------------------------------------------------------

    # NUM_REGISTERS   = 10
    s.go_r              = RegEnRst( Bits1 )
    s.status_r          = RegEnRst( Bits1 )
    s.src_base_addr_r   = RegEnRst( AddrType )
    s.src_x_stride_r    = RegEnRst( StrideType )
    s.src_x_count_r     = RegEnRst( CountType )
    s.src_y_stride_r    = RegEnRst( StrideType )
    s.src_y_count_r     = RegEnRst( CountType )
    s.dst_base_addr_r   = RegEnRst( AddrType )
    s.dst_ack_addr_r    = RegEnRst( AddrType )

    s.register_read_r = Wire( DataType )
    s.register_read_n = Wire( DataType )
    s.cfg_read_addr_r = Wire( AddrType )

    @update_ff
    def smu_dpath_registers():
      if s.reset:
        s.register_read_r <<= 0
        s.cfg_read_addr_r <<= 0
      else:
        s.register_read_r <<= s.register_read_n
        s.cfg_read_addr_r <<= s.cfg_req_msg.addr

    @update
    def smu_dpath_register_read_n():
      s.register_read_n @= 0
      if s.cfg_read_addr_r == GO:
        s.register_read_n @= zext( s.go_r.out, data_width )
      elif s.cfg_read_addr_r == STATUS:
        s.register_read_n @= zext( s.status_r.out, data_width )
      elif s.cfg_read_addr_r == SRC_BASE_ADDR:
        s.register_read_n @= zext( s.src_base_addr_r.out, data_width )
      elif s.cfg_read_addr_r == SRC_X_STRIDE:
        s.register_read_n @= zext( s.src_x_stride_r.out, data_width )
      elif s.cfg_read_addr_r == SRC_X_COUNT:
        s.register_read_n @= zext( s.src_x_count_r.out, data_width )
      elif s.cfg_read_addr_r == SRC_Y_STRIDE:
        s.register_read_n @= zext( s.src_y_stride_r.out, data_width )
      elif s.cfg_read_addr_r == SRC_Y_COUNT:
        s.register_read_n @= zext( s.src_y_count_r.out, data_width )
      elif s.cfg_read_addr_r == DST_BASE_ADDR:
        s.register_read_n @= zext( s.dst_base_addr_r.out, data_width )
      elif s.cfg_read_addr_r == DST_ACK_ADDR:
        s.register_read_n @= zext( s.dst_ack_addr_r.out, data_width )

    @update
    def smu_dpath_register_in_ports():
      s.go_r.in_              @= s.cfg_req_msg.data[0:1]
      s.status_r.in_          @= s.cfg_req_msg.data[0:1]
      s.src_base_addr_r.in_   @= s.cfg_req_msg.data[0:addr_width]
      s.src_x_stride_r.in_    @= s.cfg_req_msg.data[0:stride_width]
      s.src_x_count_r.in_     @= s.cfg_req_msg.data[0:count_width]
      s.src_y_stride_r.in_    @= s.cfg_req_msg.data[0:stride_width]
      s.src_y_count_r.in_     @= s.cfg_req_msg.data[0:count_width]
      s.dst_base_addr_r.in_   @= s.cfg_req_msg.data[0:addr_width]
      s.dst_ack_addr_r.in_    @= s.cfg_req_msg.data[0:addr_width]

      s.go_r.en              @= s.cfg_go & (s.cfg_req_msg.addr == GO)
      s.status_r.en          @= s.cfg_go & (s.cfg_req_msg.addr == STATUS)
      s.src_base_addr_r.en   @= s.cfg_go & (s.cfg_req_msg.addr == SRC_BASE_ADDR)
      s.src_x_stride_r.en    @= s.cfg_go & (s.cfg_req_msg.addr == SRC_X_STRIDE)
      s.src_x_count_r.en     @= s.cfg_go & (s.cfg_req_msg.addr == SRC_X_COUNT)
      s.src_y_stride_r.en    @= s.cfg_go & (s.cfg_req_msg.addr == SRC_Y_STRIDE)
      s.src_y_count_r.en     @= s.cfg_go & (s.cfg_req_msg.addr == SRC_Y_COUNT)
      s.dst_base_addr_r.en   @= s.cfg_go & (s.cfg_req_msg.addr == DST_BASE_ADDR)
      s.dst_ack_addr_r.en    @= s.cfg_go & (s.cfg_req_msg.addr == DST_ACK_ADDR)

    #---------------------------------------------------------------------
    # Counters
    #---------------------------------------------------------------------

    s.remote_x_count_r = Wire( CountType )
    s.remote_y_count_r = Wire( CountType )
    s.local_x_count_r = Wire( CountType )
    s.local_y_count_r = Wire( CountType )

    s.remote_x_count_n = Wire( CountType )
    s.remote_y_count_n = Wire( CountType )
    s.local_x_count_n = Wire( CountType )
    s.local_y_count_n = Wire( CountType )

    s.remote_addr = Wire( AddrType )

    s.local_addr_r = Wire( AddrType )
    s.local_addr_n = Wire( AddrType )

    s.remote_row_addr_r = Wire( AddrType )
    s.remote_row_addr_n = Wire( AddrType )

    s.remote_row_addr_offset_r = Wire( AddrType )
    s.remote_row_addr_offset_n = Wire( AddrType )

    @update_ff
    def smu_dpath_xy_count_r():
      if s.reset:
        s.remote_x_count_r <<= 0
        s.remote_y_count_r <<= 0
        s.local_x_count_r  <<= 0
        s.local_y_count_r  <<= 0
        s.remote_row_addr_r <<= 0
        s.remote_row_addr_offset_r <<= 0
        s.local_addr_r <<= 0
      else:
        if s.cfg_go & (s.cfg_req_msg.addr == SRC_X_COUNT):
          s.remote_x_count_r <<= s.cfg_req_msg.data[0:count_width]
          s.local_x_count_r  <<= s.cfg_req_msg.data[0:count_width]
        else:
          s.remote_x_count_r <<= s.remote_x_count_n
          s.local_x_count_r  <<= s.local_x_count_n

        if s.cfg_go & (s.cfg_req_msg.addr == SRC_Y_COUNT):
          s.remote_y_count_r <<= s.cfg_req_msg.data[0:count_width]
          s.local_y_count_r  <<= s.cfg_req_msg.data[0:count_width]
        else:
          s.remote_y_count_r <<= s.remote_y_count_n
          s.local_y_count_r  <<= s.local_y_count_n

        if s.cfg_go & (s.cfg_req_msg.addr == SRC_BASE_ADDR):
          s.remote_row_addr_r <<= s.cfg_req_msg.data[0:addr_width]
          s.remote_row_addr_offset_r <<= 0
        else:
          s.remote_row_addr_r <<= s.remote_row_addr_n
          s.remote_row_addr_offset_r <<= s.remote_row_addr_offset_n

        if s.cfg_go & (s.cfg_req_msg.addr == DST_BASE_ADDR):
          s.local_addr_r <<= s.cfg_req_msg.data[0:addr_width]
        else:
          s.local_addr_r <<= s.local_addr_n

    @update
    def smu_dpath_xy_count_n():
      s.remote_x_count_n         @= s.remote_x_count_r
      s.remote_y_count_n         @= s.remote_y_count_r
      s.local_x_count_n          @= s.local_x_count_r
      s.local_y_count_n          @= s.local_y_count_r
      s.remote_row_addr_n        @= s.remote_row_addr_r
      s.remote_row_addr_offset_n @= s.remote_row_addr_offset_r
      s.remote_addr              @= s.remote_row_addr_r + s.remote_row_addr_offset_r
      s.local_addr_n             @= s.local_addr_r

      if s.remote_sent & (s.remote_x_count_r == 1) & (s.remote_y_count_r > 1):
        s.remote_x_count_n         @= s.src_x_count_r.out
        s.remote_y_count_n         @= s.remote_y_count_r-1
        s.remote_row_addr_n        @= s.remote_row_addr_n + zext( s.src_y_stride_r.out, addr_width )
        s.remote_row_addr_offset_n @= 0
      elif s.remote_sent & (s.remote_x_count_r > 1):
        s.remote_x_count_n         @= s.remote_x_count_r-1
        s.remote_row_addr_offset_n @= s.remote_row_addr_offset_r + zext( s.src_x_stride_r.out, addr_width )

      if s.local_sent & (s.local_x_count_r == 1) & (s.local_y_count_r > 1):
        s.local_x_count_n @= s.src_x_count_r.out
        s.local_y_count_n @= s.local_y_count_r-1
      elif s.local_sent & (s.local_x_count_r > 1):
        s.local_x_count_n @= s.local_x_count_r-1

      if s.local_sent:
        s.local_addr_n @= s.local_addr_n + 4

    #---------------------------------------------------------------------
    # Msg
    #---------------------------------------------------------------------

    @update
    def smu_dpath_msg():
      s.cfg_resp_msg.type_ @= 0
      s.cfg_resp_msg.data  @= 0

      s.remote_req_msg.type_ @= 0
      s.remote_req_msg.opaque @= 0
      s.remote_req_msg.len @= 0
      s.remote_req_msg.data @= 0
      s.remote_req_msg.addr @= s.remote_addr

      # TODO: currently only supports square-gather mode
      s.local_req_msg.type_ @= 1
      s.local_req_msg.opaque @= 0
      s.local_req_msg.len @= 0
      s.local_req_msg.data @= s.remote_resp_msg.data if ~s.is_ack_state else 1
      s.local_req_msg.addr @= s.local_addr_r if ~s.is_ack_state else s.dst_ack_addr_r.out

    #---------------------------------------------------------------------
    # Control signals
    #---------------------------------------------------------------------

    s.remote_req_all_sent_r = Wire()
    s.local_req_all_sent_r = Wire()

    @update_ff
    def smu_dpath_all_sent_r():
      if s.reset:
        s.remote_req_all_sent_r <<= 0
        s.local_req_all_sent_r <<= 0
      else:
        if s.cfg_go & (s.cfg_req_msg.addr == GO):
          s.remote_req_all_sent_r <<= 0
          s.local_req_all_sent_r <<= 0
        else:
          s.remote_req_all_sent_r <<= s.remote_req_all_sent_r | \
                                    (  s.remote_sent & \
                                     ( s.remote_x_count_r == 1 ) & \
                                     ( s.remote_y_count_r == 1 ) )
          s.local_req_all_sent_r <<= s.local_req_all_sent_r | \
                                    (  s.local_sent & \
                                     ( s.local_x_count_r == 1 ) & \
                                     ( s.local_y_count_r == 1 ) )

    s.is_cfg_msg_go //= lambda: s.cfg_req_msg.addr == GO

    s.remote_req_all_sent //= s.remote_req_all_sent_r
    s.local_req_all_sent //= s.local_req_all_sent_r

  def line_trace( s ):
    # return f"CFG:{s.cfg_req_msg}|"\
    return \
           f"{s.src_x_count_r.out} {s.src_y_count_r.out}|"\
           f"Rx:{s.remote_x_count_r} Ry:{s.remote_y_count_r}|"\
           f"Row:{s.remote_row_addr_r}|"\
           f"RowOffset:{s.remote_row_addr_offset_r}|"\
           f"R{s.remote_req_msg}:{s.remote_resp_msg}|"\
           f"L{s.local_req_msg}"

#=========================================================================
# Main SMU
#=========================================================================

class StreamingMemUnit( Component ):

  @staticmethod
  def get_available_modes():
    return ['square-gather']

  def construct( s, DataType=Bits32, AddrType=Bits20, StrideType=Bits10,
                 CountType=Bits10, mode='square-gather' ):

    #---------------------------------------------------------------------
    # Sanity checks
    #---------------------------------------------------------------------

    modes = StreamingMemUnit.get_available_modes()
    assert mode in modes
    s.mode = mode

    #---------------------------------------------------------------------
    # Interfaces
    #---------------------------------------------------------------------

    addr_nbits = AddrType.nbits
    data_nbits = DataType.nbits
    stride_nbits = StrideType.nbits
    count_nbits = CountType.nbits

    CfgReq, CfgResp = mk_xcel_msg( addr_nbits, data_nbits )
    RemoteReq, RemoteResp = mk_mem_msg( 1, addr_nbits, data_nbits )
    LocalReq, LocalResp = mk_mem_msg( 1, addr_nbits, data_nbits )

    # Configuration interface
    s.cfg = XcelMinionIfcRTL( CfgReq, CfgResp )

    # Remote interface
    s.remote = MemMasterIfcRTL( RemoteReq, RemoteResp )

    # Local interface
    s.local = MemMasterIfcRTL( LocalReq, LocalResp )

    #---------------------------------------------------------------------
    # Components
    #---------------------------------------------------------------------

    s.ctrl  = StreamingMemUnitCtrl()
    s.dpath = StreamingMemUnitDpath( DataType, AddrType, StrideType, CountType )

    connect_pairs(
        s.ctrl.cfg_req_en,      s.cfg.req.en,
        s.ctrl.cfg_req_rdy,     s.cfg.req.rdy,
        s.dpath.cfg_req_msg,    s.cfg.req.msg,

        s.ctrl.cfg_resp_en,      s.cfg.resp.en,
        s.ctrl.cfg_resp_rdy,     s.cfg.resp.rdy,
        s.dpath.cfg_resp_msg,    s.cfg.resp.msg,

        s.ctrl.remote_req_en,   s.remote.req.en,
        s.ctrl.remote_req_rdy,  s.remote.req.rdy,
        s.dpath.remote_req_msg, s.remote.req.msg,

        s.ctrl.remote_resp_en,   s.remote.resp.en,
        s.ctrl.remote_resp_rdy,  s.remote.resp.rdy,
        s.dpath.remote_resp_msg, s.remote.resp.msg,

        s.ctrl.local_req_en,    s.local.req.en,
        s.ctrl.local_req_rdy,   s.local.req.rdy,
        s.dpath.local_req_msg,  s.local.req.msg,

        s.ctrl.local_resp_en,    s.local.resp.en,
        s.ctrl.local_resp_rdy,   s.local.resp.rdy,
        s.dpath.local_resp_msg,  s.local.resp.msg,

        s.ctrl.is_cfg_msg_go,       s.dpath.is_cfg_msg_go,
        s.ctrl.remote_req_all_sent, s.dpath.remote_req_all_sent,
        s.ctrl.local_req_all_sent,  s.dpath.local_req_all_sent,
        s.ctrl.cfg_go,              s.dpath.cfg_go,
        s.ctrl.is_ack_state,        s.dpath.is_ack_state,
        s.ctrl.remote_sent,         s.dpath.remote_sent,
        s.ctrl.local_sent,          s.dpath.local_sent,
    )

  def line_trace( s ):
    return f"[{s.ctrl.line_trace()}] {s.dpath.line_trace()}"
