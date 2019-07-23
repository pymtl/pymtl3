#=========================================================================
# TranslationImport_closed_loop_component_input_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 6, 2019
"""Closed-loop test cases for translation-import with component and input."""

from random import seed

from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.test.TranslationImport_closed_loop_component_input_test import (
    test_adder,
    test_mux,
)
from pymtl3.passes.sverilog.util.test_utility import closed_loop_component_input_test

seed( 0xdeadebeef )

def local_do_test( m ):
  test_vector = m._test_vector
  tv_in = m._tv_in
  closed_loop_component_input_test( m, test_vector, tv_in, "yosys" )
