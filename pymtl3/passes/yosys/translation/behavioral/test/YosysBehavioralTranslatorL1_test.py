#=========================================================================
# YosysBehavioralTranslatorL1_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Test the SystemVerilog translator implementation."""

from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.behavioral.test.SVBehavioralTranslatorL1_test import (
    is_sverilog_reserved,
    test_bit_selection,
    test_comb_assign,
    test_concat,
    test_concat_constants,
    test_concat_mixed,
    test_freevar,
    test_part_selection,
    test_seq_assign,
    test_sext,
    test_sub_component_attr,
    test_sverilog_reserved_keyword,
    test_unpacked_signal_index,
    test_zext,
)

from ..YosysBehavioralTranslatorL1 import YosysBehavioralRTLIRToSVVisitorL1


def local_do_test( m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )

  visitor = YosysBehavioralRTLIRToSVVisitorL1(is_sverilog_reserved)
  upblks = m._pass_behavioral_rtlir_gen.rtlir_upblks
  m_all_upblks = m.get_update_blocks()
  for blk in m_all_upblks:
    upblk_src = visitor.enter( blk, upblks[blk] )
    upblk_src = "\n".join( upblk_src )
    assert upblk_src == m._ref_upblk_srcs_yosys[blk.__name__]
