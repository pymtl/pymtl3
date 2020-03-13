"""
========================================================================
 TinyRV0 Instruction Type
========================================================================
 Instruction types are similar to message types but are strictly used
 for communication within a TinyRV0-based processor. Instruction
 "messages" can be unpacked into the various fields as defined by the
 TinyRV0 ISA, as well as be constructed from specifying each field
 explicitly. The 32-bit instruction has different fields depending on
 the format of the instruction used. The following are the various
 instruction encoding formats used in the TinyRV0 ISA.

  31          25 24   20 19   15 14    12 11          7 6      0
 | funct7       | rs2   | rs1   | funct3 | rd          | opcode |  R-type
 | imm[11:0]            | rs1   | funct3 | rd          | opcode |  I-type, I-imm
 | imm[11:5]    | rs2   | rs1   | funct3 | imm[4:0]    | opcode |  S-type, S-imm
 | imm[12|10:5] | rs2   | rs1   | funct3 | imm[4:1|11] | opcode |  S-type, B-imm


Author : Shunning Jiang
  Date : June 14, 2019
"""

from pymtl3 import *

#-------------------------------------------------------------------------
# TinyRV0 Instruction Fields
#-------------------------------------------------------------------------

OPCODE = slice(  0,  7 )
FUNCT3 = slice( 12, 15 )
FUNCT7 = slice( 25 ,32 )

RD     = slice(  7, 12 )
RS1    = slice( 15, 20 )
RS2    = slice( 20, 25 )
SHAMT  = slice( 20, 25 )

I_IMM  = slice( 20, 32 )
CSRNUM = slice( 20, 32 )

S_IMM0 = slice(  7, 12 )
S_IMM1 = slice( 25, 32 )

B_IMM0 = slice(  8, 12 )
B_IMM1 = slice( 25, 31 )
B_IMM2 = slice(  7,  8 )
B_IMM3 = slice( 31, 32 )

#-------------------------------------------------------------------------
# TinyRV0 Instruction Definitions
#-------------------------------------------------------------------------

NOP   =  b8(0)  # 00000000000000000000000000000000
LW    =  b8(3)  # ?????????????????010?????0000011
SW    =  b8(8)  # ?????????????????010?????0100011
SLL   =  b8(9)  # 0000000??????????001?????0110011
SRL   =  b8(11) # 0000000??????????101?????0110011
ADD   =  b8(15) # 0000000??????????000?????0110011
ADDI  =  b8(16) # ?????????????????000?????0010011
AND   =  b8(24) # 0000000??????????111?????0110011
BNE   =  b8(31) # ?????????????????001?????1100011
CSRR  =  b8(46) # ????????????00000010?????1110011
CSRW  =  b8(47) # ?????????????????001000001110011
# CSRRX for accelerator
CSRRX =  b8(36) # 0111111?????00000010?????1110011

# ZERO inst
ZERO  =  b8(51)

#-------------------------------------------------------------------------
# TinyRV0 Instruction Disassembler
#-------------------------------------------------------------------------

inst_dict = {
  NOP   : "nop",
  LW    : "lw",
  SW    : "sw",
  SLL   : "sll",
  SRL   : "srl",
  ADD   : "add",
  ADDI  : "addi",
  AND   : "and",
  BNE   : "bne",
  CSRR  : "csrr",
  CSRW  : "csrw",
  CSRRX : "csrrx",
  ZERO  : "????",
}

#-------------------------------------------------------------------------
# CSR registers
#-------------------------------------------------------------------------

# R/W
CSR_PROC2MNGR = b12(0x7C0)

# R/O
CSR_MNGR2PROC = b12(0xFC0)

#-----------------------------------------------------------------------
# DecodeInstType
#-----------------------------------------------------------------------
# TinyRV0 Instruction Type Decoder

class DecodeInstType( Component ):

  # Interface

  def construct( s ):

    s.in_ = InPort ( Bits32 )
    s.out = OutPort( Bits8 )

    @update
    def comb_logic():

      s.out @= ZERO

      if   s.in_ == 0b10011:                 s.out @= NOP
      elif s.in_[OPCODE] == 0b0110011:
        if   s.in_[FUNCT3] == 0b000:     s.out @= ADD
        elif s.in_[FUNCT3] == 0b001:     s.out @= SLL
        elif s.in_[FUNCT3] == 0b111:     s.out @= AND
        elif s.in_[FUNCT3] == 0b101:     s.out @= SRL

      elif s.in_[OPCODE] == 0b0010011:
        if   s.in_[FUNCT3] == 0b000:       s.out @= ADDI

      elif s.in_[OPCODE] == 0b0100011:
        if s.in_[FUNCT3] == 0b010:       s.out @= SW

      elif s.in_[OPCODE] == 0b0000011:
        if s.in_[FUNCT3] == 0b010:       s.out @= LW

      elif s.in_[OPCODE] == 0b1100011:
        if s.in_[FUNCT3] == 0b001:       s.out @= BNE

      elif s.in_[OPCODE] == 0b1110011:
        if   s.in_[FUNCT3] == 0b001:       s.out @= CSRW

        elif s.in_[FUNCT3] == 0b010:
          if s.in_[FUNCT7] == 0b0111111:   s.out @= CSRRX
          else:                                s.out @= CSRR
