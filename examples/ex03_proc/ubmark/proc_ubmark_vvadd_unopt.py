#========================================================================
# ubmark-vvadd-unopt: vector-vector addition kernel
#========================================================================
#
# This code does adds the values of two arrays and stores the result to
# the destination array. The code is equivalent to:
#
# void vvadd( int *dest, int *src0, int *src1, int size ) {
#   for ( int i = 0; i < size; i++ )
#     *dest++ = *src0++ + *src1++;
# }

import struct

from examples.ex03_proc.SparseMemoryImage import SparseMemoryImage, mk_section
from examples.ex03_proc.tinyrv0_encoding import assemble
from .proc_ubmark_vvadd_data import ref, src0, src1
from pymtl3 import *

c_vvadd_src0_ptr = 0x2000;
c_vvadd_src1_ptr = 0x3000;
c_vvadd_dest_ptr = 0x4000;
c_vvadd_size     = 100;

class ubmark_vvadd_unopt:

  # verification function, argument is a bytearray from TestMemory instance

  @staticmethod
  def verify( memory ):

    is_pass      = True
    first_failed = -1

    for i in range(c_vvadd_size):
      x = struct.unpack('i', memory[c_vvadd_dest_ptr + i * 4 : c_vvadd_dest_ptr + (i+1) * 4] )[0]
      if not ( x == ref[i] ):
        is_pass     = False
        first_faild = i
        print( " [ failed ] dest[{i}]: {x} != ref[{i}]: {ref} ".format( i=i, x=x, ref=ref[i] ) )
        return False

    if is_pass:
      print( " [ passed ]: vvadd-unopt" )
      return True

  @staticmethod
  def gen_mem_image():

    # text section

    text = \
           """
           # load array pointers
           csrr  x1, mngr2proc < 100
           csrr  x2, mngr2proc < 0x2000
           csrr  x3, mngr2proc < 0x3000
           csrr  x4, mngr2proc < 0x4000
           add   x5, x0, x1

         loop:
           lw    x6, 0(x2)
           lw    x7, 0(x3)
           add   x8, x6, x7
           sw    x8, 0(x4)
           addi  x2, x2, 4
           addi  x3, x3, 4
           addi  x4, x4, 4
           addi  x5, x5, -1
           bne   x5, x0, loop

           # end of the program
           csrw  proc2mngr, x0 > 0
           nop
           nop
           nop
           nop
           nop
           nop
           """

    mem_image = assemble( text )

    # load data by manually create data sections using binutils

    src0_section = mk_section( ".data", c_vvadd_src0_ptr, src0 )
    src1_section = mk_section( ".data", c_vvadd_src1_ptr, src1 )

    # load data

    mem_image.add_section( src0_section )
    mem_image.add_section( src1_section )

    return mem_image
