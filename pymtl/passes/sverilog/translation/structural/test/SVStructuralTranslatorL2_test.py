#=========================================================================
# SVStructuralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 2 SystemVerilog structural translator."""

from pymtl import Component, Wire, InPort, OutPort, Bits1, Bits32
from pymtl.passes.rtlir.test.test_utility import do_test
from pymtl.passes.rtlir import RTLIRDataType as rdt
from pymtl.passes.sverilog.translation.structural.SVStructuralTranslatorL2 import \
    SVStructuralTranslatorL2

def local_do_test( m ):
  m.elaborate()
  tr = SVStructuralTranslatorL2( m )
  tr.translate_structural( m )

  ports = tr.structural.decl_ports[m]
  assert ports == m._ref_ports[m]
  wires = tr.structural.decl_wires[m]
  assert wires == m._ref_wires[m]
  structs = tr.structural.decl_type_struct
  assert map(lambda x: x[0], structs) == map(lambda x: x[0], m._ref_structs)
  assert map(lambda x: x[1]['def'], structs) == map(lambda x: x[1], m._ref_structs)
  conns = tr.structural.connections[m]
  assert conns == m._ref_conns[m]

def test_struct_port( do_test ):
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = Bits32(foo)
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits32 )
      s.connect( s.out, s.in_.foo )
  a = A()
  a._ref_structs = [
    ( rdt.Struct( 'B', {'foo':rdt.Vector(32)}, ['foo'] ), \
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
"""
}
  a._ref_wires = { a : "" }
  a._ref_conns = { a : \
"""\
  assign out = in_.foo;\
"""
}
  do_test( a )

def test_nested_struct_port( do_test ):
  class C( object ):
    def __init__( s, bar=1 ):
      s.bar = Bits32(bar)
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = Bits32(foo)
      s.c = C()
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out_foo = OutPort( Bits32 )
      s.out_bar = OutPort( Bits32 )
      s.connect( s.out_foo, s.in_.foo )
      s.connect( s.out_bar, s.in_.c.bar )
  a = A()
  _C = rdt.Struct( 'C', {'bar':rdt.Vector(32)}, ['bar'] )
  a._ref_structs = [ ( _C, \
"""\
typedef struct packed {
  logic [31:0] bar;
} C;
""" ),
    ( rdt.Struct( 'B', {'c':_C, 'foo':rdt.Vector(32)}, ['c', 'foo'] ), \
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
"""
}
  a._ref_wires = { a : "" }
  a._ref_conns = { a : \
"""\
  assign out_foo = in_.foo;
  assign out_bar = in_.c.bar;\
"""
}
  do_test( a )

def test_packed_array( do_test ):
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = [ Bits32(foo) for _ in xrange(2) ]
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out =  [ OutPort( Bits32 ) for _ in xrange(2) ]
      s.connect( s.out[0], s.in_.foo[0] )
      s.connect( s.out[1], s.in_.foo[1] )
  a = A()
  _foo = rdt.PackedArray( [2], rdt.Vector(32) )
  a._ref_structs = [
    ( rdt.Struct( 'B', {'foo':_foo}, ['foo'] ), \
"""\
typedef struct packed {
  logic [31:0] foo [0:1];
} B;
""" ) ]
  a._ref_ports = { a : \
"""\
  input logic [0:0] clk,
  input B in_,
  output logic [31:0] out [0:1],
  input logic [0:0] reset\
"""
}
  a._ref_wires = { a : "" }
  a._ref_conns = { a : \
"""\
  assign out[0] = in_.foo[0];
  assign out[1] = in_.foo[1];\
"""
}
  do_test( a )

def test_struct_packed_array( do_test ):
  class C( object ):
    def __init__( s, bar=1 ):
      s.bar = Bits32(bar)
  class B( object ):
    def __init__( s ):
      s.c = [ C() for _ in xrange(2) ]
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out =  [ OutPort( Bits32 ) for _ in xrange(2) ]
      s.connect( s.out[0], s.in_.c[0].bar )
      s.connect( s.out[1], s.in_.c[1].bar )
  a = A()
  _C = rdt.Struct('C', {'bar':rdt.Vector(32)}, ['bar'])
  a._ref_structs = [
    ( _C, \
"""\
typedef struct packed {
  logic [31:0] bar;
} C;
""" ),
    ( rdt.Struct( 'B', {'c':rdt.PackedArray([2], _C)}, ['c'] ), \
"""\
typedef struct packed {
  C c [0:1];
} B;
""" ) ]
  a._ref_ports = { a : \
"""\
  input logic [0:0] clk,
  input B in_,
  output logic [31:0] out [0:1],
  input logic [0:0] reset\
"""
}
  a._ref_wires = { a : "" }
  a._ref_conns = { a : \
"""\
  assign out[0] = in_.c[0].bar;
  assign out[1] = in_.c[1].bar;\
"""
}
  do_test( a )
