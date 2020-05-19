#=========================================================================
# YosysBehavioralTranslatorL1_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 9, 2019
"""Test the YosysVerilog translator implementation."""

import pytest

from pymtl3.passes.backends.verilog.errors import VerilogTranslationError
from pymtl3.passes.backends.verilog.util.utility import verilog_reserved
from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl3.passes.rtlir.util.test_utility import expected_failure

from ....testcases import (
    CaseBits32BitSelUpblkComp,
    CaseBits32x2ConcatComp,
    CaseBits32x2ConcatConstComp,
    CaseBits32x2ConcatFreeVarComp,
    CaseBits32x2ConcatMixedComp,
    CaseBits32x2ConcatUnpackedSignalComp,
    CaseBits64PartSelUpblkComp,
    CaseBits64SextInComp,
    CaseBits64ZextInComp,
    CaseDefaultBitsComp,
    CasePassThroughComp,
    CasePythonClassAttr,
    CaseSequentialPassThroughComp,
    CaseVerilogReservedComp,
)
from ..YosysBehavioralTranslatorL1 import YosysBehavioralRTLIRToVVisitorL1


def run_test( case, m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass( m ) )
  m.apply( BehavioralRTLIRTypeCheckPass( m ) )

  visitor = YosysBehavioralRTLIRToVVisitorL1(lambda x: x in verilog_reserved)
  upblks = m.get_metadata( BehavioralRTLIRGenPass.rtlir_upblks )
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
      CasePythonClassAttr,
      CaseDefaultBitsComp,
    ]
)
def test_yosys_behavioral_L1( case ):
  run_test( case, case.DUT() )

def test_yosys_reserved_keyword():
  with expected_failure( VerilogTranslationError, "reserved keyword" ):
    run_test( CaseVerilogReservedComp, CaseVerilogReservedComp.DUT() )
