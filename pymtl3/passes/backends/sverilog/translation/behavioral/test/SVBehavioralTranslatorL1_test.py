#=========================================================================
# SVBehavioralTranslatorL1_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 28, 2019
"""Test the SystemVerilog translator implementation."""

import pytest

from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl3.passes.rtlir.util.test_utility import expected_failure

from ..SVBehavioralTranslatorL1 import BehavioralRTLIRToSVVisitorL1
from ...SVTranslator import sverilog_reserved
from ....errors import SVerilogTranslationError
from ....testcases import CasePassThroughComp, CaseSequentialPassThroughComp, \
    CaseBits32x2ConcatComp, CaseBits32x2ConcatConstComp, CaseBits32x2ConcatMixedComp, \
    CaseBits64SextInComp, CaseBits64ZextInComp, CaseBits32x2ConcatFreeVarComp, \
    CaseBits32x2ConcatUnpackedSignalComp, CaseBits32BitSelUpblkComp, \
    CaseBits64PartSelUpblkComp, CaseSVerilogReservedComp


def is_sverilog_reserved( name ):
  return name in sverilog_reserved

def run_test( case, m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )

  visitor = BehavioralRTLIRToSVVisitorL1(is_sverilog_reserved)
  upblks = m._pass_behavioral_rtlir_gen.rtlir_upblks
  m_all_upblks = m.get_update_blocks()
  assert len(m_all_upblks) == 1

  for blk in m_all_upblks:
    upblk_src = visitor.enter( blk, upblks[blk] )
    upblk_src = "\n".join( upblk_src )
    assert upblk_src + '\n' == case.REF_UPBLK

@pytest.mark.parametrize(
    'case', [
      CasePassThroughComp,
      CaseSequentialPassThroughComp,
      CaseBits32x2ConcatComp,
      CaseBits32x2ConcatConstComp,
      CaseBits32x2ConcatMixedComp,
      CaseBits64SextInComp,
      CaseBits64ZextInComp,
      CaseBits32x2ConcatFreeVarComp,
      CaseBits32x2ConcatUnpackedSignalComp,
      CaseBits32BitSelUpblkComp,
      CaseBits64PartSelUpblkComp,
    ]
)
def test_sv_behavioral_L1( case ):
  run_test( case, case.DUT() )

def test_sverilog_reserved_keyword():
  with expected_failure( SVerilogTranslationError, "reserved keyword" ):
    run_test( CaseSVerilogReservedComp, CaseSVerilogReservedComp.DUT() )
