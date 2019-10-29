#=========================================================================
# StructuralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 21, 2019
"""Test the level 2 structural translators."""

import pytest

from pymtl3.datatypes import Bits16, Bits32, bitstruct
from pymtl3.dsl import Component, InPort, OutPort, Wire, connect
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir.errors import RTLIRConversionError
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure
from pymtl3.passes.translator.structural.StructuralTranslatorL2 import (
    StructuralTranslatorL2,
)

from .TestStructuralTranslator import mk_TestStructuralTranslator


def local_do_test( m ):
  m.elaborate()
  tr = mk_TestStructuralTranslator(StructuralTranslatorL2)(m)
  tr.clear( m )
  tr.translate_structural(m)
  try:
    name = tr.structural.component_unique_name[m]
    assert name == m._ref_name
    decl_ports = tr.structural.decl_ports[m]
    assert decl_ports == m._ref_ports
    decl_wires = tr.structural.decl_wires[m]
    assert decl_wires == m._ref_wires
    decl_consts = tr.structural.decl_consts[m]
    assert decl_consts == m._ref_consts
    connections = tr.structural.connections[m]
    assert connections == m._ref_conns
    struct_types = tr.structural.decl_type_struct
    assert sorted(struct_types, key=lambda x: str(x[1])) == m._ref_structs
  except AttributeError:
    pass

def test_struct_port_decl( do_test ):
  @bitstruct
  class B:
    foo: Bits32
    bar: Bits16
  class A( Component ):
    def construct( s ):
      s.struct = InPort( B )
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: struct Port of Struct B
"""
  a._ref_wires = "wire_decls:\n"
  a._ref_consts = "const_decls:\n"
  a._ref_conns = "connections:\n"
  a._ref_structs = [(rdt.Struct('B',
    {'foo':rdt.Vector(32), 'bar':rdt.Vector(16)}), 'B')]
  a._ref_src = \
"""\
struct B
component A
(
port_decls:
  port_decl: struct Port of Struct B
interface_decls:
);
const_decls:
freevars:
wire_decls:
component_decls:
tmpvars:
upblk_srcs:
connections:

endcomponent
"""
  do_test( a )

def test_struct_wire_decl( do_test ):
  @bitstruct
  class B:
    foo: Bits32
    bar: Bits16
  class A( Component ):
    def construct( s ):
      s.struct = Wire( B )
      @s.update
      def upblk():
        s.struct.foo = 0
        s.struct.bar = Bits16(42)
  a = A()
  a._ref_name = "A"
  a._ref_ports = "port_decls:\n"
  a._ref_wires = \
"""\
wire_decls:
  wire_decl: struct Wire of Struct B
"""
  a._ref_consts = "const_decls:\n"
  a._ref_conns = "connections:\n"
  a._ref_structs = [(rdt.Struct('B',
    {'foo':rdt.Vector(32), 'bar':rdt.Vector(16)}), 'B')]
  a._ref_src = \
"""\
struct B
component A
(
port_decls:
interface_decls:
);
const_decls:
freevars:
wire_decls:
  wire_decl: struct Wire of Struct B
component_decls:
tmpvars:
upblk_srcs:
  upblk_src: upblk
connections:

endcomponent
"""
  do_test( a )

@pytest.mark.xfail( reason = "RTLIR not support const struct instance yet" )
def test_struct_const_decl( do_test ):
  @bitstruct
  class B:
    foo: Bits32
    bar: Bits16
  class A( Component ):
    def construct( s ):
      s.struct = B()
  a = A()
  a._ref_name = "A"
  a._ref_ports = "port_decls:\n"
  a._ref_wires = "wire_decls:\n"
  a._ref_consts = \
"""\
const_decls:
  const_decl: struct Const of Struct B
"""
  a._ref_conns = "connections:\n"
  a._ref_structs = [(rdt.Struct('B',
    {'foo':rdt.Vector(32), 'bar':rdt.Vector(16)}), 'B')]
  a._ref_src = \
"""\
struct B
component A
(
port_decls:
interface_decls:
);
const_decls:
  const_decl: struct Const of Struct B
freevars:
wire_decls:
component_decls:
tmpvars:
upblk_srcs:
connections:

endcomponent
"""
  do_test( a )

def test_struct_port_array( do_test ):
  @bitstruct
  class B:
    foo: Bits32
    bar: Bits16
  class A( Component ):
    def construct( s ):
      s.struct = [ InPort( B ) for _ in range(5) ]
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: struct Array[5] of Port
"""
  a._ref_wires = "wire_decls:\n"
  a._ref_consts = "const_decls:\n"
  a._ref_conns = "connections:\n"
  a._ref_structs = [(rdt.Struct('B',
    {'foo':rdt.Vector(32), 'bar':rdt.Vector(16)}), 'B')]
  a._ref_src = \
"""\
struct B
component A
(
port_decls:
  port_decl: struct Array[5] of Port
interface_decls:
);
const_decls:
freevars:
wire_decls:
component_decls:
tmpvars:
upblk_srcs:
connections:

endcomponent
"""
  do_test( a )

def test_nested_struct_port_decl( do_test ):
  @bitstruct
  class C:
    bar: Bits16
  @bitstruct
  class B:
    foo: Bits32
    bar: C
  class A( Component ):
    def construct( s ):
      s.struct = InPort( B )
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: struct Port of Struct B
"""
  a._ref_wires = "wire_decls:\n"
  a._ref_consts = "const_decls:\n"
  a._ref_conns = "connections:\n"
  a._ref_structs = [(rdt.Struct('B',
    {'foo':rdt.Vector(32), 'bar':rdt.Struct('C', {'bar':rdt.Vector(16)})},
    ), 'B'),
    (rdt.Struct('C', {'bar':rdt.Vector(16)}), 'C')
  ]
  a._ref_src = \
"""\
struct C
struct B
component A
(
port_decls:
  port_decl: struct Port of Struct B
interface_decls:
);
const_decls:
freevars:
wire_decls:
component_decls:
tmpvars:
upblk_srcs:
connections:

endcomponent
"""
  do_test( a )

def test_struct_packed_array_port_decl( do_test ):
  @bitstruct
  class B:
    foo: [Bits32] * 5
    bar: Bits16
  class A( Component ):
    def construct( s ):
      s.struct = InPort( B )
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: struct Port of Struct B
"""
  a._ref_wires = "wire_decls:\n"
  a._ref_consts = "const_decls:\n"
  a._ref_conns = "connections:\n"
  a._ref_structs = [(rdt.Struct('B',
    {'foo':rdt.PackedArray([5], rdt.Vector(32)),
     'bar':rdt.Vector(16) }),
    'B')
  ]
  a._ref_src = \
"""\
struct B
component A
(
port_decls:
  port_decl: struct Port of Struct B
interface_decls:
);
const_decls:
freevars:
wire_decls:
component_decls:
tmpvars:
upblk_srcs:
connections:

endcomponent
"""
  do_test( a )

def test_nested_struct_packed_array_port_decl( do_test ):
  @bitstruct
  class C:
    bar: Bits16
  @bitstruct
  class B:
    foo: Bits32
    bar: [ C ] * 5
  class A( Component ):
    def construct( s ):
      s.struct = InPort( B )
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: struct Port of Struct B
"""
  a._ref_wires = "wire_decls:\n"
  a._ref_consts = "const_decls:\n"
  a._ref_conns = "connections:\n"
  a._ref_structs = [(rdt.Struct('B',
    {'foo':rdt.Vector(32),
     'bar':rdt.PackedArray([5], rdt.Struct('C', {'bar':rdt.Vector(16)}))}),
    'B'),
    (rdt.Struct('C', {'bar':rdt.Vector(16)}), 'C')
  ]
  a._ref_src = \
"""\
struct C
struct B
component A
(
port_decls:
  port_decl: struct Port of Struct B
interface_decls:
);
const_decls:
freevars:
wire_decls:
component_decls:
tmpvars:
upblk_srcs:
connections:

endcomponent
"""
  do_test( a )

def test_nested_struct_packed_array_index( do_test ):
  @bitstruct
  class C:
    bar: Bits16
  @bitstruct
  class B:
    foo: Bits32
    bar: [ C ] * 5
  class A( Component ):
    def construct( s ):
      s.struct = InPort( B )
      s.out = OutPort( C )
      connect( s.struct.bar[1], s.out )
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: out Port of Struct C
  port_decl: struct Port of Struct B
"""
  a._ref_wires = "wire_decls:\n"
  a._ref_consts = "const_decls:\n"
  a._ref_conns = \
"""\
connections:
  connection: PackedIndex StructAttr CurCompAttr struct bar 1 -> CurCompAttr out
"""
  a._ref_structs = [(rdt.Struct('B',
    {'foo':rdt.Vector(32),
     'bar':rdt.PackedArray([5], rdt.Struct('C', {'bar':rdt.Vector(16)}))}),
    'B'),
    (rdt.Struct('C', {'bar':rdt.Vector(16)}), 'C')
  ]
  a._ref_src = \
"""\
struct C
struct B
component A
(
port_decls:
  port_decl: out Port of Struct C
  port_decl: struct Port of Struct B
interface_decls:
);
const_decls:
freevars:
wire_decls:
component_decls:
tmpvars:
upblk_srcs:
connections:
  connection: PackedIndex StructAttr CurCompAttr struct bar 1 -> CurCompAttr out

endcomponent
"""
  do_test( a )

__all__ = list([s for s in dir() if s.startswith('test_')])
