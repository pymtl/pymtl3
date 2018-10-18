#========================================================================
# UniqueModule_test.py
#========================================================================
# This file contains an expected failure test case for the translation
# and import pass. The verilator compiler should complain about the 
# duplicated definition of one module in the module hierarchy.

from pymtl import *
from pymtl.passes.test.trans_import.Verify import Verify

test_vector = [
      'in_      out1      out2', 
      [ 0,    0xffff,   0xffff],
      [ 1,    0xffff,   0xffff],
      [ 2,    0xffff,   0xffff],
    ]

def test_UniqueModule():

  Verify( 'UniqueModule', test_vector, 'normal' )

