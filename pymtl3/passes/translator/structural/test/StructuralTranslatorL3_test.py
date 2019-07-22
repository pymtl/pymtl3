#=========================================================================
# StructuralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 21, 2019
"""Test the level 3 structural translators."""

import pytest

from pymtl3.datatypes import Bits1, Bits32
from pymtl3.dsl import Component, InPort, Interface, OutPort, connect
from pymtl3.passes.rtlir.errors import RTLIRConversionError
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure
from pymtl3.passes.translator.structural.StructuralTranslatorL3 import (
    StructuralTranslatorL3,
)

from .TestStructuralTranslator import mk_TestStructuralTranslator


def local_do_test( m ):
  m.elaborate()
  tr = mk_TestStructuralTranslator(StructuralTranslatorL3)(m)
  tr.clear( m )
  tr.translate_structural(m)
  try:
    decl_ifcs = tr.structural.decl_ifcs[m]
    assert decl_ifcs == m._ref_ifcs
    connections = tr.structural.connections[m]
    assert connections == m._ref_conns
  except AttributeError:
    pass

def test_ifc_decls( do_test ):
  class Ifc( Interface ):
    def construct( s ):
      s.msg = OutPort( Bits32 )
      s.val = OutPort( Bits1 )
      s.rdy = InPort( Bits1 )
  class A( Component ):
    def construct( s ):
      s.ifc = Ifc()
      @s.update
      def upblk():
        s.ifc.msg = Bits32(42)
        s.ifc.val = Bits1(1)
  a = A()
  a._ref_ifcs = \
"""\
interface_decls:
  interface_decl: ifc InterfaceView Ifc
    interface_ports:
      interface_port: msg Port of Vector32
      interface_port: rdy Port of Vector1
      interface_port: val Port of Vector1
"""
  a._ref_conns = "connections:\n"
  a._ref_src = \
"""\
component A
(
port_decls:
interface_decls:
  interface_decl: ifc InterfaceView Ifc
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
  upblk_src: upblk
connections:

endcomponent
"""
  do_test( a )

def test_multi_ifc_decls( do_test ):
  class InIfc( Interface ):
    def construct( s ):
      s.msg = InPort( Bits32 )
      s.val = InPort( Bits1 )
      s.rdy = OutPort( Bits1 )
  class OutIfc( Interface ):
    def construct( s ):
      s.msg = OutPort( Bits32 )
      s.val = OutPort( Bits1 )
      s.rdy = InPort( Bits1 )
  class A( Component ):
    def construct( s ):
      s.in_ = InIfc()
      s.out = OutIfc()
      connect( s.out, s.in_ )
  a = A()
  a._ref_ifcs = \
"""\
interface_decls:
  interface_decl: in_ InterfaceView InIfc
    interface_ports:
      interface_port: msg Port of Vector32
      interface_port: rdy Port of Vector1
      interface_port: val Port of Vector1
  interface_decl: out InterfaceView OutIfc
    interface_ports:
      interface_port: msg Port of Vector32
      interface_port: rdy Port of Vector1
      interface_port: val Port of Vector1
"""
  a._ref_conns = \
"""\
connections:
  connection: IfcAttr CurCompAttr in_ msg -> IfcAttr CurCompAttr out msg
  connection: IfcAttr CurCompAttr out rdy -> IfcAttr CurCompAttr in_ rdy
  connection: IfcAttr CurCompAttr in_ val -> IfcAttr CurCompAttr out val
"""
  a._ref_src = \
"""\
component A
(
port_decls:
interface_decls:
  interface_decl: in_ InterfaceView InIfc
    interface_ports:
      interface_port: msg Port of Vector32
      interface_port: rdy Port of Vector1
      interface_port: val Port of Vector1
  interface_decl: out InterfaceView OutIfc
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
  connection: IfcAttr CurCompAttr in_ msg -> IfcAttr CurCompAttr out msg
  connection: IfcAttr CurCompAttr out rdy -> IfcAttr CurCompAttr in_ rdy
  connection: IfcAttr CurCompAttr in_ val -> IfcAttr CurCompAttr out val

endcomponent
"""
  do_test( a )

def test_ifc_array_idx( do_test ):
  class InIfc( Interface ):
    def construct( s ):
      s.msg = InPort( Bits32 )
      s.val = InPort( Bits1 )
      s.rdy = OutPort( Bits1 )
  class OutIfc( Interface ):
    def construct( s ):
      s.msg = OutPort( Bits32 )
      s.val = OutPort( Bits1 )
      s.rdy = InPort( Bits1 )
  class A( Component ):
    def construct( s ):
      s.in_ = [ InIfc() for _ in range(5) ]
      s.out = [ OutIfc() for _ in range(5) ]
      for i in range(5):
        connect( s.out[i], s.in_[i] )
  a = A()
  a._ref_ifcs = \
"""\
interface_decls:
  interface_decl: in_ Array[5] of InterfaceView InIfc
    interface_ports:
      interface_port: msg Port of Vector32
      interface_port: rdy Port of Vector1
      interface_port: val Port of Vector1
  interface_decl: out Array[5] of InterfaceView OutIfc
    interface_ports:
      interface_port: msg Port of Vector32
      interface_port: rdy Port of Vector1
      interface_port: val Port of Vector1
"""
  a._ref_conns = \
"""\
connections:
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 0 msg -> IfcAttr IfcArrayIdx CurCompAttr out 0 msg
  connection: IfcAttr IfcArrayIdx CurCompAttr out 0 rdy -> IfcAttr IfcArrayIdx CurCompAttr in_ 0 rdy
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 0 val -> IfcAttr IfcArrayIdx CurCompAttr out 0 val
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 1 msg -> IfcAttr IfcArrayIdx CurCompAttr out 1 msg
  connection: IfcAttr IfcArrayIdx CurCompAttr out 1 rdy -> IfcAttr IfcArrayIdx CurCompAttr in_ 1 rdy
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 1 val -> IfcAttr IfcArrayIdx CurCompAttr out 1 val
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 2 msg -> IfcAttr IfcArrayIdx CurCompAttr out 2 msg
  connection: IfcAttr IfcArrayIdx CurCompAttr out 2 rdy -> IfcAttr IfcArrayIdx CurCompAttr in_ 2 rdy
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 2 val -> IfcAttr IfcArrayIdx CurCompAttr out 2 val
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 3 msg -> IfcAttr IfcArrayIdx CurCompAttr out 3 msg
  connection: IfcAttr IfcArrayIdx CurCompAttr out 3 rdy -> IfcAttr IfcArrayIdx CurCompAttr in_ 3 rdy
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 3 val -> IfcAttr IfcArrayIdx CurCompAttr out 3 val
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 4 msg -> IfcAttr IfcArrayIdx CurCompAttr out 4 msg
  connection: IfcAttr IfcArrayIdx CurCompAttr out 4 rdy -> IfcAttr IfcArrayIdx CurCompAttr in_ 4 rdy
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 4 val -> IfcAttr IfcArrayIdx CurCompAttr out 4 val
"""
  a._ref_src = \
"""\
component A
(
port_decls:
interface_decls:
  interface_decl: in_ Array[5] of InterfaceView InIfc
    interface_ports:
      interface_port: msg Port of Vector32
      interface_port: rdy Port of Vector1
      interface_port: val Port of Vector1
  interface_decl: out Array[5] of InterfaceView OutIfc
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
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 0 msg -> IfcAttr IfcArrayIdx CurCompAttr out 0 msg
  connection: IfcAttr IfcArrayIdx CurCompAttr out 0 rdy -> IfcAttr IfcArrayIdx CurCompAttr in_ 0 rdy
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 0 val -> IfcAttr IfcArrayIdx CurCompAttr out 0 val
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 1 msg -> IfcAttr IfcArrayIdx CurCompAttr out 1 msg
  connection: IfcAttr IfcArrayIdx CurCompAttr out 1 rdy -> IfcAttr IfcArrayIdx CurCompAttr in_ 1 rdy
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 1 val -> IfcAttr IfcArrayIdx CurCompAttr out 1 val
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 2 msg -> IfcAttr IfcArrayIdx CurCompAttr out 2 msg
  connection: IfcAttr IfcArrayIdx CurCompAttr out 2 rdy -> IfcAttr IfcArrayIdx CurCompAttr in_ 2 rdy
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 2 val -> IfcAttr IfcArrayIdx CurCompAttr out 2 val
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 3 msg -> IfcAttr IfcArrayIdx CurCompAttr out 3 msg
  connection: IfcAttr IfcArrayIdx CurCompAttr out 3 rdy -> IfcAttr IfcArrayIdx CurCompAttr in_ 3 rdy
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 3 val -> IfcAttr IfcArrayIdx CurCompAttr out 3 val
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 4 msg -> IfcAttr IfcArrayIdx CurCompAttr out 4 msg
  connection: IfcAttr IfcArrayIdx CurCompAttr out 4 rdy -> IfcAttr IfcArrayIdx CurCompAttr in_ 4 rdy
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 4 val -> IfcAttr IfcArrayIdx CurCompAttr out 4 val

endcomponent
"""
  do_test( a )

# TODO: support nested interface
@pytest.mark.xfail( reason = "TOOD: support nested interface" )
def test_nested_ifc( do_test ):
  class ReqIfc( Interface ):
    def construct( s ):
      s.msg = InPort( Bits32 )
      s.val = InPort( Bits1 )
      s.rdy = OutPort( Bits1 )
  class MemReqIfc( Interface ):
    def construct( s ):
      s.req_ifc = ReqIfc()
      s.ctrl_foo = InPort( Bits1 )
      s.ctrl_bar = OutPort( Bits1 )
  class RespIfc( Interface ):
    def construct( s ):
      s.msg = OutPort( Bits32 )
      s.val = OutPort( Bits1 )
      s.rdy = InPort( Bits1 )
  class MemRespIfc( Interface ):
    def construct( s ):
      s.resp_ifc = RespIfc()
      s.ctrl_foo = OutPort( Bits1 )
      s.ctrl_bar = InPort( Bits1 )
  class A( Component ):
    def construct( s ):
      s.in_ = [ MemReqIfc() for _ in range(5) ]
      s.out = [ MemRespIfc() for _ in range(5) ]
      for i in range(5):
        connect( s.out[i], s.in_[i] )
  a = A()
  a._ref_ifcs = \
"""\
interface_decls:
  interface_decl: in_ Array[5] of InterfaceView MemReqIfc
    interface_ports:
      interface_port: msg Port of Vector32
  interface_decl: out Array[5] of InterfaceView OutIfc
    interface_ports:
      interface_port: msg Port of Vector32
"""
  a._ref_conns = \
"""\
connections:
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 0 msg -> IfcAttr IfcArrayIdx CurCompAttr out 0 msg
"""
  a._ref_src = \
"""\
component A
(
port_decls:
interface_decls:
  interface_decl: in_ Array[5] of InterfaceView InIfc
    interface_ports:
      interface_port: msg Port of Vector32
  interface_decl: out Array[5] of InterfaceView OutIfc
    interface_ports:
      interface_port: msg Port of Vector32
);
const_decls:
freevars:
wire_decls:
component_decls:
tmpvars:
upblk_srcs:
connections:
  connection: IfcAttr IfcArrayIdx CurCompAttr in_ 0 msg -> IfcAttr IfcArrayIdx CurCompAttr out 0 msg

endcomponent
"""
  do_test( a )

__all__ = [s for s in dir() if s.startswith('test_')]
