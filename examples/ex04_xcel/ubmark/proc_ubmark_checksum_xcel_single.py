#========================================================================
# ubmark-checksum-xcel single iteration
#========================================================================


from examples.ex03_proc.SparseMemoryImage import SparseMemoryImage, mk_section
from examples.ex03_proc.tinyrv0_encoding import assemble
from pymtl3 import *


class ubmark_cksum_xcel_single:

  # verification function, argument is a bytearray from TestMemory instance

  @staticmethod
  def gen_mem_image():

    # text section

    text = """
        # load array pointers
        csrr  x1, mngr2proc < 0xff00f000
        csrr  x2, mngr2proc < 0x20001000
        csrr  x3, mngr2proc < 0x60005000
        csrr  x4, mngr2proc < 0x80007000
        addi  x5, x0, 1

        csrw  0x7E0, x1
        csrw  0x7E1, x2
        csrw  0x7E2, x3
        csrw  0x7E3, x4
        csrw  0x7E4, x5

        csrr  x1, 0x7E5
        csrw  proc2mngr, x1 > 0x3900bf00

    """

    mem_image = assemble( text )

    return mem_image
