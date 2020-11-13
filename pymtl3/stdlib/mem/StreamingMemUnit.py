#=========================================================================
# StreamingMemUnit.py
#=========================================================================
# Configurable DMA unit that streams data from source to destination.
#
# Registers (currently supporting matrix gather operation):
# 0. Go
# 1. Status
# 2. Padding
# 3. Source base address
# 4. Source x address stride
# 5. Source x access count
# 6. Source y address stride
# 7. Source y access count
# 8. Destination base address
# 9. Destination ack address
#
# The padding register indicates the sides to which the SMU pads zeros
# LSB 0: west (left column)
#     1: east (right column)
#     2: north (top row)
# MSB 3: south (bottom row)
#
# Author : Peitian Pan
# Date   : Oct 28, 2020

from pymtl3 import *
from pymtl3.stdlib.basic_rtl import RegEnRst
from pymtl3.stdlib.ifcs import mk_xcel_msg, XcelMinionIfcRTL, RecvIfcRTL
from pymtl3.stdlib.mem import mk_mem_msg, MemMasterIfcRTL
from pymtl3.stdlib.queues import ReorderQueue, SendIfcRTLArbiter
from pymtl3.stdlib.connects import connect_pairs

# Padding Directions
W = 0
E = 1
N = 2
S = 3

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

#=========================================================================
# Control unit
#=========================================================================

class StreamingMemUnitCtrl( Component ):

  def construct( s, num_elems ):

    #---------------------------------------------------------------------
    # Sanity check
    #---------------------------------------------------------------------

    num_elems_width = clog2(num_elems)
    assert num_elems == 2**num_elems_width
    credit_width = num_elems_width+1

    #---------------------------------------------------------------------
    # Interfaces
    #---------------------------------------------------------------------

    s.cfg_req_en   = InPort()
    s.cfg_req_rdy  = OutPort()
    s.cfg_resp_en  = OutPort()
    s.cfg_resp_rdy = InPort()

    s.remote_req_en   = OutPort()
    s.remote_req_rdy  = InPort()

    s.local_req_en   = OutPort()
    s.local_req_rdy  = InPort()
    s.local_resp_en  = InPort()
    s.local_resp_rdy = OutPort()

    s.is_cfg_msg_go = InPort()
    s.remote_req_all_sent = InPort()
    s.local_req_all_sent = InPort()
    s.local_req_all_sent_n = InPort()

    s.cfg_go = OutPort()
    s.is_ack_state = OutPort()
    s.remote_sent = OutPort()
    s.local_sent = OutPort()

    s.is_padding = InPort()
    s.reorder_q_deq_en = OutPort()
    s.reorder_q_deq_rdy = InPort()
    s.pad_resp_en = OutPort()
    s.pad_resp_rdy = InPort()

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
      s.smu_work_done @= (s.state == WORK) & s.local_req_all_sent_n
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
    # Credit counter
    #---------------------------------------------------------------------

    s.credit_r = Wire( credit_width )
    s.credit_n = Wire( credit_width )

    s.remote_ifc_sent = Wire()
    s.pad_ifc_sent = Wire()

    @update_ff
    def smu_ctrl_credit_counter():
      if s.reset:
        s.credit_r <<= num_elems
      else:
        s.credit_r <<= s.credit_n

    @update
    def smu_ctrl_credit_n():
      s.credit_n @= s.credit_r
      if s.remote_sent & ~s.reorder_q_deq_en:
        s.credit_n @= s.credit_r - 1
      if ~s.remote_sent & s.reorder_q_deq_en:
        s.credit_n @= s.credit_r + 1

    s.remote_ifc_sent //= lambda: s.remote_req_en & s.remote_req_rdy
    s.pad_ifc_sent    //= lambda: s.pad_resp_en & s.pad_resp_rdy

    #---------------------------------------------------------------------
    # Control signals
    #---------------------------------------------------------------------

    s.cfg_go //= lambda: s.cfg_req_en & s.cfg_req_rdy
    s.is_ack_state //= lambda: s.state == ACK

    s.remote_sent //= lambda: s.remote_ifc_sent | s.pad_ifc_sent
    s.local_sent //= lambda: s.local_req_en & s.local_req_rdy

    s.cfg_req_rdy //= lambda: s.state == IDLE
    s.cfg_resp_en //= 0

    s.remote_req_en //= lambda: s.remote_req_rdy & (s.state == WORK) & \
                                ~s.is_padding & \
                                (s.credit_r != 0) & ~s.remote_req_all_sent

    s.pad_resp_en //= lambda: s.pad_resp_rdy & (s.state == WORK) & \
                              s.is_padding & \
                              (s.credit_r != 0) & ~s.remote_req_all_sent

    s.local_req_en //= lambda: s.local_req_rdy & \
                               (((s.state == WORK) & ~s.local_req_all_sent & s.reorder_q_deq_en) | \
                                (s.state == ACK))

    s.reorder_q_deq_en //= lambda: s.reorder_q_deq_rdy & s.local_req_rdy

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
    # return f"{state}:CFG{s.cfg_req_en}{s.cfg_req_rdy}:"\
    #        f"R{s.remote_req_en}{s.remote_req_rdy}:"\
    #        f"L{s.local_req_en}{s.local_req_rdy}"\
    return f"{state}"

#=========================================================================
# Datapath
#=========================================================================

class StreamingMemUnitDpath( Component ):

  def construct( s, DataType, AddrType, StrideType, CountType, OpaqueType,
                 num_elems ):

    data_width   = DataType.nbits
    addr_width   = AddrType.nbits
    stride_width = StrideType.nbits
    count_width  = CountType.nbits
    opaque_nbits = OpaqueType.nbits

    CfgReq, CfgResp = mk_xcel_msg( addr_width, data_width )
    RemoteReq, RemoteResp = mk_mem_msg( opaque_nbits, addr_width, data_width )
    LocalReq, LocalResp = mk_mem_msg( opaque_nbits, addr_width, data_width )

    #---------------------------------------------------------------------
    # Interfaces
    #---------------------------------------------------------------------

    s.cfg_req_msg = InPort( CfgReq )
    s.cfg_resp_msg = OutPort( CfgResp )

    s.remote_req_msg = OutPort( RemoteReq )

    s.remote_resp = RecvIfcRTL( RemoteResp )

    s.local_req_msg = OutPort( LocalReq )
    s.local_resp_msg = InPort( LocalResp )

    s.is_cfg_msg_go = OutPort()
    s.remote_req_all_sent = OutPort()
    s.local_req_all_sent = OutPort()
    s.local_req_all_sent_n = OutPort()

    s.cfg_go = InPort()
    s.is_ack_state = InPort()
    s.remote_sent = InPort()
    s.local_sent = InPort()

    s.is_padding = OutPort()
    s.reorder_q_deq_en = InPort()
    s.reorder_q_deq_rdy = OutPort()
    s.pad_resp_en = InPort()
    s.pad_resp_rdy = OutPort()

    #---------------------------------------------------------------------
    # Registers
    #---------------------------------------------------------------------

    # NUM_REGISTERS   = 10
    s.go_r              = RegEnRst( Bits1 )
    s.status_r          = RegEnRst( Bits1 )
    s.padding_r         = RegEnRst( Bits4 )
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
      elif s.cfg_read_addr_r == PADDING:
        s.register_read_n @= zext( s.padding_r.out, data_width )
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
      s.padding_r.in_         @= s.cfg_req_msg.data[0:4]
      s.src_base_addr_r.in_   @= s.cfg_req_msg.data[0:addr_width]
      s.src_x_stride_r.in_    @= s.cfg_req_msg.data[0:stride_width]
      s.src_x_count_r.in_     @= s.cfg_req_msg.data[0:count_width]
      s.src_y_stride_r.in_    @= s.cfg_req_msg.data[0:stride_width]
      s.src_y_count_r.in_     @= s.cfg_req_msg.data[0:count_width]
      s.dst_base_addr_r.in_   @= s.cfg_req_msg.data[0:addr_width]
      s.dst_ack_addr_r.in_    @= s.cfg_req_msg.data[0:addr_width]

      s.go_r.en              @= s.cfg_go & (s.cfg_req_msg.addr == GO)
      s.status_r.en          @= s.cfg_go & (s.cfg_req_msg.addr == STATUS)
      s.padding_r.en         @= s.cfg_go & (s.cfg_req_msg.addr == PADDING)
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
    s.remote_opaque_r = Wire( OpaqueType )

    s.remote_x_count_n = Wire( CountType )
    s.remote_y_count_n = Wire( CountType )
    s.local_x_count_n = Wire( CountType )
    s.local_y_count_n = Wire( CountType )
    s.remote_opaque_n = Wire( OpaqueType )

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
        s.remote_opaque_r <<= 0
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

        if s.cfg_go & (s.cfg_req_msg.addr == GO):
          s.remote_opaque_r <<= 0
        else:
          s.remote_opaque_r <<= s.remote_opaque_n

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
      s.remote_opaque_n          @= s.remote_opaque_r

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

      if s.remote_sent:
        s.remote_opaque_n @= s.remote_opaque_r + 1

    #---------------------------------------------------------------------
    # Padding
    #---------------------------------------------------------------------

    s.pad_resp_msg = Wire( RemoteResp )

    @update
    def smu_dpath_is_padding():
      s.is_padding @= 0
      if s.padding_r.out[W] & (s.remote_x_count_r == s.src_x_count_r.out):
        s.is_padding @= 1
      if s.padding_r.out[E] & (s.remote_x_count_r == 1):
        s.is_padding @= 1
      if s.padding_r.out[N] & (s.remote_y_count_r == s.src_y_count_r.out):
        s.is_padding @= 1
      if s.padding_r.out[S] & (s.remote_y_count_r == 1):
        s.is_padding @= 1

    #---------------------------------------------------------------------
    # 2-to-1 grant-hold arbiter
    #---------------------------------------------------------------------

    s.arb = SendIfcRTLArbiter( RemoteResp, 2 )

    s.arb.recv[0] //= s.remote_resp
    s.arb.recv[1].en //= s.pad_resp_en
    s.arb.recv[1].rdy //= s.pad_resp_rdy
    s.arb.recv[1].msg //= s.pad_resp_msg

    #---------------------------------------------------------------------
    # Reorder queue
    #---------------------------------------------------------------------

    s.reorder_q = ReorderQueue( RemoteResp, num_elems )

    s.reorder_q.enq //= s.arb.send

    s.reorder_q.deq.en //= s.reorder_q_deq_en
    s.reorder_q.deq.rdy //= s.reorder_q_deq_rdy

    #---------------------------------------------------------------------
    # Msg
    #---------------------------------------------------------------------

    @update
    def smu_dpath_msg():
      s.cfg_resp_msg.type_ @= 0
      s.cfg_resp_msg.data  @= 0

      s.pad_resp_msg.type_  @= 0
      s.pad_resp_msg.opaque @= s.remote_opaque_r
      s.pad_resp_msg.test   @= 0
      s.pad_resp_msg.len    @= 0
      s.pad_resp_msg.data   @= 0

      s.remote_req_msg.type_  @= 0
      s.remote_req_msg.opaque @= s.remote_opaque_r
      s.remote_req_msg.len    @= 0
      s.remote_req_msg.data   @= 0
      s.remote_req_msg.addr   @= s.remote_addr

      # TODO: currently only supports matrix-gather mode
      s.local_req_msg.type_  @= 1
      s.local_req_msg.opaque @= s.reorder_q.deq.ret.opaque
      s.local_req_msg.len    @= 0
      s.local_req_msg.data   @= s.reorder_q.deq.ret.data if ~s.is_ack_state else 1
      s.local_req_msg.addr   @= s.local_addr_r if ~s.is_ack_state else s.dst_ack_addr_r.out

    #---------------------------------------------------------------------
    # Control signals
    #---------------------------------------------------------------------

    s.remote_req_all_sent_n = Wire()

    @update
    def smu_dpath_all_sent_n():
      s.remote_req_all_sent_n @= s.remote_req_all_sent
      s.local_req_all_sent_n @= s.local_req_all_sent

      if s.cfg_go & (s.cfg_req_msg.addr == GO):
        s.remote_req_all_sent_n @= 0
        s.local_req_all_sent_n  @= 0
      else:
        s.remote_req_all_sent_n @= s.remote_req_all_sent | \
                                   ( s.remote_sent & \
                                   ( s.remote_x_count_r == 1 ) & \
                                   ( s.remote_y_count_r == 1 ) )
        s.local_req_all_sent_n  @= s.local_req_all_sent | \
                                   ( s.local_sent & \
                                   ( s.local_x_count_r == 1 ) & \
                                   ( s.local_y_count_r == 1 ) )

    @update_ff
    def smu_dpath_all_sent_r():
      if s.reset:
        s.remote_req_all_sent <<= 0
        s.local_req_all_sent <<= 0
      else:
        s.remote_req_all_sent <<= s.remote_req_all_sent_n
        s.local_req_all_sent  <<= s.local_req_all_sent_n

    s.is_cfg_msg_go //= lambda: s.cfg_req_msg.addr == GO

  def line_trace( s ):
    # return f"CFG:{s.cfg_req_msg}|"\
           # f"{s.src_x_count_r.out} {s.src_y_count_r.out}|"\
    return \
           f"#x:{s.remote_x_count_r}#y:{s.remote_y_count_r}|"\
           f"Row-:{s.remote_row_addr_r}"\
           f"Row+:{s.remote_row_addr_offset_r}|"\
           f"Pad?{s.is_padding}{s.pad_resp_en}-{s.pad_resp_msg}|"\
           f"Rord{s.reorder_q.deq}|"\
           f"L{s.local_req_msg}"

#=========================================================================
# Main SMU
#=========================================================================

class StreamingMemUnit( Component ):

  @staticmethod
  def get_available_modes():
    return ['matrix-gather']

  def construct( s, DataType=Bits32, AddrType=Bits20, StrideType=Bits10,
                 CountType=Bits10, OpaqueType=Bits5, num_elems=32,
                 mode='matrix-gather' ):

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
    opaque_nbits = OpaqueType.nbits

    CfgReq, CfgResp = mk_xcel_msg( addr_nbits, data_nbits )
    RemoteReq, RemoteResp = mk_mem_msg( opaque_nbits, addr_nbits, data_nbits )
    LocalReq, LocalResp = mk_mem_msg( opaque_nbits, addr_nbits, data_nbits )

    # Configuration interface
    s.cfg = XcelMinionIfcRTL( CfgReq, CfgResp )

    # Remote interface
    s.remote = MemMasterIfcRTL( RemoteReq, RemoteResp )

    # Local interface
    s.local = MemMasterIfcRTL( LocalReq, LocalResp )

    #---------------------------------------------------------------------
    # Components
    #---------------------------------------------------------------------

    s.ctrl  = StreamingMemUnitCtrl( num_elems )
    s.dpath = StreamingMemUnitDpath(
                  DataType, AddrType, StrideType, CountType, OpaqueType,
                  num_elems )

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

        s.dpath.remote_resp, s.remote.resp,

        s.ctrl.local_req_en,    s.local.req.en,
        s.ctrl.local_req_rdy,   s.local.req.rdy,
        s.dpath.local_req_msg,  s.local.req.msg,

        s.ctrl.local_resp_en,    s.local.resp.en,
        s.ctrl.local_resp_rdy,   s.local.resp.rdy,
        s.dpath.local_resp_msg,  s.local.resp.msg,

        s.ctrl.is_cfg_msg_go,       s.dpath.is_cfg_msg_go,
        s.ctrl.remote_req_all_sent, s.dpath.remote_req_all_sent,
        s.ctrl.local_req_all_sent,  s.dpath.local_req_all_sent,
        s.ctrl.local_req_all_sent_n,  s.dpath.local_req_all_sent_n,

        s.ctrl.cfg_go,              s.dpath.cfg_go,
        s.ctrl.is_ack_state,        s.dpath.is_ack_state,
        s.ctrl.remote_sent,         s.dpath.remote_sent,
        s.ctrl.local_sent,          s.dpath.local_sent,

        s.ctrl.is_padding,        s.dpath.is_padding,
        s.ctrl.reorder_q_deq_en,  s.dpath.reorder_q_deq_en,
        s.ctrl.reorder_q_deq_rdy, s.dpath.reorder_q_deq_rdy,
        s.ctrl.pad_resp_en,       s.dpath.pad_resp_en,
        s.ctrl.pad_resp_rdy,      s.dpath.pad_resp_rdy,
    )

  def line_trace( s ):
    input_str  = f"{s.cfg.req}|{s.remote.req}|{s.remote.resp}"
    middle_str = f"([{s.ctrl.line_trace()}]{s.dpath.line_trace()})"
    output_str = f"{s.local.req}"
    return f"{input_str} > {middle_str} > {output_str}"
