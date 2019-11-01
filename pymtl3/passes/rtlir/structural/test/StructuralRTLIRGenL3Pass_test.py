#=========================================================================
# StructuralRTLIRGenL3Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the generation of level 1 structural RTLIR."""

import pymtl3.dsl as dsl
from pymtl3.datatypes import Bits1, Bits32
from pymtl3.passes.rtlir.structural.StructuralRTLIRGenL3Pass import (
    StructuralRTLIRGenL3Pass,
)
from pymtl3.passes.rtlir.structural.StructuralRTLIRSignalExpr import *

from .StructuralRTLIRGenL1Pass_test import gen_connections


def test_L3_ifc_view_attr():
  class Ifc( dsl.Interface ):
    def construct( s ):
      s.msg = dsl.InPort( Bits32 )
  class A( dsl.Component ):
    def construct( s ):
      s.in_ = Ifc()
      s.out = dsl.OutPort( Bits32 )
      dsl.connect( s.out, s.in_.msg )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL3Pass( gen_connections( a ) ) )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  assert ns.connections == \
    [(InterfaceAttr(CurCompAttr(comp, 'in_'), 'msg'), CurCompAttr(comp, 'out'))]

def test_L3_ifc_view_index():
  class Ifc( dsl.Interface ):
    def construct( s ):
      s.msg = dsl.InPort( Bits32 )
  class A( dsl.Component ):
    def construct( s ):
      s.in_ = [ Ifc() for _ in range(5) ]
      s.out = dsl.OutPort( Bits32 )
      dsl.connect( s.in_[2].msg, s.out )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL3Pass( gen_connections( a ) ) )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  assert ns.connections == \
    [(InterfaceAttr(InterfaceViewIndex(CurCompAttr(comp, 'in_'), 2), 'msg'),
     CurCompAttr(comp, 'out'))]

def test_L3_ifc_view_connection():
  class InIfc( dsl.Interface ):
    def construct( s ):
      s.msg = dsl.InPort( Bits32 )
      s.val = dsl.InPort( Bits1 )
      s.rdy = dsl.OutPort( Bits1 )
  class OutIfc( dsl.Interface ):
    def construct( s ):
      s.msg = dsl.OutPort( Bits32 )
      s.val = dsl.OutPort( Bits1 )
      s.rdy = dsl.InPort( Bits1 )
  class A( dsl.Component ):
    def construct( s ):
      s.in_ = InIfc()
      s.out = OutIfc()
      # This will be automatically extended to connect all signals in
      # this interface!
      dsl.connect( s.out, s.in_ )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL3Pass( gen_connections( a ) ) )
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
