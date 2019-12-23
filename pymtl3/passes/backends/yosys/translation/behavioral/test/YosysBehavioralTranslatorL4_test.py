#=========================================================================
# YosysBehavioralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Test the SystemVerilog translator implementation."""

import pytest

from pymtl3.passes.backends.sverilog.errors import SVerilogTranslationError
from pymtl3.passes.backends.sverilog.util.utility import sverilog_reserved
from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl3.passes.rtlir.util.test_utility import expected_failure

from ....testcases import (
    CaseArrayBits32IfcInUpblkComp,
    CaseConnectValRdyIfcUpblkComp,
    CaseInterfaceArrayNonStaticIndexComp,
)
from ..YosysBehavioralTranslatorL4 import YosysBehavioralRTLIRToSVVisitorL4


def run_test( case, m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )

  visitor = YosysBehavioralRTLIRToSVVisitorL4(lambda x: x in sverilog_reserved)
  upblks = m._pass_behavioral_rtlir_gen.rtlir_upblks
  m_all_upblks = m.get_update_blocks()
  assert len(m_all_upblks) == 1

  for blk in m_all_upblks:
    upblk_src = visitor.enter( blk, upblks[blk] )
    upblk_src = "\n".join( upblk_src )
    assert upblk_src + '\n' == case.REF_UPBLK

@pytest.mark.parametrize(
    'case', [
      CaseConnectValRdyIfcUpblkComp,
      CaseArrayBits32IfcInUpblkComp,
      CaseInterfaceArrayNonStaticIndexComp,
    ]
)
def test_yosys_behavioral_L4( case ):
  run_test( case, case.DUT() )
