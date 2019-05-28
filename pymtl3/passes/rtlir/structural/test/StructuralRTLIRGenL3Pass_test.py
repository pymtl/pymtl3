#=========================================================================
# StructuralRTLIRGenL3Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the generation of level 1 structural RTLIR."""

from __future__ import absolute_import, division, print_function

import pymtl
from pymtl import Bits1, Bits32, InPort, OutPort
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

def test_L3_ifc_view_connection():
  class InIfc( pymtl.Interface ):
    def construct( s ):
      s.msg = InPort( Bits32 )
      s.val = InPort( Bits1 )
      s.rdy = OutPort( Bits1 )
  class OutIfc( pymtl.Interface ):
    def construct( s ):
      s.msg = OutPort( Bits32 )
      s.val = OutPort( Bits1 )
      s.rdy = InPort( Bits1 )
  class A( pymtl.Component ):
    def construct( s ):
      s.in_ = InIfc()
      s.out = OutIfc()
      # This will be automatically extended to connect all signals in
      # this interface!
      s.connect( s.out, s.in_ )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL3Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  ref = \
    [
      (InterfaceAttr(CurCompAttr(comp, 'in_'), 'msg'),
      InterfaceAttr(CurCompAttr(comp, 'out'), 'msg')),
      (InterfaceAttr(CurCompAttr(comp, 'in_'), 'val'),
      InterfaceAttr(CurCompAttr(comp, 'out'), 'val')),
      (InterfaceAttr(CurCompAttr(comp, 'out'), 'rdy'),
      InterfaceAttr(CurCompAttr(comp, 'in_'), 'rdy')),
    ]
  # The order of ports is non-deterministic?
  assert ns.connections[0] in ref
  assert ns.connections[1] in ref
  assert ns.connections[2] in ref
