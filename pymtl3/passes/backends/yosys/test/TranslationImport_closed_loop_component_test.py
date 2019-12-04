#=========================================================================
# TranslationImport_closed_loop_component_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 6, 2019
"""Closed-loop test cases for translation-import with component."""

from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.test.TranslationImport_closed_loop_component_test import (
    test_adder,
    test_index_static,
    test_mux,
    test_nested_struct,
    test_struct,
    test_subcomp,
)
from pymtl3.passes.sverilog.util.test_utility import closed_loop_component_test


def local_do_test( m ):
  closed_loop_component_test( m, m._data, "yosys" )
