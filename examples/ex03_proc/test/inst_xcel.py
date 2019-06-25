#=========================================================================
# xcel
#=========================================================================


from pymtl3 import *

from .inst_utils import *

#-------------------------------------------------------------------------
# gen_basic_test
#-------------------------------------------------------------------------

def gen_basic_test():
  return """
    csrr x1, mngr2proc < 0xdeadbeef
    csrw 0x7E9, x1
    csrr x2, 0x7FF
    csrw proc2mngr, x2 > 0xdeadbeef
  """

def gen_multiple_test():
  return """
    csrr x1, mngr2proc < 0xdeadbee0
    csrw 0x7E0, x1
    csrr x2, 0x7FF
    csrw proc2mngr, x2 > 0xdeadbee0

    csrr x1, mngr2proc < 0xdeadbee1
    csrw 0x7E0, x1
    csrr x2, 0x7FF
    csrw proc2mngr, x2 > 0xdeadbee1

    csrr x1, mngr2proc < 0xdeadbee2
    csrw 0x7E0, x1
    csrr x2, 0x7FF
    csrw proc2mngr, x2 > 0xdeadbee2

    csrr x1, mngr2proc < 0xdeadbee2
    csrw 0x7E0, x1
    csrr x2, 0x7FF
    csrw proc2mngr, x2 > 0xdeadbee2

    csrr x1, mngr2proc < 0xdeadbee3
    csrw 0x7E0, x1
    csrr x2, 0x7FF
    csrw proc2mngr, x2 > 0xdeadbee3

    csrr x1, mngr2proc < 0xdeadbee4
    csrw 0x7E0, x1
    csrr x2, 0x7FF
    csrw proc2mngr, x2 > 0xdeadbee4

    csrr x1, mngr2proc < 0xdeadbee5
    csrw 0x7E0, x1
    csrr x2, 0x7FF
    csrw proc2mngr, x2 > 0xdeadbee5

    csrr x1, mngr2proc < 0xdeadbee6
    csrw 0x7E0, x1
    csrr x2, 0x7FF
    csrw proc2mngr, x2 > 0xdeadbee6
  """
