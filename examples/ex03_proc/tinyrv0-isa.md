
TinyRV0 Instruction Set Architecture
==========================================================================

 - Author : Christopher Batten, Shunning Jiang
 - Date   : June 14, 2019

The TinyRV0 ISA is a (tiny) subset of the full 32-bit RISC-V RV32IZicsr
ISA. TinyRV0 includes just 10 instructions and mainly suitable for
illustrative and teaching purposes. This document provides a compact
description of the TinyRV0 ISA, but it should be read in combination with
the full RISC-V ISA manuals.

### Table of Contents

 - Architectural State
 - TinyRV0 Instruction Overview
 - TinyRV0 Instruction Encoding
 - TinyRV0 Instruction Details
 - TinyRV0 Privileged ISA

Architectural State
--------------------------------------------------------------------------

### Data Formats

TinyRV0 only supports 4B signed and unsigned integer values. There are no
byte nor half-word values and no floating-point.

### General Purpose Registers

There are 31 general-purpose registers x1-x31 (called x registers),
which hold integer values. Register x0 is hardwired to the constant
zero. Each register is 32 bits wide. TinyRV0 uses the same calling
convention and symbolic register names as RISC-V:

### Memory

TinyRV0 only supports a 1MB virtual memory address space from 0x00000000
to 0x000fffff. The result of memory accesses to addresses larger than
0x000fffff are undefined.

A key feature of any ISA is identifying the endianness of the memory
system. Endianness specifies if we load a word in memory, what order
should those bytes appear in the destination register. Assume the letter
A ia at byte address 0x0, the letter B is at byte address 0x1, the letter
C is at byte address 0x2, and the letter D is at byte address 0x3. If we
laod a four-byte word from address 0x0, there are two options: the
destination register can either hold 0xABCD (big endian) or 0xDCBA
(little endian). There is no significant benefit of one system over the
other. TinyRV0 uses a little endian memory system.

TinyRV0 ISA Overview
--------------------------------------------------------------------------

Here is a brief list of the instructions which make the TinyRV0 ISA.

 - CSRR, CSRW (`proc2mngr`, `mngr2proc`, `xcelregXX`)
 - ADD, SLL, SRL, AND, ADDI
 - LW, SW
 - BNE

CSSR and CSRW are pseudo-instructions in the full RV32IZicsr ISA for
specific usage of the CSRRW and CSRRS instructions. The full CSRRW and
CSRRS instructions are rather complicated and we don't actually need any
functionality beyond what CSSR and CSRW provide. So TinyRV0 only includes
the CSSR and CSRW pseudo-instruction. Here is the mapping between the
TinyRV0 and RV32IZicsr instructions:

    csrr rd, csr  == csrrs rd, csr, x0
    csrw csr, rs1 == csrrw x0, csr, rs1

TinyRV0 Instruction and Immediate Encoding
--------------------------------------------------------------------------

The TinyRV0 ISA uses the same instruction encoding as RISC-V. There are
four instruction types and five immediate encodings. Each instruction has
a specific instruction type, and if that instruction includes an
immediate, then it will also have an immediate type.

### R-type

     31        25 24     20 19     15 14  12 11      7 6           0
    +------------+---------+---------+------+---------+-------------+
    | funct7     | rs2     | rs1     |funct3| rd      | opcode      |
    +------------+---------+---------+------+---------+-------------+

### I-type

     31                  20 19     15 14  12 11      7 6           0
    +----------------------+---------+------+---------+-------------+
    | imm                  | rs1     |funct3| rd      | opcode      |
    +----------------------+---------+------+---------+-------------+

### S-type

     31        25 24     20 19     15 14  12 11      7 6           0
    +------------+---------+---------+------+---------+-------------+
    | imm        | rs2     | rs1     |funct3| imm     | opcode      |
    +------------+---------+---------+------+---------+-------------+

RISC-V has an asymmetric immediate encoding which means that the
immediates are formed by concatenating different bits in an asymmetric
order based on the specific immediate formats. Note that in RISC-V all
immediates are always sign extended, and the sign-bit for the immediate
is always in bit 31 of the instruction.

The following diagrams illustrate how to create a 32-bit immediate from
each of the five immediate formats. The fields are labeled with the
instruction bits used to construct their value. `<-- n` is used to
indicate repeating bit n of the instruction to fill that field and `z` is
used to indicate a bit which is always set to zero.

### I-immediate

     31                                        10        5 4     1  0
    +-----------------------------------------+-----------+-------+--+
    |                                  <-- 31 | 30:25     | 24:21 |20|
    +-----------------------------------------+-----------+-------+--+

### S-immediate

     31                                        10        5 4     1  0
    +-----------------------------------------+-----------+-------+--+
    |                                  <-- 31 | 30:25     | 11:8  |7 |
    +-----------------------------------------+-----------+-------+--+

### B-immediate

     31                                  12 11 10        5 4     1  0
    +--------------------------------------+--+-----------+-------+--+
    |                               <-- 31 |7 | 30:25     | 11:8  |z |
    +--------------------------------------+--+-----------+-------+--+

TinyRV0 Instruction Details
--------------------------------------------------------------------------

For each instruction we include a brief summary, assembly syntax,
instruction semantics, instruction and immediate encoding format, and the
actual encoding for the instruction. We use the following conventions
when specifying the instruction semantics:

 - R[rx]      : general-purpose register value for register specifier rx
 - CSR[src]   : control/status register value for register specifier csr
 - sext       : sign extend to 32 bits
 - M_4B[addr] : 4-byte memory value at address addr
 - PC         : current program counter
 - imm        : immediate according to the immediate type

Unless otherwise specified assume instruction updates PC with PC+4.

### CSRR

    - Summary   : Move value in control/status register to GPR
    - Assembly  : csrr rd, csr
    - Semantics : R[rd] = CSR[csr]
    - Format    : I-type, I-immediate

     31                  20 19     15 14  12 11      7 6           0
    +----------------------+---------+------+---------+-------------+
    | csr                  | rs1     | 010  | rd      | 1110011     |
    +----------------------+---------+------+---------+-------------+

The control/status register read instruction is used to read a CSR and
write the result to a GPR. The CSRs supported in TinyRV0 are listed in
Section 5. Note that in RISC-V CSRR is really a pseudo-instruction for a
specific usage of CSRRS, but in TinyRV0 we only support the subset of
CSRRS captured by CSRR.

### CSRW

    - Summary   : Move value in GPR to control/status register
    - Assembly  : csrw csr, rs1
    - Semantics : CSR[csr] = R[rs1]
    - Format    : I-type, I-immediate

     31                  20 19     15 14  12 11      7 6           0
    +----------------------+---------+------+---------+-------------+
    | csr                  | rs1     | 001  | rd      | 1110011     |
    +----------------------+---------+------+---------+-------------+

The control/status register write instruction is used to read a GPR and
write the result to a CSR. The CSRs supported in TinyRV0 are listed in
Section 5. Note that in RISC-V CSRW is really a pseudo-instruction for a
specific usage of CSRRW, but in TinyRV0 we only support the subset of
CSRRW captured by CSRW.

### ADD

    - Summary   : Addition with 3 GPRs, no overflow exception
    - Assembly  : add rd, rs1, rs2
    - Semantics : R[rd] = R[rs1] + R[rs2]
    - Format    : R-type

     31        25 24     20 19     15 14  12 11      7 6           0
    +------------+---------+---------+------+---------+-------------+
    | 0000000    | rs2     | rs1     | 000  | rd      | 0110011     |
    +------------+---------+---------+------+---------+-------------+

### AND

    - Summary   : Bitwise logical AND with 3 GPRs
    - Assembly  : and rd, rs1, rs2
    - Semantics : R[rd] = R[rs1] & R[rs2]
    - Format    : R-type

     31        25 24     20 19     15 14  12 11      7 6           0
    +------------+---------+---------+------+---------+-------------+
    | 0000000    | rs2     | rs1     | 111  | rd      | 0110011     |
    +------------+---------+---------+------+---------+-------------+

### SLL

    - Summary   : Shift left logical by register value (append zeroes)
    - Assembly  : sll rd, rs1, rs2
    - Semantics : R[rd] = R[rs1] << R[rs2][4:0]
    - Format    : R-type

     31        25 24     20 19     15 14  12 11      7 6           0
    +------------+---------+---------+------+---------+-------------+
    | 0000000    | rs2     | rs1     | 001  | rd      | 0110011     |
    +------------+---------+---------+------+---------+-------------+

Note that the hardware should append zeros to the right as it does the
left shift. The hardware _must_ only use the bottom five bits of R[rs2]
when performing the shift.

### SRL

    - Summary   : Shift right logical by register value (append zeroes)
    - Assembly  : srl rd, rs1, rs2
    - Semantics : R[rd] = R[rs1] >> R[rs2][4:0]
    - Format    : R-type

     31        25 24     20 19     15 14  12 11      7 6           0
    +------------+---------+---------+------+---------+-------------+
    | 0000000    | rs2     | rs1     | 101  | rd      | 0110011     |
    +------------+---------+---------+------+---------+-------------+

Note that the hardware should append zeros to the left as it does the
right shift. The hardware _must_ only use the bottom five bits of R[rs2]
when performing the shift.

### ADDI

    - Summary   : Add constant, no overflow exception
    - Assembly  : addi rd, rs1, imm
    - Semantics : R[rd] = R[rs1] + sext(imm)
    - Format    : I-type, I-immediate

     31                  20 19     15 14  12 11      7 6           0
    +----------------------+---------+------+---------+-------------+
    | imm                  | rs1     | 000  | rd      | 0010011     |
    +----------------------+---------+------+---------+-------------+

### LW

    - Summary   : Load word from memory
    - Assembly  : lw rd, imm(rs1)
    - Semantics : R[rd] = M_4B[ R[rs1] + sext(imm) ]
    - Format    : I-type, I-immediate

     31                  20 19     15 14  12 11      7 6           0
    +----------------------+---------+------+---------+-------------+
    | imm                  | rs1     | 010  | rd      | 0000011     |
    +----------------------+---------+------+---------+-------------+

All addresses used with LW instructions must be four-byte aligned. This
means the bottom two bits of every effective address (i.e., after the
base address is added to the offset) will always be zero. The semantics
of unaligned addresses is undefined.

### SW

    - Summary   : Store word into memory
    - Assembly  : sw rs2, imm(rs1)
    - Semantics : M_4B[ R[rs1] + sext(imm) ] = R[rs2]
    - Format    : S-type, S-immediate

     31        25 24     20 19     15 14  12 11      7 6           0
    +------------+---------+---------+------+---------+-------------+
    | imm        | rs2     | rs1     | 010  | imm     | 0100011     |
    +------------+---------+---------+------+---------+-------------+

All addresses used with SW instructions must be four-byte aligned. This
means the bottom two bits of every effective address (i.e., after the
base address is added to the offset) will always be zero. The semantics
of unaligned addresses is undefined.

### BNE

    - Summary   : Branch if 2 GPRs are not equal
    - Assembly  : bne rs1, rs2, imm
    - Semantics : PC = ( R[rs1] != R[rs2] ) ? PC + sext(imm) : PC + 4
    - Format    : S-type, B-immediate

     31        25 24     20 19     15 14  12 11      7 6           0
    +------------+---------+---------+------+---------+-------------+
    | imm        | rs2     | rs1     | 001  | imm     | 1100011     |
    +------------+---------+---------+------+---------+-------------+

TinyRV0 Privileged ISA
--------------------------------------------------------------------------

TinyRV0 does not support any kind of distinction between user and
privileged mode. Using the terminology in the RISC-V vol 2 ISA manual,
TinyRV0 only supports M-mode.

### Reset Vector

RISC-V specifies two potential reset vectors: one at a low address, and
one at a high address. TinyRV0 uses the low address reset vector at
0x00000200. This is where assembly tests should reside as well as user
code in TinyRV0.

### Control/Status Registers

RISC-V includes two non-standard CSRs for communication between the
processor and a manager (primarily used for testing) and 32 . Here is the mapping:

    CSR Name    Privilege  Read/Write  CSR Num
    ------------------------------------------
    proc2mngr   M          RW          0x7C0
    mngr2proc   M          R           0xFC0
    xcelreg01   M          RW          0x7e0
    xcelreg02   M          RW          0x7e1
    ...
    xcelreg03   M          RW          0x7ff

These are chosen to conform to the guidelines in Section 2.1 of the
RISC-V vol 2 ISA manual. Here is a description of each of the CSRs.

 - `mngr2proc` (0xFC0): Used to communicate data from the manager to the
   processor. This register has register-mapped FIFO-dequeue semantics
   meaning reading the register essentially dequeues the data from the
   head of a FIFO. Reading the register will stall if the FIFO has no
   valid data. Writing the register is undefined.

 - `proc2mngr` (0x7c0): Used to communicate data from the processor to the
   manager. This register has register-mapped FIFO-enqueue semantics
   meaning writing the register essentially enqueues the data on the tail
   of a FIFO. Writing the register will stall if the FIFO is not ready.
   Reading the register is undefined.

 - `xcelregXX` (0x7e0-0x7ff): Used to communicate data to/from the
   processor and an accelerator. The exact semantics of each register is
   specific to each accelerator.

### Address Translation

TinyRV0 only supports the most basic form of address translation. Every
logical address is directly mapped to the corresponding physical address.
As mentioned above, TinyRV0 only supports a 1MB virtual memory address
space from 0x00000000 to 0x000fffff, and thus TinyRV0 only supports a 1MB
physical memory address space. In the RISC-V vol 2 ISA manual this is
called a Mbare addressing environment.

