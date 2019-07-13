"""
==========================================================================
ProcDpathRTL.py
==========================================================================
Datapath for the RTL TinyRV0 processor.

Author : Shunning Jiang
  Date : June 12, 2019
"""

from pymtl3 import *
from pymtl3.stdlib.ifcs import mk_mem_msg
from pymtl3.stdlib.rtl import Adder, Incrementer, Mux, RegEn, RegEnRst, RegisterFile

from .MiscRTL import AluRTL, ImmGenRTL
from .TinyRV0InstRTL import OPCODE, RD, RS1, RS2, SHAMT

#-------------------------------------------------------------------------
# Constants
#-------------------------------------------------------------------------

c_reset_vector = 0x200
c_reset_inst   = 0

#-------------------------------------------------------------------------
# ProcDpath
#-------------------------------------------------------------------------

class ProcDpath( Component ):

  def construct( s ):

    #---------------------------------------------------------------------
    # Interface
    #---------------------------------------------------------------------

    # imem ports
    s.imemreq_addr   = OutPort( Bits32 )
    s.imemresp_data  = InPort ( Bits32 )

    # dmem ports
    s.dmemreq_addr   = OutPort( Bits32 )
    s.dmemreq_data   = OutPort( Bits32 )
    s.dmemresp_data  = InPort ( Bits32 )

    # mngr ports
    s.mngr2proc_data = InPort ( Bits32 )
    s.proc2mngr_data = OutPort( Bits32 )

    # xcel ports
    s.xcelreq_addr   = OutPort( Bits5 )
    s.xcelreq_data   = OutPort( Bits32 )
    s.xcelresp_data  = InPort ( Bits32 )

    # Control signals (ctrl->dpath)

    s.reg_en_F         = InPort ( Bits1 )
    s.pc_sel_F         = InPort ( Bits1 )

    s.reg_en_D         = InPort ( Bits1 )
    s.op1_byp_sel_D    = InPort ( Bits2 )
    s.op2_byp_sel_D    = InPort ( Bits2 )
    s.op2_sel_D        = InPort ( Bits2 )
    s.imm_type_D       = InPort ( Bits3 )

    s.reg_en_X         = InPort ( Bits1 )
    s.alu_fn_X         = InPort ( Bits4 )

    s.reg_en_M         = InPort ( Bits1 )
    s.wb_result_sel_M  = InPort ( Bits2 )

    s.reg_en_W         = InPort ( Bits1 )
    s.rf_waddr_W       = InPort ( Bits5 )
    s.rf_wen_W         = InPort ( Bits1 )

    # Status signals (dpath->Ctrl)

    s.inst_D           = OutPort( Bits32 )
    s.ne_X             = OutPort( Bits1 )

    #---------------------------------------------------------------------
    # F stage
    #---------------------------------------------------------------------

    s.pc_F        = Wire( Bits32 )
    s.pc_plus4_F  = Wire( Bits32 )

    # PC+4 incrementer

    s.pc_incr_F = Incrementer( Bits32, amount=4 )(
      in_ = s.pc_F,
      out = s.pc_plus4_F,
    )

    # forward delaration for branch target and jal target

    s.br_target_X  = Wire( Bits32 )

    # PC sel mux

    s.pc_sel_mux_F = Mux( Bits32, 2 )(
      in_ = { 0: s.pc_plus4_F, 1: s.br_target_X },
      sel = s.pc_sel_F,
      out = s.imemreq_addr,
    )

    # PC register

    s.pc_reg_F = RegEnRst( Bits32, reset_value=c_reset_vector-4 )(
      en  = s.reg_en_F,
      in_ = s.pc_sel_mux_F.out,
      out = s.pc_F,
    )

    #---------------------------------------------------------------------
    # D stage
    #---------------------------------------------------------------------

    # PC reg in D stage
    # This value is basically passed from F stage for the corresponding
    # instruction to use, e.g. branch to (PC+imm)

    s.pc_reg_D = m = RegEnRst( Bits32 )( en = s.reg_en_D, in_ = s.pc_F )

    # Instruction reg

    s.inst_D_reg = m = RegEnRst( Bits32, reset_value=c_reset_inst )(
      en  = s.reg_en_D,
      in_ = s.imemresp_data,
      out = s.inst_D # to ctrl
    )

    # Register File
    # The rf_rdata_D wires, albeit redundant in some sense, are used to
    # remind people these data are from D stage.

    s.rf_rdata0_D = Wire( Bits32 )
    s.rf_rdata1_D = Wire( Bits32 )

    s.rf_wdata_W  = Wire( Bits32 )

    s.rf = RegisterFile( Bits32, nregs=32, rd_ports=2, wr_ports=1, const_zero=True )(
      raddr = { 0: s.inst_D[ RS1 ],
                1: s.inst_D[ RS2 ], },
      rdata = { 0: s.rf_rdata0_D,
                1: s.rf_rdata1_D, },
      wen   = { 0: s.rf_wen_W },
      waddr = { 0: s.rf_waddr_W },
      wdata = { 0: s.rf_wdata_W },
    )

    # Immediate generator

    s.immgen_D = ImmGenRTL()( imm_type = s.imm_type_D, inst = s.inst_D )

    s.bypass_X = Wire( Bits32 )
    s.bypass_M = Wire( Bits32 )
    s.bypass_W = Wire( Bits32 )

    # op1 bypass mux

    s.op1_byp_mux_D = Mux( Bits32, 4 )(
      in_ = { 0: s.rf_rdata0_D,
              1: s.bypass_X,
              2: s.bypass_M,
              3: s.bypass_W, },
      sel = s.op1_byp_sel_D,
    )

    # op2 bypass mux

    s.op2_byp_mux_D = Mux( Bits32, 4 )(
      in_ = { 0: s.rf_rdata1_D,
              1: s.bypass_X,
              2: s.bypass_M,
              3: s.bypass_W, },
      sel = s.op2_byp_sel_D,
    )

    # op2 sel mux
    # This mux chooses among RS2, imm, and the mngr2proc.
    # Basically we are using two muxes here for pedagogy.

    s.op2_sel_mux_D = Mux( Bits32, 3 )(
      in_ = { 0: s.op2_byp_mux_D.out,
              1: s.immgen_D.imm,
              2: s.mngr2proc_data, },
      sel = s.op2_sel_D,
    )

    # Risc-V always calcs branch target by adding imm(generated above) to PC

    s.pc_plus_imm_D = Adder( Bits32 )(
      in0 = s.pc_reg_D.out,
      in1 = s.immgen_D.imm,
    )

    #---------------------------------------------------------------------
    # X stage
    #---------------------------------------------------------------------

    # br_target_reg_X
    # Since branches are resolved in X stage, we register the target,
    # which is already calculated in D stage, to X stage.

    s.br_target_reg_X = RegEnRst( Bits32, reset_value=0 )(
      en  = s.reg_en_X,
      in_ = s.pc_plus_imm_D.out,
      out = s.br_target_X,
    )

    # op1 reg

    s.op1_reg_X = RegEnRst( Bits32, reset_value=0 )(
      en  = s.reg_en_X,
      in_ = s.op1_byp_mux_D.out,
    )

    # op2 reg

    s.op2_reg_X = m = RegEnRst( Bits32, reset_value=0 )(
      en  = s.reg_en_X,
      in_ = s.op2_sel_mux_D.out,
    )

    # Send out xcelreq msg
    s.xcelreq_data //= s.op1_reg_X.out
    s.xcelreq_addr //= s.op2_reg_X.out[0:5]

    # store data reg
    # Since the op1 is the base address and op2 is the immediate so that
    # we could utilize ALU to do address calculation, we need one more
    # register to hold the R[rs2] we want to store to memory.

    s.store_reg_X = RegEnRst( Bits32, reset_value=0 )(
      en  = s.reg_en_X,
      in_ = s.op2_byp_mux_D.out, # R[rs2]
      out = s.dmemreq_data,
    )

    # ALU

    s.alu_X = AluRTL()(
      in0     = s.op1_reg_X.out,
      in1     = s.op2_reg_X.out,
      fn      = s.alu_fn_X,
      ops_ne  = s.ne_X,
      out     = ( s.bypass_X, s.dmemreq_addr )
    )

    #---------------------------------------------------------------------
    # M stage
    #---------------------------------------------------------------------

    # Alu execution result reg

    s.ex_result_reg_M = m = RegEnRst( Bits32, reset_value=0 )(
      en  = s.reg_en_M,
      in_ = s.alu_X.out
    )

    # Writeback result selection mux

    s.wb_result_sel_mux_M = Mux( Bits32, 3 )(
      in_ = { 0: s.ex_result_reg_M.out,
              1: s.dmemresp_data,
              2: s.xcelresp_data, },
      sel = s.wb_result_sel_M,
      out = s.bypass_M,
    )

    #---------------------------------------------------------------------
    # W stage
    #---------------------------------------------------------------------

    # Writeback result reg

    s.wb_result_reg_W = RegEnRst( Bits32, reset_value=0 )(
      en  = s.reg_en_W,
      in_ = s.wb_result_sel_mux_M.out,
      out = ( s.bypass_W, s.rf_wdata_W, s.proc2mngr_data ),
    )
