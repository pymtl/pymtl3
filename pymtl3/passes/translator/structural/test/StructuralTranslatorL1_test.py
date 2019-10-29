#=========================================================================
# StructuralTranslatorL1_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 21, 2019
"""Test the level 1 structural translators."""

from pymtl3.datatypes import Bits1, Bits4, Bits16, Bits32
from pymtl3.dsl import Component, InPort, OutPort, Wire, connect
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir.errors import RTLIRConversionError
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure
from pymtl3.passes.translator.structural.StructuralTranslatorL1 import (
    StructuralTranslatorL1,
)

from .TestStructuralTranslator import mk_TestStructuralTranslator


def local_do_test( m ):
  m.elaborate()
  tr = mk_TestStructuralTranslator(StructuralTranslatorL1)(m)
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
    vector_types = tr.structural.decl_type_vector
    assert sorted(vector_types, key=lambda x: str(x[0])) == m._ref_vectors
  except AttributeError:
    pass

def test_component_args( do_test ):
  class A( Component ):
    def construct( s, foo, bar ):
      assert foo == Bits4(0)
      assert bar == Bits16(42)
  a = A( Bits4(0), Bits16(42) )
  a._ref_name = 'A__foo_0__bar_002a'
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
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

def test_component_dfefault_args( do_test ):
  class A( Component ):
    def construct( s, foo, bar=Bits16(42) ):
      assert foo == Bits4(0)
      assert bar == Bits16(42)
  a = A( Bits4(0) )
  a._ref_name = 'A__foo_0__bar_002a'
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
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

def test_component_kw_args( do_test ):
  class A( Component ):
    def construct( s, foo, bar ):
      assert foo == Bits4(0)
      assert bar == Bits16(42)
  a = A( foo = Bits4(0), bar = Bits16(42) )
  a._ref_name = 'A__foo_0__bar_002a'
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
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

def test_component_star_args( do_test ):
  class A( Component ):
    def construct( s, *args ):
      assert args[0] == Bits4(0)
      assert args[1] == Bits16(42)
  args = [ Bits4(0), Bits16(42) ]
  a = A( *args )
  with expected_failure( RTLIRConversionError, "varargs are not allowed" ):
    do_test( a )

def test_component_star_args_ungroup( do_test ):
  class A( Component ):
    def construct( s, foo, bar ):
      assert foo == Bits4(0)
      assert bar == Bits16(42)
  args = [ Bits4(0), Bits16(42) ]
  a = A( *args )
  a._ref_name = 'A__foo_0__bar_002a'
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
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

def test_component_double_star_args( do_test ):
  class A( Component ):
    def construct( s, **kwargs ):
      assert kwargs['foo'] == Bits4(0)
      assert kwargs['bar'] == Bits16(42)
  kwargs = { 'foo':Bits4(0), 'bar':Bits16(42) }
  a = A( **kwargs )
  with expected_failure( RTLIRConversionError, "keyword args are not allowed" ):
    do_test( a )

def test_component_double_star_args_ungroup( do_test ):
  class A( Component ):
    def construct( s, foo, bar ):
      assert foo == Bits4(0)
      assert bar == Bits16(42)
  kwargs = { 'foo':Bits4(0), 'bar':Bits16(42) }
  a = A( **kwargs )
  a._ref_name = 'A__foo_0__bar_002a'
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
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

def test_component_mixed_kw_args( do_test ):
  class A( Component ):
    def construct( s, foo, bar, woo=Bits32(0) ):
      pass
  a = A( Bits4(0), bar = Bits16(42) )
  a._ref_name = 'A__foo_0__bar_002a__woo_00000000'
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
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

def test_port_decls( do_test ):
  class A( Component ):
    def construct( s ):
      s.foo = InPort( Bits32 )
      s.bar = InPort( Bits4 )
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: bar Port of Vector4
  port_decl: foo Port of Vector32
"""
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
  port_decl: bar Port of Vector4
  port_decl: foo Port of Vector32
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

def test_array_port_decl( do_test ):
  class A( Component ):
    def construct( s ):
      s.foo = [ InPort( Bits32 ) for _ in range(5) ]
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: foo Array[5] of Port
"""
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
  port_decl: foo Array[5] of Port
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

def test_wire_decls( do_test ):
  class A( Component ):
    def construct( s ):
      s.foo = Wire( Bits32 )
      s.bar = Wire( Bits4 )
      @s.update
      def upblk():
        s.foo = 42
        s.bar = Bits4(0)
  a = A()
  a._ref_name = "A"
  a._ref_ports = "port_decls:\n"
  a._ref_wires = \
"""\
wire_decls:
  wire_decl: bar Wire of Vector4
  wire_decl: foo Wire of Vector32
"""
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
interface_decls:
);
const_decls:
freevars:
wire_decls:
  wire_decl: bar Wire of Vector4
  wire_decl: foo Wire of Vector32
component_decls:
tmpvars:
upblk_srcs:
  upblk_src: upblk
connections:

endcomponent
"""
  do_test( a )

def test_array_wire_decl( do_test ):
  class A( Component ):
    def construct( s ):
      s.foo = [ Wire( Bits32 ) for _ in range(5) ]
      @s.update
      def upblk():
        for i in range(5):
          s.foo[i] = Bits32(0)
  a = A()
  a._ref_name = "A"
  a._ref_ports = "port_decls:\n"
  a._ref_wires = \
"""\
wire_decls:
  wire_decl: foo Array[5] of Wire
"""
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
interface_decls:
);
const_decls:
freevars:
wire_decls:
  wire_decl: foo Array[5] of Wire
component_decls:
tmpvars:
upblk_srcs:
  upblk_src: upblk
connections:

endcomponent
"""
  do_test( a )

def test_const_decls( do_test ):
  class A( Component ):
    def construct( s ):
      s.foo = Bits32(0)
      s.bar = Bits4(0)
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.foo
        s.out = Bits32(s.bar)
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: out Port of Vector32
"""
  a._ref_wires = "wire_decls:\n"
  a._ref_consts = \
"""\
const_decls:
  const_decl: bar Const of Vector4
  const_decl: foo Const of Vector32
"""
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
  port_decl: out Port of Vector32
interface_decls:
);
const_decls:
  const_decl: bar Const of Vector4
  const_decl: foo Const of Vector32
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

def test_array_const_decl( do_test ):
  class A( Component ):
    def construct( s ):
      s.foo = [ Bits32(0) for _ in range(5) ]
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.foo[0]
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: out Port of Vector32
"""
  a._ref_wires = "wire_decls:\n"
  a._ref_consts = \
"""\
const_decls:
  const_decl: foo Array[5] of Const
"""
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
  port_decl: out Port of Vector32
interface_decls:
);
const_decls:
  const_decl: foo Array[5] of Const
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

def test_expr_bit_sel( do_test ):
  # PyMTL DSL treat bit selection as a 1-bit part selection!
  class A( Component ):
    def construct( s ):
      s.foo = InPort( Bits32 )
      s.bar = OutPort( Bits1 )
      connect( s.bar, s.foo[1] )
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: bar Port of Vector1
  port_decl: foo Port of Vector32
"""
  a._ref_wires = "wire_decls:\n"
  a._ref_consts = "const_decls:\n"
  a._ref_conns = \
"""\
connections:
  connection: PartSel CurCompAttr foo 1 2 -> CurCompAttr bar
"""
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
  port_decl: bar Port of Vector1
  port_decl: foo Port of Vector32
interface_decls:
);
const_decls:
freevars:
wire_decls:
component_decls:
tmpvars:
upblk_srcs:
connections:
  connection: PartSel CurCompAttr foo 1 2 -> CurCompAttr bar

endcomponent
"""
  do_test( a )

def test_expr_part_sel( do_test ):
  class A( Component ):
    def construct( s ):
      s.foo = InPort( Bits32 )
      s.bar = OutPort( Bits4 )
      connect( s.bar, s.foo[0:4] )
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: bar Port of Vector4
  port_decl: foo Port of Vector32
"""
  a._ref_wires = "wire_decls:\n"
  a._ref_consts = "const_decls:\n"
  a._ref_conns = \
"""\
connections:
  connection: PartSel CurCompAttr foo 0 4 -> CurCompAttr bar
"""
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
  port_decl: bar Port of Vector4
  port_decl: foo Port of Vector32
interface_decls:
);
const_decls:
freevars:
wire_decls:
component_decls:
tmpvars:
upblk_srcs:
connections:
  connection: PartSel CurCompAttr foo 0 4 -> CurCompAttr bar

endcomponent
"""
  do_test( a )

def test_expr_port_array_index( do_test ):
  class A( Component ):
    def construct( s ):
      s.foo = [ InPort( Bits32 ) for _ in range(5) ]
      s.bar = OutPort( Bits32 )
      connect( s.bar, s.foo[1] )
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: bar Port of Vector32
  port_decl: foo Array[5] of Port
"""
  a._ref_wires = "wire_decls:\n"
  a._ref_consts = "const_decls:\n"
  a._ref_conns = \
"""\
connections:
  connection: PortArrayIdx CurCompAttr foo 1 -> CurCompAttr bar
"""
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
  port_decl: bar Port of Vector32
  port_decl: foo Array[5] of Port
interface_decls:
);
const_decls:
freevars:
wire_decls:
component_decls:
tmpvars:
upblk_srcs:
connections:
  connection: PortArrayIdx CurCompAttr foo 1 -> CurCompAttr bar

endcomponent
"""
  do_test( a )

def test_expr_wire_array_index( do_test ):
  class A( Component ):
    def construct( s ):
      s.wire = [ Wire( Bits32 ) for _ in range(5) ]
      s.bar = OutPort( Bits32 )
      connect( s.bar, s.wire[1] )
      @s.update
      def upblk():
        for i in range(5):
          s.wire[i] = Bits32(0)
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: bar Port of Vector32
"""
  a._ref_wires = \
"""\
wire_decls:
  wire_decl: wire Array[5] of Wire
"""
  a._ref_consts = "const_decls:\n"
  a._ref_conns = \
"""\
connections:
  connection: WireArrayIdx CurCompAttr wire 1 -> CurCompAttr bar
"""
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
  port_decl: bar Port of Vector32
interface_decls:
);
const_decls:
freevars:
wire_decls:
  wire_decl: wire Array[5] of Wire
component_decls:
tmpvars:
upblk_srcs:
  upblk_src: upblk
connections:
  connection: WireArrayIdx CurCompAttr wire 1 -> CurCompAttr bar

endcomponent
"""
  do_test( a )

def test_expr_const_array_index( do_test ):
  # Since PyMTL DSL does not provide names for constants, the
  # strutural RTLIR will remove the signal hierarchy for constants
  # and just treat them as constant integers.
  class A( Component ):
    def construct( s ):
      s.const = [ 0 for _ in range(5) ]
      s.bar = OutPort( Bits32 )
      connect( s.bar, s.const[1] )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.const[0]
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: bar Port of Vector32
  port_decl: out Port of Vector32
"""
  a._ref_wires = "wire_decls:\n"
  a._ref_consts = \
"""\
const_decls:
  const_decl: const Array[5] of Const
"""
  a._ref_conns = \
"""\
connections:
  connection: Bits32(0) -> CurCompAttr bar
"""
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
  port_decl: bar Port of Vector32
  port_decl: out Port of Vector32
interface_decls:
);
const_decls:
  const_decl: const Array[5] of Const
freevars:
wire_decls:
component_decls:
tmpvars:
upblk_srcs:
  upblk_src: upblk
connections:
  connection: Bits32(0) -> CurCompAttr bar

endcomponent
"""
  do_test( a )

def test_dtype_vector( do_test ):
  class A( Component ):
    def construct( s ):
      s.foo = InPort(Bits32)
  a = A()
  a._ref_name = "A"
  a._ref_ports = \
"""\
port_decls:
  port_decl: foo Port of Vector32
"""
  a._ref_wires = "wire_decls:\n"
  a._ref_consts = "const_decls:\n"
  a._ref_conns = "connections:\n"
  a._ref_vectors = [ (rdt.Vector(1), "Vector1"), (rdt.Vector(32), "Vector32") ]
  a._ref_src = \
f"""\
component {a._ref_name}
(
port_decls:
  port_decl: foo Port of Vector32
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

__all__ = list([s for s in dir() if s.startswith('test_')])
