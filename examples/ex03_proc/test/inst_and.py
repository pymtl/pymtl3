#=========================================================================
# and
#=========================================================================


from pymtl3 import *

from .inst_utils import *

#-------------------------------------------------------------------------
# gen_and_basic_test
#-------------------------------------------------------------------------

def gen_and_basic_test():
# ''' TUTORIAL TASK ''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Implement your own test for AND instruction
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''\/
#; Define a function named gen_and_basic_test that tests AND instruction
#:  return """
#:  """
  return """
    csrr x1, mngr2proc < 0x0f0f0f0f
    csrr x2, mngr2proc < 0x00ff00ff
    and x3, x1, x2
    csrw proc2mngr, x3 > 0x000f000f
  """

# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''/\
