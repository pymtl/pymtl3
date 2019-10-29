#=========================================================================
# StructuralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 21, 2019
"""Test the level 3 structural translators."""

import pytest

from pymtl3.datatypes import Bits1, Bits32
from pymtl3.dsl import Component, InPort, Interface, OutPort, connect
from pymtl3.passes.rtlir.errors import RTLIRConversionError
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure
from pymtl3.passes.translator.structural.StructuralTranslatorL4 import (
    StructuralTranslatorL4,
)

from .TestStructuralTranslator import mk_TestStructuralTranslator


def local_do_test( m ):
  tr = mk_TestStructuralTranslator(StructuralTranslatorL4)(m)
  tr.clear( m )
  tr.translate_structural(m)
  for comp in m._ref_comps.keys():
    decl_comp = tr.structural.decl_subcomps[comp]
    assert decl_comp == m._ref_comps[comp]
  for comp in m._ref_conns.keys():
    connections = tr.structural.connections[comp]
    assert connections == m._ref_conns[comp]

def test_multi_components( do_test ):
  class B( Component ):
    def construct( s ):
      s.out_b = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out_b = Bits32(0)
  class A( Component ):
    def construct( s ):
      s.out_a = OutPort( Bits32 )
      s.b = B()
      connect( s.b.out_b, s.out_a )
  a = A()
  a.elaborate()
  a._ref_comps = {
    a : \
"""\
component_decls:
  component_decl: b Component B
    component_ports:
      component_port: out_b Port of Vector32
    component_ifcs:
""", a.b : \
"""\
component_decls:
"""}
  a._ref_conns = {
    a : \
"""\
connections:
  connection: SubCompAttr CurCompAttr b out_b -> CurCompAttr out_a
""", a.b : \
"""\
connections:
"""}
  a._ref_src = \
"""\
component B
(
port_decls:
  port_decl: out_b Port of Vector32
interface_decls:
);
const_decls:
freevars:
wire_decls:
component_decls:
tmpvars:
upblk_srcs:
  upblk_src: upblk
connections:

endcomponent

component A
(
port_decls:
  port_decl: out_a Port of Vector32
interface_decls:
);
const_decls:
freevars:
wire_decls:
component_decls:
  component_decl: b Component B
    component_ports:
      component_port: out_b Port of Vector32
    component_ifcs:
tmpvars:
upblk_srcs:
connections:
  connection: SubCompAttr CurCompAttr b out_b -> CurCompAttr out_a

endcomponent
"""
  do_test( a )

def test_multi_components_ifc_hierarchy_connect( do_test ):
  class OutIfc( Interface ):
    def construct( s ):
      s.msg = OutPort( Bits32 )
      s.rdy = InPort( Bits1 )
      s.val = OutPort( Bits1 )
  class B( Component ):
    def construct( s ):
      s.out_b = OutPort( Bits32 )
      s.ifc_b = OutIfc()
      connect( s.out_b, 0 )
      connect( s.ifc_b.msg, 0 )
      connect( s.ifc_b.val, 1 )
  class A( Component ):
    def construct( s ):
      s.out_a = OutPort( Bits32 )
      s.b = B()
      s.ifc_a = OutIfc()
      connect( s.b.out_b, s.out_a )
      connect( s.b.ifc_b, s.ifc_a )
  a = A()
  a.elaborate()
  a._ref_comps = {
    a : \
"""\
component_decls:
  component_decl: b Component B
    component_ports:
      component_port: out_b Port of Vector32
    component_ifcs:
      component_ifc: ifc_b InterfaceView OutIfc
        component_ifc_ports:
          component_ifc_port: msg Port of Vector32
          component_ifc_port: rdy Port of Vector1
          component_ifc_port: val Port of Vector1
""", a.b : \
"""\
component_decls:
"""}
  a._ref_conns = {
    a : \
"""\
connections:
  connection: SubCompAttr CurCompAttr b out_b -> CurCompAttr out_a
  connection: IfcAttr SubCompAttr CurCompAttr b ifc_b msg -> IfcAttr CurCompAttr ifc_a msg
  connection: IfcAttr CurCompAttr ifc_a rdy -> IfcAttr SubCompAttr CurCompAttr b ifc_b rdy
  connection: IfcAttr SubCompAttr CurCompAttr b ifc_b val -> IfcAttr CurCompAttr ifc_a val
""", a.b : \
"""\
connections:
  connection: Bits32(0) -> CurCompAttr out_b
  connection: Bits32(0) -> IfcAttr CurCompAttr ifc_b msg
  connection: Bits1(1) -> IfcAttr CurCompAttr ifc_b val
"""}
  a._ref_src = \
"""\
component B
(
port_decls:
  port_decl: out_b Port of Vector32
interface_decls:
  interface_decl: ifc_b InterfaceView OutIfc
    interface_ports:
      interface_port: msg Port of Vector32
      interface_port: rdy Port of Vector1
      interface_port: val Port of Vector1
);
const_decls:
freevars:
wire_decls:
component_decls:
tmpvars:
upblk_srcs:
connections:
  connection: Bits32(0) -> CurCompAttr out_b
  connection: Bits32(0) -> IfcAttr CurCompAttr ifc_b msg
  connection: Bits1(1) -> IfcAttr CurCompAttr ifc_b val

endcomponent

component A
(
port_decls:
  port_decl: out_a Port of Vector32
interface_decls:
  interface_decl: ifc_a InterfaceView OutIfc
    interface_ports:
      interface_port: msg Port of Vector32
      interface_port: rdy Port of Vector1
      interface_port: val Port of Vector1
);
const_decls:
freevars:
wire_decls:
component_decls:
  component_decl: b Component B
    component_ports:
      component_port: out_b Port of Vector32
    component_ifcs:
      component_ifc: ifc_b InterfaceView OutIfc
        component_ifc_ports:
          component_ifc_port: msg Port of Vector32
          component_ifc_port: rdy Port of Vector1
          component_ifc_port: val Port of Vector1
tmpvars:
upblk_srcs:
connections:
  connection: SubCompAttr CurCompAttr b out_b -> CurCompAttr out_a
  connection: IfcAttr SubCompAttr CurCompAttr b ifc_b msg -> IfcAttr CurCompAttr ifc_a msg
  connection: IfcAttr CurCompAttr ifc_a rdy -> IfcAttr SubCompAttr CurCompAttr b ifc_b rdy
  connection: IfcAttr SubCompAttr CurCompAttr b ifc_b val -> IfcAttr CurCompAttr ifc_a val

endcomponent
"""
  do_test( a )

__all__ = [s for s in dir() if s.startswith('test_')]
