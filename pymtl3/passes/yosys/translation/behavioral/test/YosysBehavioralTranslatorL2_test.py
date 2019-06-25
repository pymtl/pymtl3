#=========================================================================
# YosysBehavioralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Test the SystemVerilog translator implementation."""

from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.behavioral.test.SVBehavioralTranslatorL1_test import (
    is_sverilog_reserved,
)
from pymtl3.passes.sverilog.translation.behavioral.test.SVBehavioralTranslatorL2_test import (
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
    test_nested_if,
    test_reduce,
    test_tmpvar,
)

from ..YosysBehavioralTranslatorL2 import YosysBehavioralRTLIRToSVVisitorL2


def local_do_test( m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )

  visitor = YosysBehavioralRTLIRToSVVisitorL2(is_sverilog_reserved)
  upblks = m._pass_behavioral_rtlir_gen.rtlir_upblks
  m_all_upblks = m.get_update_blocks()
  for blk in m_all_upblks:
    upblk_src = visitor.enter( blk, upblks[blk] )
    upblk_src = "\n".join( upblk_src )
    assert upblk_src == m._ref_upblk_srcs_yosys[blk.__name__]
