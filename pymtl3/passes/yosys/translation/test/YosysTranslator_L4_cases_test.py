#=========================================================================
# YosysTranslator_L4_cases_test.py
#=========================================================================
"""Test the yosys-SystemVerilog translator."""

import pytest

from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.structural.test.SVStructuralTranslatorL1_test import (
    check_eq,
)
from pymtl3.passes.sverilog.translation.test.SVTranslator_L4_cases_test import (
    test_sub_component_attr,
    test_subcomponent,
    test_subcomponent_index,
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
