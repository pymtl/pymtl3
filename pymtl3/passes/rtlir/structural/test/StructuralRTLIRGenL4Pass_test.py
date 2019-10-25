#=========================================================================
# StructuralRTLIRGenL4Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the generation of level 1 structural RTLIR."""

import pymtl3.dsl as dsl
from pymtl3.datatypes import Bits32
from pymtl3.passes.rtlir.structural.StructuralRTLIRGenL4Pass import (
    StructuralRTLIRGenL4Pass,
)
from pymtl3.passes.rtlir.structural.StructuralRTLIRSignalExpr import *

from .StructuralRTLIRGenL1Pass_test import gen_connections


def test_L4_subcomp_attr():
  class B( dsl.Component ):
    def construct( s ):
      s.msg = dsl.OutPort( Bits32 )
      dsl.connect( s.msg, 42 )
  class A( dsl.Component ):
    def construct( s ):
      s.b = B()
      s.out = dsl.OutPort( Bits32 )
      dsl.connect( s.out, s.b.msg )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL4Pass( gen_connections( a ) ) )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  # The first two signals are clk and reset
  assert ns.connections[2] == \
    (SubCompAttr(CurCompAttr(comp, 'b'), 'msg'), CurCompAttr(comp, 'out'))

def test_L4_subcomp_index():
  class B( dsl.Component ):
    def construct( s ):
      s.msg = dsl.OutPort( Bits32 )
      dsl.connect( s.msg, 42 )
  class A( dsl.Component ):
    def construct( s ):
      s.b = [ B() for _ in range(5) ]
      s.out = dsl.OutPort( Bits32 )
      dsl.connect( s.out, s.b[1].msg )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL4Pass( gen_connections( a ) ) )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  # The first ten signals are clks and resets
  assert ns.connections[10] == \
    (SubCompAttr(ComponentIndex(CurCompAttr(comp, 'b'), 1), 'msg'),
      CurCompAttr(comp, 'out'))
