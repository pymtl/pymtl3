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
from pymtl3.passes.backends.verilog import *
from pymtl3.passes.tracing import *
from pymtl3.stdlib.test_utils.test_helpers import finalize_verilator

from .harness import asm_test, assemble

random.seed(0xdeadbeef)


#-------------------------------------------------------------------------
# ProcVRTL_Tests
#-------------------------------------------------------------------------
# It is as simple as inheriting from FL tests and overwriting the run_sim
# function to apply the translation and import pass.

from .ProcFL_test import ProcFL_Tests as BaseTests

@pytest.mark.usefixtures("cmdline_opts")
class ProcVRTL_Tests( BaseTests ):

  @classmethod
  def setup_class( cls ):
    cls.ProcType = ProcRTL

  def run_sim( s, th, gen_test ):

    vcd_file_name = s.__class__.cmdline_opts["dump_vcd"]
    max_cycles = s.__class__.cmdline_opts["max_cycles"] or 10000

    th.elaborate()

    # Assemble the program
    mem_image = assemble( gen_test() )

    # Load the program into memory
    th.load( mem_image )

    # Check command line arguments for vcd dumping
    if vcd_file_name:
      th.set_metadata( VcdGenerationPass.vcd_file_name, vcd_file_name )
      th.proc.set_metadata( VerilogVerilatorImportPass.vl_trace, True )
      th.proc.set_metadata( VerilogVerilatorImportPass.vl_trace_filename, vcd_file_name )

    # Translate the DUT and import it back in using the verilog backend.
    th.proc.set_metadata( VerilogTranslationImportPass.enable, True )

    th = VerilogTranslationImportPass()( th )

    # Create a simulator and run simulation
    th.apply( DefaultPassGroup(linetrace=True) )
    th.sim_reset()

    while not th.done() and th.sim_cycle_count() < max_cycles:
      th.sim_tick()

    # Force a test failure if we timed out
    assert th.sim_cycle_count() < max_cycles

    finalize_verilator( th )

#-------------------------------------------------------------------------
# Test translation script
#-------------------------------------------------------------------------

def test_proc_translate():
  import os
  from os.path import dirname
  script_path = dirname(dirname(__file__)) + '/proc-translate'
  os.system(f'python {script_path}')


