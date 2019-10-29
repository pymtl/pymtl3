#=========================================================================
# sw
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
    csrr x2, mngr2proc < 0xdeadbeef
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    sw   x2, 0(x1)
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    lw   x3, 0(x1)
    csrw proc2mngr, x3 > 0xdeadbeef

    .data
    .word 0x01020304
  """

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

    asm_code.append( """

      csrr x1, mngr2proc < {src} # Move src value into register
      csrr x2, mngr2proc < {base} # Move base value into register

      # Instruction under test
      sw x1, {offset}(x2)

      # Check the result
      csrr x4, mngr2proc < {lw_base}
      lw   x3, 0(x4)
      csrw proc2mngr, x3 > {result}

      """.format(
        src     = result,
        lw_base = (base.uint() + offset.int()) & 0xfffffffc,
        offset  = offset.int(),
        base    = base.uint(),
        result  = result,
      )
    )

  # Generate some random data to initialize memory

  initial_data = []
  for i in range(128):
    initial_data.append( random.randint(0,0xffffffff) )

  # Add the data to the end of the assembly code

  asm_code.append( gen_word_data( initial_data ) )
  return asm_code
