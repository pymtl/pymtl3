#=========================================================================
# StructuralRTLIRGenL4Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the generation of level 1 structural RTLIR."""

from pymtl3.passes.rtlir.structural.StructuralRTLIRGenL4Pass import (
    StructuralRTLIRGenL4Pass,
)
from pymtl3.passes.rtlir.structural.StructuralRTLIRSignalExpr import *
from pymtl3.passes.testcases import (
    CaseBits32ArrayConnectSubCompAttrComp,
    CaseBits32ConnectSubCompAttrComp,
)

from ..StructuralRTLIRGenL2Pass import StructuralRTLIRGenL2Pass
from .StructuralRTLIRGenL1Pass_test import gen_connections


def test_L4_subcomp_attr():
  a = CaseBits32ConnectSubCompAttrComp.DUT()
  a.elaborate()
  a.apply( StructuralRTLIRGenL4Pass( gen_connections( a ) ) )
  connections = a.get_metadata( StructuralRTLIRGenL2Pass.connections )
  comp = CurComp(a, 's')
  # The first two signals are clk and reset
  assert connections[2] == \
    (SubCompAttr(CurCompAttr(comp, 'b'), 'out'), CurCompAttr(comp, 'out'))

def test_L4_subcomp_index():
  a = CaseBits32ArrayConnectSubCompAttrComp.DUT()
  a.elaborate()
  a.apply( StructuralRTLIRGenL4Pass( gen_connections( a ) ) )
  connections = a.get_metadata( StructuralRTLIRGenL2Pass.connections )
  comp = CurComp(a, 's')
  # The first ten signals are clks and resets
  assert connections[10] == \
    (SubCompAttr(ComponentIndex(CurCompAttr(comp, 'b'), 1), 'out'),
      CurCompAttr(comp, 'out'))
