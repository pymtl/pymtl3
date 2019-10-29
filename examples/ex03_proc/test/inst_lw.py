#=========================================================================
# lw
#=========================================================================

import random

from pymtl3 import *

from .inst_utils import *

#-------------------------------------------------------------------------
# gen_basic_test
#-------------------------------------------------------------------------

def gen_basic_test():
  return """
    csrr x1, mngr2proc < 0x00002000
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    lw   x2, 0(x1)
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    csrw proc2mngr, x2 > 0x01020304

    .data
    .word 0x01020304
  """

#-------------------------------------------------------------------------
# gen_dest_dep_test
#-------------------------------------------------------------------------

def gen_dest_dep_test():
  return [

    gen_ld_dest_dep_test( 5, "lw", 0x2000, 0x00010203 ),
    gen_ld_dest_dep_test( 4, "lw", 0x2004, 0x04050607 ),
    gen_ld_dest_dep_test( 3, "lw", 0x2008, 0x08090a0b ),
    gen_ld_dest_dep_test( 2, "lw", 0x200c, 0x0c0d0e0f ),
    gen_ld_dest_dep_test( 1, "lw", 0x2010, 0x10111213 ),
    gen_ld_dest_dep_test( 0, "lw", 0x2014, 0x14151617 ),

    gen_word_data([
      0x00010203,
      0x04050607,
      0x08090a0b,
      0x0c0d0e0f,
      0x10111213,
      0x14151617,
    ])

  ]

#-------------------------------------------------------------------------
# gen_base_dep_test
#-------------------------------------------------------------------------

def gen_base_dep_test():
  return [

    gen_ld_base_dep_test( 5, "lw", 0x2000, 0x00010203 ),
    gen_ld_base_dep_test( 4, "lw", 0x2004, 0x04050607 ),
    gen_ld_base_dep_test( 3, "lw", 0x2008, 0x08090a0b ),
    gen_ld_base_dep_test( 2, "lw", 0x200c, 0x0c0d0e0f ),
    gen_ld_base_dep_test( 1, "lw", 0x2010, 0x10111213 ),
    gen_ld_base_dep_test( 0, "lw", 0x2014, 0x14151617 ),

    gen_word_data([
      0x00010203,
      0x04050607,
      0x08090a0b,
      0x0c0d0e0f,
      0x10111213,
      0x14151617,
    ])

  ]

#-------------------------------------------------------------------------
# gen_srcs_dest_test
#-------------------------------------------------------------------------

def gen_srcs_dest_test():
  return [
    gen_ld_base_eq_dest_test( "lw", 0x2000, 0x01020304 ),
    gen_word_data([ 0x01020304 ])
  ]

#-------------------------------------------------------------------------
# gen_value_test
#-------------------------------------------------------------------------

def gen_value_test():
  return [

    # Test positive offsets

    gen_ld_value_test( "lw",   0, 0x00002000, 0xdeadbeef ),
    gen_ld_value_test( "lw",   4, 0x00002000, 0x00010203 ),
    gen_ld_value_test( "lw",   8, 0x00002000, 0x04050607 ),
    gen_ld_value_test( "lw",  12, 0x00002000, 0x08090a0b ),
    gen_ld_value_test( "lw",  16, 0x00002000, 0x0c0d0e0f ),
    gen_ld_value_test( "lw",  20, 0x00002000, 0xcafecafe ),

    # Test negative offsets

    gen_ld_value_test( "lw", -20, 0x00002014, 0xdeadbeef ),
    gen_ld_value_test( "lw", -16, 0x00002014, 0x00010203 ),
    gen_ld_value_test( "lw", -12, 0x00002014, 0x04050607 ),
    gen_ld_value_test( "lw",  -8, 0x00002014, 0x08090a0b ),
    gen_ld_value_test( "lw",  -4, 0x00002014, 0x0c0d0e0f ),
    gen_ld_value_test( "lw",   0, 0x00002014, 0xcafecafe ),

    # Test positive offset with unaligned base

    gen_ld_value_test( "lw",   1, 0x00001fff, 0xdeadbeef ),
    gen_ld_value_test( "lw",   5, 0x00001fff, 0x00010203 ),
    gen_ld_value_test( "lw",   9, 0x00001fff, 0x04050607 ),
    gen_ld_value_test( "lw",  13, 0x00001fff, 0x08090a0b ),
    gen_ld_value_test( "lw",  17, 0x00001fff, 0x0c0d0e0f ),
    gen_ld_value_test( "lw",  21, 0x00001fff, 0xcafecafe ),

    # Test negative offset with unaligned base

    gen_ld_value_test( "lw", -21, 0x00002015, 0xdeadbeef ),
    gen_ld_value_test( "lw", -17, 0x00002015, 0x00010203 ),
    gen_ld_value_test( "lw", -13, 0x00002015, 0x04050607 ),
    gen_ld_value_test( "lw",  -9, 0x00002015, 0x08090a0b ),
    gen_ld_value_test( "lw",  -5, 0x00002015, 0x0c0d0e0f ),
    gen_ld_value_test( "lw",  -1, 0x00002015, 0xcafecafe ),

    gen_word_data([
      0xdeadbeef,
      0x00010203,
      0x04050607,
      0x08090a0b,
      0x0c0d0e0f,
      0xcafecafe,
    ])

  ]

#-------------------------------------------------------------------------
# gen_random_test
#-------------------------------------------------------------------------

def gen_random_test():

  # Generate some random data

  data = []
  for i in range(128):
    data.append( random.randint(0,0xffffffff) )

  # Generate random accesses to this data

  asm_code = []
  for i in range(50):

    a = random.randint(0,127)
    b = random.randint(0,127)

    base   = Bits32( 0x2000 + (4*b) )
    offset = Bits16( 4*(a - b) )
    result = data[a]

    asm_code.append( gen_ld_value_test( "lw", offset.int(), base.uint(), result ) )

  # Add the data to the end of the assembly code

  asm_code.append( gen_word_data( data ) )
  return asm_code
