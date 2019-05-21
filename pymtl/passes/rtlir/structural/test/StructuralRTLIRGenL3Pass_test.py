#=========================================================================
# StructuralRTLIRGenL3Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the generation of level 1 structural RTLIR."""

from __future__ import absolute_import, division, print_function

import pymtl
from pymtl import Bits32, InPort, OutPort
from pymtl.passes.BasePass import PassMetadata
from pymtl.passes.rtlir.structural.StructuralRTLIRGenL3Pass import (
    StructuralRTLIRGenL3Pass,
)
from pymtl.passes.rtlir.structural.StructuralRTLIRSignalExpr import *


def test_L3_ifc_view_attr():
  class Ifc( pymtl.Interface ):
    def construct( s ):
      s.msg = InPort( Bits32 )
  class A( pymtl.Component ):
    def construct( s ):
      s.in_ = Ifc()
      s.out = OutPort( Bits32 )
      s.connect( s.out, s.in_.msg )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL3Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  assert ns.connections == \
    [(InterfaceAttr(CurCompAttr(comp, 'in_'), 'msg'), CurCompAttr(comp, 'out'))]

def test_L3_ifc_view_index():
  class Ifc( pymtl.Interface ):
    def construct( s ):
      s.msg = InPort( Bits32 )
  class A( pymtl.Component ):
    def construct( s ):
      s.in_ = [ Ifc() for _ in xrange(5) ]
      s.out = OutPort( Bits32 )
      s.connect( s.in_[2].msg, s.out )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL3Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  assert ns.connections == \
    [(InterfaceAttr(InterfaceViewIndex(CurCompAttr(comp, 'in_'), 2), 'msg'),
     CurCompAttr(comp, 'out'))]
