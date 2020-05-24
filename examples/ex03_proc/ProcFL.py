"""
==========================================================================
ProcFL
==========================================================================
TinyRV0 FL proc.

Author : Shunning Jiang
  Date : June 14, 2019
"""

from pymtl3 import *
from pymtl3.stdlib.ifcs import GetIfcFL, SendIfcFL, XcelMasterIfcFL, mk_xcel_msg
from pymtl3.stdlib.mem import MemMasterIfcFL

from .tinyrv0_encoding import RegisterFile, TinyRV0Inst, disassemble_inst


class ProcFL( Component ):

  def construct( s ):

    # Interface, Buffers to hold request/response messages

    s.commit_inst = OutPort( Bits1 )

    s.imem = MemMasterIfcFL()
    s.dmem = MemMasterIfcFL()
    s.xcel = XcelMasterIfcFL()

    s.proc2mngr = SendIfcFL()
    s.mngr2proc = GetIfcFL()

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
        s.raw_inst = s.imem.read( s.PC, 4 ) # line trace

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
          s.dmem.write( addr, 4, s.R[inst.rs2] )
          s.PC += 4
        elif inst_name == "lw":
          addr = s.R[inst.rs1] + sext( inst.i_imm, 32 )
          s.R[inst.rd] = s.dmem.read( addr, 4 )
          s.PC += 4
        elif inst_name == "bne":
          if s.R[inst.rs1] != s.R[inst.rs2]:
            s.PC = s.PC + sext( inst.b_imm, 32 )
          else:
            s.PC += 4

        elif inst_name == "csrw":
          if   inst.csrnum == 0x7C0:
            s.proc2mngr( s.R[inst.rs1] )
          elif 0x7E0 <= inst.csrnum <= 0x7FF:
            s.xcel.write( inst.csrnum[0:5], s.R[inst.rs1] )
          else:
            raise TinyRV2Semantics.IllegalInstruction(
              "Unrecognized CSR register ({}) for csrw at PC={}" \
                .format(inst.csrnum.uint(),s.PC) )
          s.PC += 4

        elif inst_name == "csrr":
          if   inst.csrnum == 0xFC0:
            s.R[inst.rd] = s.mngr2proc()
          elif 0x7E0 <= inst.csrnum <= 0x7FF:
            s.R[inst.rd] = s.xcel.read( inst.csrnum[0:5] )
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
