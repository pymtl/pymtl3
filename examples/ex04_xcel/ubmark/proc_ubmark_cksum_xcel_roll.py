"""
==========================================================================
ubmark-checksum-xcel-rolling: a modified fletcher checksum algorithm.
==========================================================================
This code computes a checksum of a sequence of 16-bit integers using the
checksum accelerator.

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
from examples.ex03_proc.ubmark.proc_ubmark_cksum_roll_data import (
    dataset_size,
    mask,
    ref,
    src,
)
from pymtl3 import *

c_cksum_src_ptr = 0x2000;
c_cksum_msk_ptr = 0x3000;
c_cksum_dst_ptr = 0x4000;
c_cksum_size    = dataset_size;

class ubmark_cksum_xcel_roll:

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
      print( " [ passed ]: cksum-xcel" )
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
        addi  x11, x0,  1         # Go bit 
        add   x7,  x0,  x0        # cksum = 0

      loop_i:
        lw    x8,  0(x2)          # load first 32-bit word
        lw    x9,  4(x2)          # load second 32-bit word
        lw    x10, 8(x2)          # load third 32-bit word

        # transfer data to accelerator

        csrw  0x7E0, x7
        csrw  0x7E1, x8
        csrw  0x7E2, x9
        csrw  0x7E3, x10
        csrw  0x7E4, x11
        
        # read back the result
        csrr  x7, 0x7E5

        addi  x2,  x2,  12        # increment word address
        addi  x1,  x1,  -6        # decrement loop counter i
        bne   x1,  x0,  loop_i

        sw    x7, 0(x4)

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
