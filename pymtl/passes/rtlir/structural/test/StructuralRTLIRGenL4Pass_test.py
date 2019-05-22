#=========================================================================
# StructuralRTLIRGenL4Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the generation of level 1 structural RTLIR."""

from __future__ import absolute_import, division, print_function

import pymtl
from pymtl import Bits32, InPort, OutPort
from pymtl.passes.BasePass import PassMetadata
from pymtl.passes.rtlir.structural.StructuralRTLIRGenL4Pass import (
    StructuralRTLIRGenL4Pass,
)
from pymtl.passes.rtlir.structural.StructuralRTLIRSignalExpr import *


def test_L4_subcomp_attr():
  class B( pymtl.Component ):
    def construct( s ):
      s.msg = OutPort( Bits32 )
      s.connect( s.msg, 42 )
  class A( pymtl.Component ):
    def construct( s ):
      s.b = B()
      s.out = OutPort( Bits32 )
      s.connect( s.out, s.b.msg )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL4Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  # The first two signals are clk and reset
  assert ns.connections[2] == \
    (SubCompAttr(CurCompAttr(comp, 'b'), 'msg'), CurCompAttr(comp, 'out'))

def test_L4_subcomp_index():
  class B( pymtl.Component ):
    def construct( s ):
      s.msg = OutPort( Bits32 )
      s.connect( s.msg, 42 )
  class A( pymtl.Component ):
    def construct( s ):
      s.b = [ B() for _ in xrange(5) ]
      s.out = OutPort( Bits32 )
      s.connect( s.out, s.b[1].msg )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL4Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  # The first ten signals are clks and resets
  assert ns.connections[10] == \
    (SubCompAttr(ComponentIndex(CurCompAttr(comp, 'b'), 1), 'msg'),
      CurCompAttr(comp, 'out'))
