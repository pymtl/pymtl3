"""
=========================================================================
ProcRTL_test.py
=========================================================================
Includes test cases for the RTL TinyRV0 processor.

Author : Shunning Jiang, Yanghui Ou
  Date : June 12, 2019
"""
import random

import pytest

from examples.ex03_proc.ProcRTL import ProcRTL
from pymtl3 import *
from pymtl3.stdlib.test_utils import run_sim

from . import (
    inst_add,
    inst_addi,
    inst_and,
    inst_bne,
    inst_csr,
    inst_lw,
    inst_sll,
    inst_srl,
    inst_sw,
    inst_xcel,
)
from .harness import TestHarness, asm_test, assemble

random.seed(0xdeadbeef)


#-------------------------------------------------------------------------
# ProcRTL_Tests
#-------------------------------------------------------------------------
# It is as simple as inheriting from FL tests. No need to overwrite
# the [run_sim], since the version for ProcFL should work fine.

from .ProcFL_test import ProcFL_Tests as BaseTests

@pytest.mark.usefixtures("cmdline_opts")
class ProcRTL_Tests( BaseTests ):

  # [setup_class] will be called by pytest before running all the tests in
  # the test class. Here we specify the type of the processor that is used
  # in all test cases. We can easily reuse all these test cases in simply
  # by creating a new test class that inherits from this class and
  # overwrite the setup_class to provide a different processor type.
  @classmethod
  def setup_class( cls ):
    cls.ProcType = ProcRTL
