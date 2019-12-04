#=========================================================================
# YosysTranslator_L2_cases_test.py
#=========================================================================
"""Test the yosys-SystemVerilog translator."""

import pytest

from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.structural.test.SVStructuralTranslatorL1_test import (
    check_eq,
)
from pymtl3.passes.sverilog.translation.test.SVTranslator_L2_cases_test import (
    test_for_range_lower_upper,
    test_for_range_lower_upper_step,
    test_for_range_upper,
    test_if,
    test_if_bool_op,
    test_if_branches,
    test_if_dangling_else_inner,
    test_if_dangling_else_outter,
    test_if_exp_for,
    test_if_exp_unary_op,
    test_lambda_connect,
    test_nested_if,
    test_nested_struct,
    test_nested_struct_port,
    test_packed_array,
    test_packed_array_concat,
    test_struct,
    test_struct_packed_array,
    test_struct_port,
    test_tmpvar,
)
from pymtl3.passes.yosys.translation.YosysTranslator import YosysTranslator


def trim( src ):
  lines = src.split( "\n" )
  ret = []
  for line in lines:
    if not line.startswith( "//" ):
      ret.append( line )
  return "\n".join( ret )

def local_do_test( m ):
  m.elaborate()
  tr = YosysTranslator( m )
  tr.translate( m )
  check_eq( tr.hierarchy.src, m._ref_src_yosys )
