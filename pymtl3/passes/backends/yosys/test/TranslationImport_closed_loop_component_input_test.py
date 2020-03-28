#=========================================================================
# TranslationImport_closed_loop_component_input_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 6, 2019
"""Closed-loop test cases for translation-import with component and input."""

from random import seed

from pymtl3.passes.backends.verilog.test.TranslationImport_closed_loop_component_input_test import (
    test_adder,
    test_mux,
)
from pymtl3.passes.backends.verilog.util.test_utility import (
    closed_loop_component_input_test,
)
from pymtl3.passes.rtlir.util.test_utility import do_test

seed( 0xdeadebeef )

def local_do_test( m ):
  closed_loop_component_input_test( m, m._tvs, m._tv_in, "yosys" )
