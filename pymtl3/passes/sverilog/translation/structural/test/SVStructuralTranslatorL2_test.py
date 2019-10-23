#=========================================================================
# SVStructuralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 2 SystemVerilog structural translator."""

from pymtl3.datatypes import Bits1, Bits32, bitstruct
from pymtl3.dsl import Component, InPort, OutPort, Wire, connect
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.structural.SVStructuralTranslatorL2 import (
    SVStructuralTranslatorL2,
)

from .SVStructuralTranslatorL1_test import check_eq, is_sverilog_reserved


def local_do_test( m ):
  m.elaborate()
  SVStructuralTranslatorL2.is_sverilog_reserved = is_sverilog_reserved
  tr = SVStructuralTranslatorL2( m )
  tr.clear( m )
  tr.translate_structural( m )

  ports = tr.structural.decl_ports[m]
  wires = tr.structural.decl_wires[m]
  structs = tr.structural.decl_type_struct
  conns = tr.structural.connections[m]
  check_eq( ports, m._ref_ports[m] )
  check_eq( wires, m._ref_wires[m] )
  assert [x[0] for x in structs] == [x[0] for x in m._ref_structs]
  check_eq( [x[1]['def'] for x in structs], [x[1] for x in m._ref_structs] )
  check_eq( conns, m._ref_conns[m] )

def test_struct_const_structural( do_test ):
  @bitstruct
  class B:
    foo: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = B( Bits32(42) )
      s.out = OutPort( Bits32 )
      connect( s.out, s.in_.foo )
  a = A()
  a._ref_structs = [
    ( rdt.Struct( 'B', {'foo':rdt.Vector(32)} ), \
"""\
typedef struct packed {
  logic [31:0] foo;
} B;
""" ) ]
  a._ref_ports = { a : \
"""\
  input logic [0:0] clk,
  output logic [31:0] out,
  input logic [0:0] reset\
"""
}
  a._ref_wires = { a : "" }
  a._ref_conns = { a : \
"""\
  assign out = 32'd42;\
"""
}
  # Yosys backend test reference output
  a._ref_ports_port_yosys = a._ref_ports
  a._ref_ports_wire_yosys = { a : "" }
  a._ref_ports_conn_yosys = { a : "" }
  a._ref_wires_yosys = a._ref_wires
  a._ref_conns_yosys = a._ref_conns
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    pass
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[0])
  a._test_vectors = [
    [       42 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )

def test_struct_port( do_test ):
  @bitstruct
  class B:
    foo: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits32 )
      connect( s.out, s.in_.foo )
  a = A()
  a._ref_structs = [
    ( rdt.Struct( 'B', {'foo':rdt.Vector(32)} ), \
"""\
typedef struct packed {
  logic [31:0] foo;
} B;
""" ) ]
  a._ref_ports = { a : \
"""\
  input logic [0:0] clk,
  input B in_,
  output logic [31:0] out,
  input logic [0:0] reset\
""" }
  a._ref_wires = { a : "" }
  a._ref_conns = { a : \
"""\
  assign out = in_.foo;\
""" }

  # Yosys backend test reference output
  a._ref_ports_port_yosys = { a : \
"""\
  input logic [0:0] clk,
  input logic [31:0] in___foo,
  output logic [31:0] out,
  input logic [0:0] reset\
""" }
  a._ref_ports_wire_yosys = { a : \
"""\
  logic [31:0] in_;\
""" }
  a._ref_ports_conn_yosys = { a : \
"""\
  assign in_[31:0] = in___foo;\
"""
}
  a._ref_wires_yosys = a._ref_wires
  a._ref_conns_yosys = { a : \
"""\
  assign out = in___foo;\
""" }

  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = tv[0]
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[1])
  a._test_vectors = [
    [   B(),      0 ],
    [   B( 0),    0 ],
    [   B(-1),   -1 ],
    [   B(-2),   -2 ],
    [   B(24),   24 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )

def test_nested_struct_port( do_test ):
  @bitstruct
  class C:
    bar: Bits32
  @bitstruct
  class B:
    c: C
    foo: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out_foo = OutPort( Bits32 )
      s.out_bar = OutPort( Bits32 )
      connect( s.out_foo, s.in_.foo )
      connect( s.out_bar, s.in_.c.bar )
  a = A()
  _C = rdt.Struct( 'C', {'bar':rdt.Vector(32)} )
  a._ref_structs = [ ( _C, \
"""\
typedef struct packed {
  logic [31:0] bar;
} C;
""" ),
    ( rdt.Struct( 'B', {'c':_C, 'foo':rdt.Vector(32)} ), \
"""\
typedef struct packed {
  C c;
  logic [31:0] foo;
} B;
""" ) ]
  a._ref_ports = { a : \
"""\
  input logic [0:0] clk,
  input B in_,
  output logic [31:0] out_bar,
  output logic [31:0] out_foo,
  input logic [0:0] reset\
""" }
  a._ref_wires = { a : "" }
  a._ref_conns = { a : \
"""\
  assign out_foo = in_.foo;
  assign out_bar = in_.c.bar;\
""" }

  # Yosys backend test reference output
  a._ref_ports_port_yosys = { a : \
"""\
  input logic [0:0] clk,
  input logic [31:0] in___c__bar,
  input logic [31:0] in___foo,
  output logic [31:0] out_bar,
  output logic [31:0] out_foo,
  input logic [0:0] reset\
""" }
  a._ref_ports_wire_yosys = { a : \
"""\
  logic [31:0] in___c;
  logic [63:0] in_;\
""" }
  a._ref_ports_conn_yosys = { a : \
"""\
  assign in___c[31:0] = in___c__bar;
  assign in_[63:32] = in___c__bar;
  assign in_[31:0] = in___foo;\
"""
}
  a._ref_wires_yosys = a._ref_wires
  a._ref_conns_yosys = { a : \
"""\
  assign out_foo = in___foo;
  assign out_bar = in___c__bar;\
""" }

  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = tv[0]
  def tv_out( m, tv ):
    assert m.out_foo == Bits32(tv[1])
    assert m.out_bar == Bits32(tv[2])
  a._test_vectors = [
    [       B(),            0,    0 ],
    [    B( C(2),  1 ),     1,    2 ],
    [   B( C(-2), -1 ),    -1,   -2 ],
    [   B( C(-3), -2 ),    -2,   -3 ],
    [   B( C(25), 24 ),    24,   25 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )

def test_packed_array( do_test ):
  @bitstruct
  class B:
    foo: [Bits32] * 2
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out =  [ OutPort( Bits32 ) for _ in range(2) ]
      connect( s.out[0], s.in_.foo[0] )
      connect( s.out[1], s.in_.foo[1] )
  a = A()
  _foo = rdt.PackedArray( [2], rdt.Vector(32) )
  a._ref_structs = [
    ( rdt.Struct( 'B', {'foo':_foo} ), \
"""\
typedef struct packed {
  logic [1:0][31:0] foo;
} B;
""" ) ]
  a._ref_ports = { a : \
"""\
  input logic [0:0] clk,
  input B in_,
  output logic [31:0] out [0:1],
  input logic [0:0] reset\
""" }
  a._ref_wires = { a : "" }
  a._ref_conns = { a : \
"""\
  assign out[0] = in_.foo[0];
  assign out[1] = in_.foo[1];\
""" }

  # Yosys backend test reference output
  a._ref_ports_port_yosys = { a : \
"""\
  input logic [0:0] clk,
  input logic [31:0] in___foo__0,
  input logic [31:0] in___foo__1,
  output logic [31:0] out__0,
  output logic [31:0] out__1,
  input logic [0:0] reset\
""" }
  a._ref_ports_wire_yosys = { a : \
"""\
  logic [31:0] in___foo [0:1];
  logic [63:0] in_;
  logic [31:0] out [0:1];\
""" }
  a._ref_ports_conn_yosys = { a : \
"""\
  assign in___foo[0] = in___foo__0;
  assign in___foo[1] = in___foo__1;
  assign in_[63:32] = in___foo__1;
  assign in_[31:0] = in___foo__0;
  assign out__0 = out[0];
  assign out__1 = out[1];\
""" }
  a._ref_wires_yosys = a._ref_wires
  a._ref_conns_yosys = { a : \
"""\
  assign out[0] = in___foo[0];
  assign out[1] = in___foo[1];\
""" }

  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = tv[0]
  def tv_out( m, tv ):
    assert m.out[0] == Bits32(tv[1])
    assert m.out[1] == Bits32(tv[2])
  a._test_vectors = [
    [       B(),                           0,    0 ],
    [    B(  [Bits32(1), Bits32(2)] ),     1,    2 ],
    [   B( [Bits32(-1), Bits32(-2)] ),    -1,   -2 ],
    [   B( [Bits32(-2), Bits32(-3)] ),    -2,   -3 ],
    [   B( [Bits32(24), Bits32(25)] ),    24,   25 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )

def test_struct_packed_array( do_test ):
  @bitstruct
  class C:
    bar: Bits32
  @bitstruct
  class B:
    c: [ C ] * 2
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out =  [ OutPort( Bits32 ) for _ in range(2) ]
      connect( s.out[0], s.in_.c[0].bar )
      connect( s.out[1], s.in_.c[1].bar )
  a = A()
  _C = rdt.Struct('C', {'bar':rdt.Vector(32)})
  a._ref_structs = [
    ( _C, \
"""\
typedef struct packed {
  logic [31:0] bar;
} C;
""" ),
    ( rdt.Struct( 'B', {'c':rdt.PackedArray([2], _C)} ), \
"""\
typedef struct packed {
  C [1:0] c;
} B;
""" ) ]
  a._ref_ports = { a : \
"""\
  input logic [0:0] clk,
  input B in_,
  output logic [31:0] out [0:1],
  input logic [0:0] reset\
""" }
  a._ref_wires = { a : "" }
  a._ref_conns = { a : \
"""\
  assign out[0] = in_.c[0].bar;
  assign out[1] = in_.c[1].bar;\
""" }

  # Yosys backend test reference output
  a._ref_ports_port_yosys = { a : \
"""\
  input logic [0:0] clk,
  input logic [31:0] in___c__0__bar,
  input logic [31:0] in___c__1__bar,
  output logic [31:0] out__0,
  output logic [31:0] out__1,
  input logic [0:0] reset\
""" }
  a._ref_ports_wire_yosys = { a : \
"""\
  logic [31:0] in___c__bar [0:1];
  logic [31:0] in___c [0:1];
  logic [63:0] in_;
  logic [31:0] out [0:1];\
""" }
  a._ref_ports_conn_yosys = { a : \
"""\
  assign in___c__bar[0] = in___c__0__bar;
  assign in___c[0][31:0] = in___c__0__bar;
  assign in___c__bar[1] = in___c__1__bar;
  assign in___c[1][31:0] = in___c__1__bar;
  assign in_[63:32] = in___c__1__bar;
  assign in_[31:0] = in___c__0__bar;
  assign out__0 = out[0];
  assign out__1 = out[1];\
""" }
  a._ref_wires_yosys = a._ref_wires
  a._ref_conns_yosys = { a : \
"""\
  assign out[0] = in___c__bar[0];
  assign out[1] = in___c__bar[1];\
""" }

  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = tv[0]
  def tv_out( m, tv ):
    assert m.out[0] == Bits32(tv[1])
    assert m.out[1] == Bits32(tv[2])
  a._test_vectors = [
    [       B(),     0,    0 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )
