"""
==========================================================================
ProcCL.py
==========================================================================
TinyRV0 CL proc.

Author : Shunning Jiang
  Date : June 14, 2019
"""
from enum import Enum

from pymtl3 import *
from pymtl3.stdlib.delays import DelayPipeDeqCL
from pymtl3.stdlib.queues import PipeQueueCL
from pymtl3.stdlib.mem import MemMsgType, mk_mem_msg, MemMasterIfcCL
from pymtl3.stdlib.ifcs import XcelMsgType, mk_xcel_msg,  XcelMasterIfcCL

from .tinyrv0_encoding import RegisterFile, TinyRV0Inst, disassemble_inst


class DXM_W(Enum):
  mem   = 1
  xcel  = 2
  arith = 3
  mngr  = 4

class PipelineStatus(Enum):
  idle  = 0
  stall = 1
  work  = 2

class ProcCL( Component ):

  def construct( s ):

    memreq_cls, memresp_cls = mk_mem_msg( 8,32,32 )
    xreq_class, xresp_class = mk_xcel_msg(5,32)

    # Interface

    s.commit_inst = OutPort( Bits1 )

    s.imem = MemMasterIfcCL( memreq_cls, memresp_cls )
    s.dmem = MemMasterIfcCL( memreq_cls, memresp_cls )

    s.xcel = XcelMasterIfcCL( xreq_class, xresp_class )

    s.proc2mngr = CallerIfcCL()
    s.mngr2proc = CalleeIfcCL()

    # Buffers to hold input messages

    s.imemresp_q  = DelayPipeDeqCL(0)
    s.imemresp_q.enq //= s.imem.resp

    s.dmemresp_q  = DelayPipeDeqCL(1)
    s.dmemresp_q.enq //= s.dmem.resp

    s.mngr2proc_q = DelayPipeDeqCL(1)
    s.mngr2proc_q.enq //= s.mngr2proc

    s.xcelresp_q  = DelayPipeDeqCL(0)
    s.xcelresp_q.enq //= s.xcel.resp

    s.pc = b32( 0x200 )
    s.R  = RegisterFile( 32 )

    s.F_DXM_queue = PipeQueueCL(1)
    s.DXM_W_queue = PipeQueueCL(1)

    s.F_status   = PipelineStatus.idle
    s.DXM_status = PipelineStatus.idle
    s.W_status   = PipelineStatus.idle

    @update_once
    def F():
      s.F_status = PipelineStatus.idle

      if s.reset:
        s.pc = b32( 0x200 )
        return

      if s.imem.req.rdy() and s.F_DXM_queue.enq.rdy():
        if s.redirected_pc_DXM >= 0:
          s.imem.req( memreq_cls( MemMsgType.READ, 0, s.redirected_pc_DXM ) )
          s.pc = s.redirected_pc_DXM
          s.redirected_pc_DXM = -1
        else:
          s.imem.req( memreq_cls( MemMsgType.READ, 0, s.pc ) )

        s.F_DXM_queue.enq( s.pc )
        s.F_status = PipelineStatus.work
        s.pc += 4
      else:
        s.F_status = PipelineStatus.stall

    s.redirected_pc_DXM = -1

    s.raw_inst = b32(0)

    @update_once
    def DXM():
      s.DXM_status = PipelineStatus.idle

      if s.redirected_pc_DXM >= 0:
        s.DXM_status = PipelineStatus.stall

      elif s.F_DXM_queue.deq.rdy() and s.imemresp_q.deq.rdy():

        if not s.DXM_W_queue.enq.rdy():
          s.DXM_status = PipelineStatus.stall
        else:
          pc = s.F_DXM_queue.peek()

          s.raw_inst = s.imemresp_q.peek().data
          inst       = TinyRV0Inst( s.raw_inst )
          inst_name  = inst.name

          s.DXM_status = PipelineStatus.work

          if inst_name == "nop":
            pass
          elif inst_name == "add":
            s.DXM_W_queue.enq( (inst.rd, s.R[ inst.rs1 ] + s.R[ inst.rs2 ], DXM_W.arith) )
          elif inst_name == "sll":
            s.DXM_W_queue.enq( (inst.rd, s.R[inst.rs1] << (s.R[inst.rs2] & 0x1F), DXM_W.arith) )
          elif inst_name == "srl":
            s.DXM_W_queue.enq( (inst.rd, s.R[inst.rs1] >> (s.R[inst.rs2].uint() & 0x1F), DXM_W.arith) )

          # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''
          # Implement instruction AND in CL processor
          # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
          #; Make an "elif" statement here to implement instruction AND
          #; that applies bit-wise "and" operator to rs1 and rs2 and
          #; pass the result to the pipeline.

          elif inst_name == "and":
            s.DXM_W_queue.enq( (inst.rd, s.R[inst.rs1] & s.R[inst.rs2], DXM_W.arith) )

          # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

          elif inst_name == "addi":
            s.DXM_W_queue.enq( (inst.rd, s.R[ inst.rs1 ] + sext(inst.i_imm, 32), DXM_W.arith) )
          elif inst_name == "sw":
            if s.dmem.req.rdy():
              s.dmem.req( memreq_cls( MemMsgType.WRITE, 0,
                                      s.R[ inst.rs1 ] + sext(inst.s_imm, 32),
                                      0,
                                      s.R[ inst.rs2 ] ) )
              s.DXM_W_queue.enq( (0, 0, DXM_W.mem) )
            else:
              s.DXM_status = PipelineStatus.stall

          elif inst_name == "lw":
            if s.dmem.req.rdy():
              s.dmem.req( memreq_cls( MemMsgType.READ, 0,
                                      s.R[ inst.rs1 ] + sext(inst.i_imm, 32),
                                      0 ) )
              s.DXM_W_queue.enq( (inst.rd, 0, DXM_W.mem) )
            else:
              s.DXM_status = PipelineStatus.stall

          elif inst_name == "bne":
            if s.R[ inst.rs1 ] != s.R[ inst.rs2 ]:
              s.redirected_pc_DXM = pc + sext(inst.b_imm, 32)
            s.DXM_W_queue.enq( None )

          elif inst_name == "csrw":
            if inst.csrnum == 0x7C0: # CSR: proc2mngr
              # We execute csrw in W stage
              s.DXM_W_queue.enq( (0, s.R[ inst.rs1 ], DXM_W.mngr) )

            elif 0x7E0 <= inst.csrnum <= 0x7FF:
              if s.xcel.req.rdy():
                s.xcel.req( xreq_class( XcelMsgType.WRITE, inst.csrnum[0:5], s.R[inst.rs1]) )
                s.DXM_W_queue.enq( (0, 0, DXM_W.xcel) )
              else:
                s.DXM_status = PipelineStatus.stall
          elif inst_name == "csrr":
            if inst.csrnum == 0xFC0: # CSR: mngr2proc
              if s.mngr2proc_q.deq.rdy():
                s.DXM_W_queue.enq( (inst.rd, s.mngr2proc_q.deq(), DXM_W.arith) )
              else:
                s.DXM_status = PipelineStatus.stall
            elif 0x7E0 <= inst.csrnum <= 0x7FF:
              if s.xcel.req.rdy():
                s.xcel.req( xreq_class( XcelMsgType.READ, inst.csrnum[0:5], s.R[inst.rs1]) )
                s.DXM_W_queue.enq( (inst.rd, 0, DXM_W.xcel) )
              else:
                s.DXM_status = PipelineStatus.stall

          # If we execute any instruction, we pop from queues
          if s.DXM_status == PipelineStatus.work:
            s.F_DXM_queue.deq()
            s.imemresp_q.deq()

    s.rd = b5(0)

    @update_once
    def W():
      s.rd = b5(0)
      s.commit_inst @= 0
      s.W_status = PipelineStatus.idle

      if s.DXM_W_queue.deq.rdy():
        entry = s.DXM_W_queue.peek()
        if entry is not None:
          rd, data, entry_type = entry
          s.rd = rd

          if entry_type == DXM_W.mem:
            if s.dmemresp_q.deq.rdy():
              if rd > 0: # load
                s.R[ rd ] = Bits32( s.dmemresp_q.deq().data )
              else: # store
                s.dmemresp_q.deq()

              s.W_status = PipelineStatus.work

            else:
              s.W_status = PipelineStatus.stall

          elif entry_type == DXM_W.xcel:
            if s.xcelresp_q.deq.rdy():
              if rd > 0: # csrr
                s.R[ rd ] = Bits32( s.xcelresp_q.deq().data )
              else: # csrw
                s.xcelresp_q.deq()

              s.W_status = PipelineStatus.work
            else:
              s.W_status = PipelineStatus.stall

          elif entry_type == DXM_W.mngr:
            if s.proc2mngr.rdy():
              s.proc2mngr( data )
              s.W_status = PipelineStatus.work
            else:
              s.W_status = PipelineStatus.stall

          else: # other WB insts
            assert entry_type == DXM_W.arith
            if rd > 0: s.R[ rd ] = Bits32( data )
            s.W_status = PipelineStatus.work

        else: # non-WB insts
          s.W_status = PipelineStatus.work

      if s.W_status == PipelineStatus.work:
        s.DXM_W_queue.deq()
        s.commit_inst @= 1

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    F_line_trace = " "
    if s.F_status == PipelineStatus.work:
      F_line_trace = str(s.pc)
    elif s.F_status == PipelineStatus.stall:
      F_line_trace = "#"

    DXM_line_trace = " "
    if s.DXM_status == PipelineStatus.work:
      DXM_line_trace = disassemble_inst(s.raw_inst)
    elif s.DXM_status == PipelineStatus.stall:
      DXM_line_trace = "#"

    W_line_trace = " "
    if s.W_status == PipelineStatus.work:
      W_line_trace = "x{:2}".format(str(s.rd) if s.rd > 0 else "--")
    elif s.F_status == PipelineStatus.stall:
      W_line_trace = "#"

    return "[{:<8s}|{:<23s}|{:<3s}]".format( F_line_trace, DXM_line_trace, W_line_trace )
