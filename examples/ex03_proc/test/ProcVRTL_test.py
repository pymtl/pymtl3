"""
=========================================================================
ProcVRTL_test.py
=========================================================================
Includes test cases for the translated TinyRV0 processor.

Author : Shunning Jiang, Yanghui Ou
  Date : June 15, 2019
"""
import random

import pytest

from examples.ex03_proc.ProcRTL import ProcRTL
from pymtl3 import *

from .harness import asm_test, assemble

random.seed(0xdeadbeef)


#-------------------------------------------------------------------------
# ProcVRTL_Tests
#-------------------------------------------------------------------------
# It is as simple as inheriting from RTL tests and overwrite [run_sim]
# function to apply the translation and import pass.

from .ProcRTL_test import ProcRTL_Tests as BaseTests

class ProcVRTL_Tests( BaseTests ):

  def run_sim( s, th, gen_test, max_cycles=10000 ):

    th.elaborate()

    # Assemble the program
    mem_image = assemble( gen_test() )

    # Load the program into memory
    th.load( mem_image )

    # Translate the processor and import it back in
    from pymtl3.passes.backends.yosys import TranslationImportPass
    th.proc.set_metadata( TranslationImportPass.enable, True )
    th = TranslationImportPass()( th )

    # Create a simulator and run simulation
    th.apply( SimulationPass(print_line_trace=True) )
    th.sim_reset()

    while not th.done() and th.sim_cycle_count() < max_cycles:
      th.sim_tick()

    # Force a test failure if we timed out
    assert th.sim_cycle_count() < max_cycles

#-------------------------------------------------------------------------
# Test translation script
#-------------------------------------------------------------------------

def test_proc_translate():
  import os
  from os.path import dirname
  script_path = dirname(dirname(__file__)) + '/proc-translate'
  os.system(f'python {script_path}')
