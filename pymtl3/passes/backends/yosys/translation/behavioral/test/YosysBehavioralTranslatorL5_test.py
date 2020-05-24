#=========================================================================
# YosysBehavioralTranslatorL5_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Test the YosysVerilog translator implementation."""

import pytest

from pymtl3.passes.backends.verilog.util.utility import verilog_reserved
from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass

from ....testcases import (
    CaseBehavioralArraySubCompArrayStructIfcComp,
    CaseBits32ArraySubCompAttrUpblkComp,
    CaseBits32SubCompAttrUpblkComp,
)
from ..YosysBehavioralTranslatorL5 import YosysBehavioralRTLIRToVVisitorL5


def run_test( case, m ):
  m.elaborate()
  visitor = YosysBehavioralRTLIRToVVisitorL5(lambda x: x in verilog_reserved)

  m.apply( BehavioralRTLIRGenPass( m ) )
  m.apply( BehavioralRTLIRTypeCheckPass( m ) )
  upblks = m.get_metadata( BehavioralRTLIRGenPass.rtlir_upblks )
  m_all_upblks = m.get_update_blocks()
  assert len(m_all_upblks) == 1

  for blk in m_all_upblks:
    upblk_src = visitor.enter( blk, upblks[blk] )
    upblk_src = "\n".join( upblk_src )
    assert upblk_src + '\n' == case.REF_UPBLK

@pytest.mark.parametrize(
    'case', [
      CaseBits32SubCompAttrUpblkComp,
      CaseBits32ArraySubCompAttrUpblkComp,
      CaseBehavioralArraySubCompArrayStructIfcComp,
    ]
)
def test_yosys_behavioral_L5( case ):
  run_test( case, case.DUT() )
