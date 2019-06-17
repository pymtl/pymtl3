"""
==========================================================================
 ProcCL.py
==========================================================================
TinyRV0 CL proc

Author : Shunning Jiang
  Date : June 14, 2019
"""
from collections import deque
from enum import Enum

from pymtl3      import *

from pymtl3.stdlib.ifcs import mk_mem_msg, MemMsgType
from pymtl3.stdlib.ifcs.mem_ifcs  import MemMasterIfcCL, MemMasterIfcFL
from pymtl3.stdlib.ifcs.xcel_ifcs import XcelMasterIfcCL
from pymtl3.stdlib.ifcs.XcelMsg   import mk_xcel_msg, XcelMsgType
from pymtl3.stdlib.cl.queues import BypassQueueCL, PipeQueueCL
from pymtl3.stdlib.cl.DelayPipeCL import DelayPipeDeqCL

from tinyrv0_encoding import RegisterFile, TinyRV0Inst

class ProcCL( Component ):

  def construct( s ):

    memreq_cls, memresp_cls = mk_mem_msg( 8,32,32 )
    xreq_class, xresp_class = mk_xcel_msg(5,32)

    # Interface

    s.commit_inst = OutPort( Bits1 )

    s.imem = MemMasterIfcCL( memreq_cls, memresp_cls )
    s.dmem = MemMasterIfcCL( memreq_cls, memresp_cls )

    s.xcel = XcelMasterIfcCL( xreq_class, xresp_class )

    s.proc2mngr = NonBlockingCallerIfc()
    s.mngr2proc = NonBlockingCalleeIfc()

    # Buffers to hold input messages

    s.imemresp_q  = DelayPipeDeqCL(0)( enq = s.imem.resp )
    s.dmemresp_q  = DelayPipeDeqCL(1)( enq = s.dmem.resp )
    s.mngr2proc_q = DelayPipeDeqCL(1)( enq = s.mngr2proc )
    s.xcelresp_q  = DelayPipeDeqCL(1)( enq = s.xcel.resp )

    s.pc = Bits32( 0x200 )
    s.R  = RegisterFile( 32 )

    s.F_DXM_queue = PipeQueueCL(1)
    s.DXM_W_queue = PipeQueueCL(1)

    s.F_line_trace = " "*5
    s.DXM_line_trace = " "*5
    s.W_line_trace = " "*3

    class DXM_W(Enum):
      mem   = 1
      xcel  = 2
      arith = 3
      mngr  = 4

    @s.update
    def F():
      s.F_line_trace = "     "
      if s.imem.req.rdy() and s.F_DXM_queue.enq.rdy():
        if s.redirected_pc_DXM >= 0:
          s.imem.req( memreq_cls( MemMsgType.READ, 0, s.redirected_pc_DXM ) )
          s.pc = s.redirected_pc_DXM
        else:
          s.imem.req( memreq_cls( MemMsgType.READ, 0, s.pc ) )

        s.F_DXM_queue.enq( s.pc )
        s.F_line_trace = "{:5}".format( hex(int(s.pc)) )
        s.pc += 4

    s.redirected_pc_DXM = -1

    @s.update
    def DXM():
      s.redirected_pc_DXM = -1
      s.DXM_line_trace = "     "

      if s.F_DXM_queue.deq.rdy() and s.DXM_W_queue.enq.rdy():
        if not s.imemresp_q.deq.rdy():
          s.DXM_line_trace = "#    "
        else:
          pc   = s.F_DXM_queue.peek()
          raw_inst = s.imemresp_q.peek().data

          inst = TinyRV0Inst( raw_inst )

          inst_name = inst.name

          executed = True

          if inst_name == "nop":
            pass
          elif inst_name == "add":
            s.DXM_W_queue.enq( (inst.rd, s.R[ inst.rs1 ] + s.R[ inst.rs2 ], DXM_W.arith) )
          elif inst_name == "sll":
            s.DXM_W_queue.enq( (inst.rd, s.R[inst.rs1] << (s.R[inst.rs2] & 0x1F), DXM_W.arith) )
          elif inst_name == "srl":
            s.DXM_W_queue.enq( (inst.rd, s.R[inst.rs1] >> (s.R[inst.rs2].uint() & 0x1F), DXM_W.arith) )
          elif inst_name == "and":
            s.DXM_W_queue.enq( (inst.rd, s.R[inst.rs1] & s.R[inst.rs2], DXM_W.arith) )
          elif inst_name == "addi":
            s.DXM_W_queue.enq( (inst.rd, s.R[ inst.rs1 ] + inst.i_imm.int(), DXM_W.arith) )
          elif inst_name == "sw":
            if s.dmem.req.rdy():
              s.dmem.req( memreq_cls( MemMsgType.WRITE, 0,
                                      s.R[ inst.rs1 ] + inst.s_imm.int(),
                                      0,
                                      s.R[ inst.rs2 ] ) )
              s.DXM_W_queue.enq( (0, 0, DXM_W.mem) )
            else:
              executed = False
          elif inst_name == "lw":
            if s.dmem.req.rdy():
              s.dmem.req( memreq_cls( MemMsgType.READ, 0,
                                      s.R[ inst.rs1 ] + inst.i_imm.int(),
                                      0 ) )
              s.DXM_W_queue.enq( (inst.rd, 0, DXM_W.mem) )
            else:
              executed = False

          elif inst_name == "bne":
            if s.R[ inst.rs1 ] != s.R[ inst.rs2 ]:
              s.redirected_pc_DXM = pc + inst.b_imm.int()
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
                executed = False
          elif inst_name == "csrr":
            if inst.csrnum == 0xFC0: # CSR: mngr2proc
              if s.mngr2proc_q.deq.rdy():
                s.DXM_W_queue.enq( (inst.rd, s.mngr2proc_q.deq(), DXM_W.arith) )
              else:
                executed = False
            elif 0x7E0 <= inst.csrnum <= 0x7FF:
              if s.xcel.req.rdy():
                s.xcel.req( xreq_class( XcelMsgType.READ, inst.csrnum[0:5], s.R[inst.rs1]) )
                s.DXM_W_queue.enq( (inst.rd, 0, DXM_W.xcel) )
              else:
                executed = False

          # If we execute any instruction, we pop from queues
          if executed:
            s.F_DXM_queue.deq()
            s.imemresp_q.deq()
            s.DXM_line_trace = "{:5}".format( inst_name )

    @s.update
    def W():
      s.commit_inst = Bits1(0)
      s.W_line_trace = "   "

      if s.DXM_W_queue.deq.rdy():
        entry = s.DXM_W_queue.peek()
        if entry is not None:
          rd, data, entry_type = entry

          if entry_type == DXM_W.mem:
            if s.dmemresp_q.deq.rdy():
              if rd > 0: # load
                s.R[ rd ] = Bits32( s.dmemresp_q.deq().data )
                s.W_line_trace = "x{:02}".format( int(rd) )
              else: # store
                s.dmemresp_q.deq()
                s.W_line_trace = "x--"
            else:
              s.W_line_trace = "#  "

          elif entry_type == DXM_W.xcel:
            if s.xcelresp_q.deq.rdy():
              if rd > 0: # csrr
                s.R[ rd ] = Bits32( s.xcelresp_q.deq().data )
                s.W_line_trace = "x{:02}".format( int(rd) )
              else: # csrw
                s.xcelresp_q.deq()
                s.W_line_trace = "x--"
            else:
              s.W_line_trace = "#  "

          elif entry_type == DXM_W.mngr:
            if s.proc2mngr.rdy():
              s.proc2mngr( data )
              s.W_line_trace = "x--"
            else:
              s.W_line_trace = "#  "

          else: # other WB insts
            assert entry_type == DXM_W.arith
            if rd > 0: s.R[ rd ] = Bits32( data )
            s.W_line_trace = "x{:02}".format( int(rd) )

        else: # non-WB insts
          s.W_line_trace = "x--"

      if s.W_line_trace[0] != " " and s.W_line_trace[0] != "#":
        s.DXM_W_queue.deq()
        s.commit_inst = Bits1(1)

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    return "{}|{}|{}".format( s.F_line_trace, s.DXM_line_trace, s.W_line_trace )
