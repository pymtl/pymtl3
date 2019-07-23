#=========================================================================
# YosysBehavioralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Test the SystemVerilog translator implementation."""

from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.errors import SVerilogTranslationError
from pymtl3.passes.sverilog.translation.behavioral.test.SVBehavioralTranslatorL1_test import (
    is_sverilog_reserved,
)
from pymtl3.passes.sverilog.translation.behavioral.test.SVBehavioralTranslatorL3_test import (
    test_nested_struct,
    test_packed_array_behavioral,
    test_struct,
)

from ..YosysBehavioralTranslatorL3 import YosysBehavioralRTLIRToSVVisitorL3


def local_do_test( m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )

  try:
    visitor = YosysBehavioralRTLIRToSVVisitorL3(is_sverilog_reserved)
    upblks = m._pass_behavioral_rtlir_gen.rtlir_upblks
    m_all_upblks = m.get_update_blocks()
    for blk in m_all_upblks:
      upblk_src = visitor.enter( blk, upblks[blk] )
      upblk_src = "\n".join( upblk_src )
      assert upblk_src == m._ref_upblk_srcs_yosys[blk.__name__]
  except SVerilogTranslationError:
    if m._ref_upblk_srcs_yosys is None:
      pass
    else:
      raise
