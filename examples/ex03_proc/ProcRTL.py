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
from pymtl3.stdlib.xcel import mk_xcel_msg
from pymtl3.stdlib.xcel.ifcs import XcelRequesterIfc
from pymtl3.stdlib.mem import mk_mem_msg
from pymtl3.stdlib.mem.ifcs import MemRequesterIfc
from pymtl3.stdlib.stream import StreamBypassQueue
from pymtl3.stdlib.stream.ifcs import IStreamIfc, OStreamIfc

from .MiscRTL import DropUnitRTL
from .ProcCtrlRTL import ProcCtrl
from .ProcDpathRTL import ProcDpath
from .tinyrv0_encoding import disassemble_inst
from .TinyRV0InstRTL import inst_dict


class ProcRTL( Component ):

  def construct( s ):

    req_class, resp_class = mk_mem_msg( 8, 32, 32 )

    # Proc/Mngr Interface

    s.mngr2proc = IStreamIfc( Bits32 )
    s.proc2mngr = OStreamIfc( Bits32 )

    # Instruction Memory Request/Response Interface

    s.imem = MemRequesterIfc( req_class, resp_class )

    # Data Memory Request/Response Interface

    s.dmem = MemRequesterIfc( req_class, resp_class )

    # Xcel Request/Response Interface

    xreq_class, xresp_class = mk_xcel_msg( 5, 32 )

    s.xcel = XcelRequesterIfc( xreq_class, xresp_class )

    # val_W port used for counting commited insts.

    s.commit_inst = OutPort( Bits1 )

    # Bypass queues

    s.imemreq_q   = StreamBypassQueue( req_class, 2 )

    # We have to turn input receive interface into get interface

    s.imemresp_q  = StreamBypassQueue( resp_class, 1 )
    s.dmemresp_q  = StreamBypassQueue( resp_class, 1 )
    s.mngr2proc_q = StreamBypassQueue( Bits32, 1 )
    s.xcelresp_q  = StreamBypassQueue( xresp_class, 1 )

    # imem drop unit

    s.imemresp_drop = m = DropUnitRTL( Bits32 )
    m.in_.val //= s.imemresp_q.ostream.val
    m.in_.rdy //= s.imemresp_q.ostream.rdy
    m.in_.msg //= s.imemresp_q.ostream.msg.data

    # connect all the queues

    s.imemreq_q.ostream   //= s.imem.reqstream
    s.imemresp_q.istream  //= s.imem.respstream
    s.dmemresp_q.istream  //= s.dmem.respstream
    s.mngr2proc_q.istream //= s.mngr2proc
    s.xcelresp_q.istream  //= s.xcel.respstream

    # Control

    s.ctrl = m = ProcCtrl()

    # imem port
    m.imemresp_drop //= s.imemresp_drop.drop
    m.imemreq_val   //= s.imemreq_q.istream.val
    m.imemreq_rdy   //= s.imemreq_q.istream.rdy
    m.imemresp_val  //= s.imemresp_drop.out.val
    m.imemresp_rdy  //= s.imemresp_drop.out.rdy

    # dmem port
    m.dmemreq_val   //= s.dmem.reqstream.val
    m.dmemreq_rdy   //= s.dmem.reqstream.rdy
    m.dmemreq_type  //= s.dmem.reqstream.msg.type_
    m.dmemresp_val  //= s.dmemresp_q.ostream.val
    m.dmemresp_rdy  //= s.dmemresp_q.ostream.rdy

    # xcel port
    m.xcelreq_type  //= s.xcel.reqstream.msg.type_

    m.xcelreq_val   //= s.xcel.reqstream.val
    m.xcelreq_rdy   //= s.xcel.reqstream.rdy
    m.xcelresp_val  //= s.xcelresp_q.ostream.val
    m.xcelresp_rdy  //= s.xcelresp_q.ostream.rdy

    # proc2mngr and mngr2proc
    m.proc2mngr_val //= s.proc2mngr.val
    m.proc2mngr_rdy //= s.proc2mngr.rdy
    m.mngr2proc_val //= s.mngr2proc_q.ostream.val
    m.mngr2proc_rdy //= s.mngr2proc_q.ostream.rdy

    # commit inst for counting
    m.commit_inst //= s.commit_inst

    # Dpath

    s.dpath = m = ProcDpath()

    # imem ports
    m.imemreq_addr  //= s.imemreq_q.istream.msg.addr
    m.imemresp_data //= s.imemresp_drop.out.msg

    # dmem ports
    m.dmemreq_addr  //= s.dmem.reqstream.msg.addr
    m.dmemreq_data  //= s.dmem.reqstream.msg.data
    m.dmemresp_data //= s.dmemresp_q.ostream.msg.data

    # xcel ports
    m.xcelreq_addr  //= s.xcel.reqstream.msg.addr
    m.xcelreq_data  //= s.xcel.reqstream.msg.data
    m.xcelresp_data //= s.xcelresp_q.ostream.msg.data

    # mngr
    m.mngr2proc_data //= s.mngr2proc_q.ostream.msg
    m.proc2mngr_data //= s.proc2mngr.msg

    # Ctrl <-> Dpath

    s.ctrl.reg_en_F        //= s.dpath.reg_en_F
    s.ctrl.pc_sel_F        //= s.dpath.pc_sel_F

    s.ctrl.reg_en_D        //= s.dpath.reg_en_D
    s.ctrl.op1_byp_sel_D   //= s.dpath.op1_byp_sel_D
    s.ctrl.op2_byp_sel_D   //= s.dpath.op2_byp_sel_D
    s.ctrl.op2_sel_D       //= s.dpath.op2_sel_D
    s.ctrl.imm_type_D      //= s.dpath.imm_type_D

    s.ctrl.reg_en_X        //= s.dpath.reg_en_X
    s.ctrl.alu_fn_X        //= s.dpath.alu_fn_X

    s.ctrl.reg_en_M        //= s.dpath.reg_en_M
    s.ctrl.wb_result_sel_M //= s.dpath.wb_result_sel_M

    s.ctrl.reg_en_W        //= s.dpath.reg_en_W
    s.ctrl.rf_waddr_W      //= s.dpath.rf_waddr_W
    s.ctrl.rf_wen_W        //= s.dpath.rf_wen_W

    s.dpath.inst_D         //= s.ctrl.inst_D
    s.dpath.ne_X           //= s.ctrl.ne_X

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
