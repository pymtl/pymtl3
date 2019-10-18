"""
==========================================================================
ubmark-checksum-rolling: a modified fletcher checksum algorithm.
==========================================================================
This code computes a checksum of a sequence of 16-bit integers.

void cksum_rolling( int *dest, int *src, int size ) {
  int idx = 0;
  int sum1 = 0, sum2 = 0;
  int sum1_prev = 0, sum2_prev = 0;
  for ( int i = 0; i < size; i+=6 ){
    sum1 = sum1_prev & 0xffff;
    sum2 = sum1 & 0xffff;
    sum1 = ( sum1 + sum2_prev ) & 0xffff;
    sum2 = ( sum2 + sum1 ) & 0xffff;
    for ( int j = 0; j < 6; j++ ){
      sum1 = ( sum1 + src[i+j] ) & 0xffff;
      sum2 = ( sum2 + sum1 ) & 0xffff;
    }
    sum1_prev = sum1;
    sum2_prev = sum2;
  }
  *dest = ( sum2 << 16 ) | sum1;

Author : Yanghui Ou
  Date : June 18, 2019
"""

import struct

from examples.ex03_proc.SparseMemoryImage import SparseMemoryImage, mk_section
from examples.ex03_proc.tinyrv0_encoding import assemble
from .proc_ubmark_cksum_roll_data import dataset_size, mask, ref, src
from pymtl3 import *

c_cksum_src_ptr = 0x2000;
c_cksum_msk_ptr = 0x3000;
c_cksum_dst_ptr = 0x4000;
c_cksum_size    = dataset_size;

class ubmark_cksum_roll:

  # verification function, argument is a bytearray from TestMemory instance

  @staticmethod
  def verify( memory ):

    is_pass      = True
    first_failed = -1

    for i in range(1):
      x = struct.unpack('i', memory[c_cksum_dst_ptr + i * 4 : c_cksum_dst_ptr + (i+1) * 4] )[0]
      if not ( b32(x) == b32(ref[i]) ):
        is_pass     = False
        first_faild = i
        print( " [ failed ] dest[{i}]: {x} != ref[{i}]: {ref} ".format( i=i, x=hex(x), ref=hex(ref[i]) ) )
        return False

    if is_pass:
      print( " [ passed ]: cksum-null" )
      return True

  @staticmethod
  def gen_mem_image():

    # text section

    text =( """
        # load array pointers
        csrr  x1,  mngr2proc < {}     # size
        csrr  x2,  mngr2proc < 0x2000 # src pointer
        csrr  x3,  mngr2proc < 0x3000 # mask pointer
        csrr  x4,  mngr2proc < 0x4000 # dst pointer

        addi  x5,  x0,  16        # shift amount
        lw    x6,  0(x3)          # mask = 0xffff
        add   x7,  x0,  x0        # sum1 = 0
        add   x8,  x0,  x0        # sum2 = 0
        add   x9,  x0,  x0        # sum1_prev = 0
        add   x10, x0,  x0        # sum2_prev = 0

      loop_i:
        and   x7,  x9,  x6        # sum1 = sum1_prev & 0xffff
        and   x8,  x7,  x6        # sum2 = sum1 & 0xffff
        add   x7,  x7,  x10       # sum1 += sum2_prev
        and   x7,  x7,  x6        # sum1 &= 0xffff
        add   x8,  x8,  x7        # sum2 += sum1
        and   x8,  x8,  x6        # sum2 &= 0xffff
        addi  x11, x0,  3         # j = 3

      loop_j:
        lw    x12, 0(x2)          # load 2 16-bit ints
        and   x13, x12, x6        # src[i+j] = word & 0xffff
        srl   x12, x12, x5        # src[i+j+1] = word >> 16

        add   x7,  x7,  x13       # sum1 += src[i+j]
        and   x7,  x7,  x6        # sum1 &= 0xffff
        add   x8,  x8,  x7        # sum2 += sum1
        and   x8,  x8,  x6        # sum2 &= 0xffff

        add   x7,  x7,  x12       # sum1 += src[i+j+1]
        and   x7,  x7,  x6        # sum1 &= 0xffff
        add   x8,  x8,  x7        # sum2 += sum1
        and   x8,  x8,  x6        # sum2 &= 0xffff

        addi  x2,  x2,  4         # increment word address
        addi  x11, x11, -1        # decrement loop counter
        bne   x11, x0,  loop_j

        add   x9,  x0,  x7        # sum1_prev = sum1
        add   x10, x0,  x8        # sum2_prev = sum2

        addi  x1,  x1,  -6        # decrement loop counter i
        bne   x1,  x0,  loop_i
        
        add   x14, x0,  x8        # ret = sum2
        sll   x14, x14, x5        # ret = sum2 << 16
        add   x14, x14, x7        # ret |= sum1
        sw    x14, 0(x4)

        # End of program
        csrw  proc2mngr, x0 > 0
        nop
        nop
        nop
        nop
        nop
        nop
    """.format( c_cksum_size ) )

    mem_image = assemble( text )

    # load data by manually create data sections using binutils

    src_section = mk_section( ".data", c_cksum_src_ptr, src )
    msk_section = mk_section( ".data", c_cksum_msk_ptr, mask )

    # load data

    mem_image.add_section( src_section )
    mem_image.add_section( msk_section )

    return mem_image
