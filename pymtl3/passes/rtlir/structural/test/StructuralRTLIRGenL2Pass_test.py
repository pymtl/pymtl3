#=========================================================================
# StructuralRTLIRGenL2Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the generation of level 2 structural RTLIR."""

from pymtl3.passes.rtlir.structural.StructuralRTLIRGenL2Pass import (
    StructuralRTLIRGenL2Pass,
)
from pymtl3.passes.rtlir.structural.StructuralRTLIRSignalExpr import *
from pymtl3.passes.testcases import (
    CaseConnectArrayStructAttrToOutComp,
    CaseConnectStructAttrToOutComp,
)

from .StructuralRTLIRGenL1Pass_test import gen_connections


def test_L2_struct_attr():
  a = CaseConnectStructAttrToOutComp.DUT()
  a.elaborate()
  a.apply( StructuralRTLIRGenL2Pass( gen_connections( a ) ) )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  assert ns.connections == \
    [(StructAttr(CurCompAttr(comp, 'in_'), 'foo'), CurCompAttr(comp, 'out'))]

def test_L2_packed_index():
  a = CaseConnectArrayStructAttrToOutComp.DUT()
  a.elaborate()
  a.apply( StructuralRTLIRGenL2Pass( gen_connections( a ) ) )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  assert ns.connections == \
    [(PackedIndex(StructAttr(CurCompAttr(comp, 'in_'), 'foo'), 1),
      CurCompAttr(comp, 'out'))]
