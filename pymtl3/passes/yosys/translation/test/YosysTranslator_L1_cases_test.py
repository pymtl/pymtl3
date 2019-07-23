#=========================================================================
# YosysTranslator_L1_cases_test.py
#=========================================================================
"""Test the yosys-SystemVerilog translator."""

import pytest

from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.structural.test.SVStructuralTranslatorL1_test import (
    check_eq,
)
from pymtl3.passes.sverilog.translation.test.SVTranslator_L1_cases_test import (
    test_bit_selection,
    test_comb_assign,
    test_concat,
    test_concat_constants,
    test_concat_mixed,
    test_connect_constant,
    test_freevar,
    test_part_selection,
    test_port_bit_selection,
    test_port_const_accessed,
    test_port_const_array,
    test_port_const_unaccessed,
    test_port_part_selection,
    test_port_wire,
    test_port_wire_array_index,
    test_seq_assign,
    test_sext,
    test_unpacked_signal_index,
    test_zext,
)
from pymtl3.passes.yosys.translation.YosysTranslator import YosysTranslator


def local_do_test( m ):
  m.elaborate()
  tr = YosysTranslator( m )
  tr.translate( m )
  check_eq( tr.hierarchy.src, m._ref_src_yosys )
