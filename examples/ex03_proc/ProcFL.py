"""
==========================================================================
ProcFL
==========================================================================
TinyRV0 FL proc.

Author : Shunning Jiang, Peitian Pan
  Date : Sep 9, 2022
"""

from pymtl3 import *
from pymtl3.extra import clone_deepcopy
from pymtl3.stdlib.stream.ifcs import IStreamIfc, OStreamIfc
from pymtl3.stdlib.stream      import IStreamDeqAdapterFL, OStreamEnqAdapterFL
from pymtl3.stdlib.xcel.ifcs   import XcelRequesterIfc
from pymtl3.stdlib.xcel        import mk_xcel_msg, XcelRequesterAdapterFL
from pymtl3.stdlib.mem.ifcs    import MemRequesterIfc
from pymtl3.stdlib.mem         import mk_mem_msg, MemRequesterAdapterFL

from .tinyrv0_encoding import RegisterFile, TinyRV0Inst, disassemble_inst


class ProcFL( Component ):

  def construct( s ):

    req_class, resp_class = mk_mem_msg( 8, 32, 32 )
    xreq_class, xresp_class = mk_xcel_msg( 5, 32 )

    # Interface, Buffers to hold request/response messages

    s.commit_inst = OutPort( Bits1 )

    s.imem = MemRequesterIfc( req_class, resp_class )
    s.dmem = MemRequesterIfc( req_class, resp_class )
    s.xcel = XcelRequesterIfc( xreq_class, xresp_class )

    s.proc2mngr = OStreamIfc( Bits32 )
    s.mngr2proc = IStreamIfc( Bits32 )

    # Adapters to convert ports into callable methods

    s.imem_adapter = MemRequesterAdapterFL( req_class, resp_class )
    s.dmem_adapter = MemRequesterAdapterFL( req_class, resp_class )
    s.xcel_adapter = XcelRequesterAdapterFL( xreq_class, xresp_class )

    connect( s.imem, s.imem_adapter.requester )
    connect( s.dmem, s.dmem_adapter.requester )
    connect( s.xcel, s.xcel_adapter.requester )

    s.proc2mngr_q = OStreamEnqAdapterFL( Bits32 )
    s.mngr2proc_q = IStreamDeqAdapterFL( Bits32 )

    connect( s.mngr2proc, s.mngr2proc_q.istream )
    connect( s.proc2mngr_q.ostream, s.proc2mngr )

    # Internal data structures

    s.PC = b32( 0x200 )

    s.R = RegisterFile(32)
    s.raw_inst = None

    @update_once
    def up_ProcFL():
      if s.reset:
        s.PC = b32( 0x200 )
        return

      s.commit_inst @= 0

      try:
        s.raw_inst = s.imem_adapter.read( s.PC, 4 ) # line trace

        inst = TinyRV0Inst( s.raw_inst )
        inst_name = inst.name

        if   inst_name == "nop":
          s.PC += 4
        elif inst_name == "add":
          s.R[inst.rd] = s.R[inst.rs1] + s.R[inst.rs2]
          s.PC += 4
        elif inst_name == "sll":
          s.R[inst.rd] = s.R[inst.rs1] << (s.R[inst.rs2] & 0x1F)
          s.PC += 4
        elif inst_name == "srl":
          s.R[inst.rd] = s.R[inst.rs1] >> (s.R[inst.rs2].uint() & 0x1F)
          s.PC += 4

        # ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''
        # Implement instruction AND in FL processor
        # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
        #; Make an "elif" statement here to implement instruction AND
        #; that applies bit-wise "and" operator to rs1 and rs2 and stores
        #; the result to rd

        elif inst_name == "and":
          s.R[inst.rd] = s.R[inst.rs1] & s.R[inst.rs2]
          s.PC += 4

        # ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\

        elif inst_name == "addi":
          s.R[inst.rd] = s.R[inst.rs1] + sext( inst.i_imm, 32 )
          s.PC += 4
        elif inst_name == "sw":
          addr = s.R[inst.rs1] + sext( inst.s_imm, 32 )
          s.dmem_adapter.write( addr, 4, s.R[inst.rs2] )
          s.PC += 4
        elif inst_name == "lw":
          addr = s.R[inst.rs1] + sext( inst.i_imm, 32 )
          s.R[inst.rd] = s.dmem_adapter.read( addr, 4 )
          s.PC += 4
        elif inst_name == "bne":
          if s.R[inst.rs1] != s.R[inst.rs2]:
            s.PC = s.PC + sext( inst.b_imm, 32 )
          else:
            s.PC += 4

        elif inst_name == "csrw":
          if   inst.csrnum == 0x7C0:
            if not s.proc2mngr_q.enq.rdy():
              return
            s.proc2mngr_q.enq( s.R[inst.rs1] )
          elif 0x7E0 <= inst.csrnum <= 0x7FF:
            s.xcel_adapter.write( inst.csrnum[0:5], s.R[inst.rs1] )
          else:
            raise TinyRV2Semantics.IllegalInstruction(
              "Unrecognized CSR register ({}) for csrw at PC={}" \
                .format(inst.csrnum.uint(),s.PC) )
          s.PC += 4

        elif inst_name == "csrr":
          if   inst.csrnum == 0xFC0:
            if not s.mngr2proc_q.deq.rdy():
              return
            s.R[inst.rd] = s.mngr2proc_q.deq()
          elif 0x7E0 <= inst.csrnum <= 0x7FF:
            s.R[inst.rd] = s.xcel_adapter.read( inst.csrnum[0:5] )
          else:
            raise TinyRV2Semantics.IllegalInstruction(
              "Unrecognized CSR register ({}) for csrr at PC={}" \
                .format(inst.csrnum.uint(),s.PC) )

          s.PC += 4

      except:
        print( "Unexpected error at PC={:0>8s}!".format( str(s.PC) ) )
        raise

      s.commit_inst @= 1

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    if s.commit_inst:
      return "[{:0>8s} {: <24}]".format( str(s.PC), disassemble_inst( s.raw_inst ) )
    return "[{}]".format( "#".ljust(33) )
