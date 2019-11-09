"""
==========================================================================
ubmark-checksum-block: a modified fletcher checksum algorithm.
==========================================================================
This code computes checksum of an array of 16 byte blocks and stores
result to the destination array.

void cksum( int *dest, int *src0, int size ) {
  for ( int i = 0; i < size; i++ ){
    sum1 = 0;
    sum2 = 0;
    for ( int j = 0; j < 8; j++ ){
      sum1 = ( sum1 + src[i*8+j] ) & 0xffff;
      sum2 = ( sum2 + sum1 ) & 0xffff;
    }
    dest[i] = ( sum2 << 16 ) | sum1;
  }
Author : Yanghui Ou
  Date : June 11, 2019
"""

import struct

from examples.ex03_proc.SparseMemoryImage import SparseMemoryImage, mk_section
from examples.ex03_proc.tinyrv0_encoding import assemble
from .proc_ubmark_cksum_blk_data import dataset_size, mask, ref, src
from pymtl3 import *

c_cksum_src_ptr = 0x2000;
c_cksum_msk_ptr = 0x3000;
c_cksum_dst_ptr = 0x4000;
c_cksum_size    = dataset_size;
    
class ubmark_cksum_blk:

  # verification function, argument is a bytearray from TestMemory instance

  @staticmethod
  def verify( memory ):

    is_pass      = True
    first_failed = -1

    for i in range(c_cksum_size):
      x = struct.unpack('i', memory[c_cksum_dst_ptr + i * 4 : c_cksum_dst_ptr + (i+1) * 4] )[0]
      if not ( x == ref[i] ):
        is_pass     = False
        first_faild = i
        print( " [ failed ] dest[{i}]: {x} != ref[{i}]: {ref} ".format( i=i, x=hex(x), ref=hex(ref[i]) ) )
        return False

    if is_pass:
      print( " [ passed ]: cksum-blk" )
      return True

  @staticmethod
  def gen_mem_image():

    # text section

    text =( """
        # load array pointers
        csrr  x1,  mngr2proc < {}     # size
        csrr  x2,  mngr2proc < 0x2000 # src pointer
        csrr  x14, mngr2proc < 0x3000 # mask pointer
        csrr  x3,  mngr2proc < 0x4000 # dst pointer
        add   x4,  x0,  x1            # loop var i
        addi  x5,  x0,  16            # shift amount
        lw    x13, 0(x14)             # mask = 0xffff

      loop_i:
        add   x6,  x0,  x0 # sum1 = 0
        add   x7,  x0,  x0 # sum2 = 0
        addi  x10, x0,  4

      loop_j:
        lw    x8,  0(x2)          # load 2 16-bit ints
        and   x9,  x8,  x13       # src[j]
        srl   x8,  x8,  x5        # src[j+1]

        add   x6,  x6,  x9        # sum1 += src[j]
        and   x6,  x6,  x13       # sum1 &= 0xffff
        add   x7,  x7,  x6        # sum2 += sum1
        and   x7,  x7,  x13       # sum2 &= 0xffff

        add   x6,  x6,  x8        # sum1 += src[j+1]
        and   x6,  x6,  x13       # sum1 &= 0xffff
        add   x7,  x7,  x6        # sum2 += sum1
        and   x7,  x7,  x13       # sum2 &= 0xffff

        addi  x2,  x2,  4         # j+=2
        addi  x10, x10, -1        # decrement loop counter
        bne   x10, x0,  loop_j

        add   x11, x0,  x7        # ret = sum2
        sll   x11, x11, x5        # ret = ret << 16
        add   x11, x11, x6        # ret |= sum1
        sw    x11  0(x3)          # src[i] = ret
        addi  x3,  x3,  4
        addi  x4,  x4,  -1
        bne   x4,  x0,  loop_i

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
