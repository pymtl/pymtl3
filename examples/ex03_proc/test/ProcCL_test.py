"""
=========================================================================
 ProcCL_test.py
=========================================================================
 Includes a test harness that composes a processor, src/sink, and test
 memory, and a run_test function.

Author : Shunning Jiang, Yanghui Ou
  Date : June 12, 2019
"""
import pytest
import random
random.seed(0xdeadbeef)

from pymtl3  import *
from examples.ex03_proc.ProcCL import ProcCL
from ProcFL_test import ProcFL_Tests as BaseTests

#-------------------------------------------------------------------------
# ProcCL_Tests
#-------------------------------------------------------------------------
# It is as simple as inheriting from FL tests and change the ProcType to
# use.

class ProcCL_Tests( BaseTests ):

  @classmethod
  def setup_class( cls ):
    cls.ProcType = ProcCL

