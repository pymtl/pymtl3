#=========================================================================
# YosysBehavioralTranslatorL5_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Test the SystemVerilog translator implementation."""

from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.behavioral.test.SVBehavioralTranslatorL1_test import (
    is_sverilog_reserved,
)
from pymtl3.passes.sverilog.translation.behavioral.test.SVBehavioralTranslatorL5_test import (
    test_subcomponent,
    test_subcomponent_index,
)

from ..YosysBehavioralTranslatorL5 import YosysBehavioralRTLIRToSVVisitorL5


def local_do_test( m ):
  visitor = YosysBehavioralRTLIRToSVVisitorL5(is_sverilog_reserved)
  for comp, _all_upblks in m._ref_upblk_srcs_yosys.items():
    comp.apply( BehavioralRTLIRGenPass() )
    comp.apply( BehavioralRTLIRTypeCheckPass() )
    upblks = comp._pass_behavioral_rtlir_gen.rtlir_upblks
    m_all_upblks = comp.get_update_blocks()
    for blk in m_all_upblks:
      upblk_src = visitor.enter( blk, upblks[blk] )
      upblk_src = "\n".join( upblk_src )
      assert upblk_src == _all_upblks[blk.__name__]
