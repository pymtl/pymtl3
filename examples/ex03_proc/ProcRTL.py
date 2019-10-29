"""
==========================================================================
ProcRTL.py
==========================================================================
TinyRV0 RTL proc.

Author : Shunning Jiang
  Date : June 12, 2019
"""
from pymtl3 import *
from pymtl3.stdlib.connects import connect_pairs
from pymtl3.stdlib.ifcs import RecvIfcRTL, SendIfcRTL, mk_mem_msg, mk_xcel_msg
from pymtl3.stdlib.ifcs.mem_ifcs import MemMasterIfcRTL
from pymtl3.stdlib.ifcs.xcel_ifcs import XcelMasterIfcRTL
from pymtl3.stdlib.rtl.enrdy_queues import BypassQueue2RTL
from pymtl3.stdlib.rtl.queues import BypassQueueRTL

from .MiscRTL import DropUnitRTL
from .ProcCtrlRTL import ProcCtrl
from .ProcDpathRTL import ProcDpath
from .tinyrv0_encoding import disassemble_inst
from .TinyRV0InstRTL import inst_dict


class ProcRTL( Component ):

  def construct( s ):

    req_class, resp_class = mk_mem_msg( 8, 32, 32 )

    # Proc/Mngr Interface

    s.mngr2proc = RecvIfcRTL( Bits32 )
    s.proc2mngr = SendIfcRTL( Bits32 )

    # Instruction Memory Request/Response Interface

    s.imem = MemMasterIfcRTL( req_class, resp_class )

    # Data Memory Request/Response Interface

    s.dmem = MemMasterIfcRTL( req_class, resp_class )

    # Xcel Request/Response Interface

    xreq_class, xresp_class = mk_xcel_msg( 5, 32 )

    s.xcel = XcelMasterIfcRTL( xreq_class, xresp_class )

    # val_W port used for counting commited insts.

    s.commit_inst = OutPort( Bits1 )

    # imem drop unit

    s.imemresp_drop = m = DropUnitRTL( Bits32 )
    connect_pairs(
      m.in_.en,  s.imem.resp.en,
      m.in_.rdy, s.imem.resp.rdy,
      m.in_.msg, s.imem.resp.msg.data,
    )

    # Bypass queues

    s.imemreq_q   = BypassQueue2RTL( req_class, 2 )( deq = s.imem.req )

    # We have to turn input receive interface into get interface

    s.imemresp_q  = BypassQueueRTL( Bits32, 1 )( enq = s.imemresp_drop.out )
    s.dmemresp_q  = BypassQueueRTL( resp_class, 1 )( enq = s.dmem.resp )
    s.mngr2proc_q = BypassQueueRTL( Bits32, 1 )( enq = s.mngr2proc )
    s.xcelresp_q  = BypassQueueRTL( xresp_class, 1 )( enq = s.xcel.resp )

    # Control

    s.ctrl  = ProcCtrl()(

      # imem port
      imemresp_drop = s.imemresp_drop.drop,
      imemreq_en    = s.imemreq_q.enq.en,
      imemreq_rdy   = s.imemreq_q.enq.rdy,
      imemresp_en   = s.imemresp_q.deq.en,
      imemresp_rdy  = s.imemresp_q.deq.rdy,

      # dmem port
      dmemreq_en    = s.dmem.req.en,
      dmemreq_rdy   = s.dmem.req.rdy,
      dmemreq_type  = s.dmem.req.msg.type_,
      dmemresp_en   = s.dmemresp_q.deq.en,
      dmemresp_rdy  = s.dmemresp_q.deq.rdy,

      # xcel port
      xcelreq_en    = s.xcel.req.en,
      xcelreq_rdy   = s.xcel.req.rdy,
      xcelresp_en   = s.xcelresp_q.deq.en,
      xcelresp_rdy  = s.xcelresp_q.deq.rdy,

      # proc2mngr and mngr2proc
      proc2mngr_en  = s.proc2mngr.en,
      proc2mngr_rdy = s.proc2mngr.rdy,
      mngr2proc_en  = s.mngr2proc_q.deq.en,
      mngr2proc_rdy = s.mngr2proc_q.deq.rdy,

      # commit inst for counting
      commit_inst = s.commit_inst
    )

    # Dpath

    s.dpath = ProcDpath()(

      # imem ports
      imemreq_addr  = s.imemreq_q.enq.msg.addr,
      imemresp_data = s.imemresp_q.deq.msg,

      # dmem ports
      dmemreq_addr  = s.dmem.req.msg.addr,
      dmemreq_data  = s.dmem.req.msg.data,
      dmemresp_data = s.dmemresp_q.deq.msg.data,

      # xcel ports
      xcelresp_data = s.xcelresp_q.deq.msg.data,

      # mngr
      mngr2proc_data = s.mngr2proc_q.deq.msg,
      proc2mngr_data = s.proc2mngr.msg,

    )
    @s.update
    def up_xcelreq():
      s.xcel.req.msg = xreq_class(
        s.ctrl.xcelreq_type,
        s.dpath.xcelreq_addr,
        s.dpath.xcelreq_data,
      )

    # Ctrl <-> Dpath

    connect_pairs(
      s.ctrl.reg_en_F       , s.dpath.reg_en_F,
      s.ctrl.pc_sel_F       , s.dpath.pc_sel_F,

      s.ctrl.reg_en_D       , s.dpath.reg_en_D,
      s.ctrl.op1_byp_sel_D  , s.dpath.op1_byp_sel_D,
      s.ctrl.op2_byp_sel_D  , s.dpath.op2_byp_sel_D,
      s.ctrl.op2_sel_D      , s.dpath.op2_sel_D,
      s.ctrl.imm_type_D     , s.dpath.imm_type_D,

      s.ctrl.reg_en_X       , s.dpath.reg_en_X,
      s.ctrl.alu_fn_X       , s.dpath.alu_fn_X,

      s.ctrl.reg_en_M       , s.dpath.reg_en_M,
      s.ctrl.wb_result_sel_M, s.dpath.wb_result_sel_M,

      s.ctrl.reg_en_W       , s.dpath.reg_en_W,
      s.ctrl.rf_waddr_W     , s.dpath.rf_waddr_W,
      s.ctrl.rf_wen_W       , s.dpath.rf_wen_W,

      s.dpath.inst_D        , s.ctrl.inst_D,
      s.dpath.ne_X          , s.ctrl.ne_X,
    )

  #-----------------------------------------------------------------------
  # Line tracing
  #-----------------------------------------------------------------------

  def line_trace( s ):
    # F stage
    if not s.ctrl.val_F:  F_str = "{:<8s}".format( ' ' )
    elif s.ctrl.squash_F: F_str = "{:<8s}".format( '~' )
    elif s.ctrl.stall_F:  F_str = "{:<8s}".format( '#' )
    else:                 F_str = "{:08x}".format( s.dpath.pc_reg_F.out.uint() )

    # D stage
    if not s.ctrl.val_D:  D_str = "{:<23s}".format( ' ' )
    elif s.ctrl.squash_D: D_str = "{:<23s}".format( '~' )
    elif s.ctrl.stall_D:  D_str = "{:<23s}".format( '#' )
    else:                 D_str = "{:<23s}".format( disassemble_inst(s.ctrl.inst_D) )

    # X stage
    if not s.ctrl.val_X:  X_str = "{:<5s}".format( ' ' )
    elif s.ctrl.stall_X:  X_str = "{:<5s}".format( '#' )
    else:                 X_str = "{:<5s}".format( inst_dict[s.ctrl.inst_type_X] )

    # M stage
    if not s.ctrl.val_M:  M_str = "{:<5s}".format( ' ' )
    elif s.ctrl.stall_M:  M_str = "{:<5s}".format( '#' )
    else:                 M_str = "{:<5s}".format( inst_dict[s.ctrl.inst_type_M] )

    # W stage
    if not s.ctrl.val_W:  W_str = "{:<5s}".format( ' ' )
    elif s.ctrl.stall_W:  W_str = "{:<5s}".format( '#' )
    else:                 W_str = "{:<5s}".format( inst_dict[s.ctrl.inst_type_W] )

    return "[{}|{}|{}|{}|{}]".format( F_str, D_str, X_str, M_str, W_str)
