#=========================================================================
# SVStructuralTranslatorL1_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 1 SystemVerilog structural translator."""

from pymtl import Component, Wire, InPort, OutPort, Bits1, Bits4, Bits32
from pymtl.passes.rtlir.test.test_utility import do_test
from pymtl.passes.sverilog.translation.structural.SVStructuralTranslatorL1 import \
    SVStructuralTranslatorL1

def local_do_test( m ):
  m.elaborate()
  tr = SVStructuralTranslatorL1( m )
  tr.translate_structural( m )

  ports = tr.structural.decl_ports[m]
  assert ports == m._ref_ports[m]
  wires = tr.structural.decl_wires[m]
  assert wires == m._ref_wires[m]
  consts = tr.structural.decl_consts[m]
  assert consts == m._ref_consts[m]
  conns = tr.structural.connections[m]
  assert conns == m._ref_conns[m]

def test_port_wire( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.wire = Wire( Bits32 )
      s.out = OutPort( Bits32 )
      s.connect( s.in_, s.wire )
      s.connect( s.wire, s.out )
  a = A()
  a._ref_ports = { a : \
"""\
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [31:0] out,
  input logic [0:0] reset\
"""
}
  a._ref_wires = { a : \
"""\
  logic [31:0] wire;\
"""
}
  a._ref_consts = { a : "" }
  a._ref_conns = { a : \
"""\
  assign wire = in_;
  assign out = wire;\
"""
}
  do_test( a )

def test_connect_constant( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      s.connect( 42, s.out )
  a = A()
  a._ref_ports = { a : \
"""\
  input logic [0:0] clk,
  output logic [31:0] out,
  input logic [0:0] reset\
"""
}
  a._ref_wires = { a : "" }
  a._ref_consts = { a : "" }
  a._ref_conns = { a : \
"""\
  assign out = 32'd42;\
"""
}
  do_test( a )

def test_port_const( do_test ):
  class A( Component ):
    def construct( s ):
      s.STATE_IDLE = 42
      s.out = OutPort( Bits32 )
      s.connect( s.STATE_IDLE, s.out )
  a = A()
  a._ref_ports = { a : \
"""\
  input logic [0:0] clk,
  output logic [31:0] out,
  input logic [0:0] reset\
"""
}
  a._ref_wires = { a : "" }
  a._ref_consts = { a : \
"""\
  localparam [31:0] STATE_IDLE = 32'd42;\
"""
}
  # Structural reference to constant number will be replaced
  # with that constant value. This is because the DSL does not
  # add a `my_name` field in _dsl for constant numbers...
  # You can still refer to this constant number in upblks because
  # we define that as a localparam.
  a._ref_conns = { a : \
"""\
  assign out = 32'd42;\
"""
}
  do_test( a )

def test_port_const_array( do_test ):
  class A( Component ):
    def construct( s ):
      s.STATES = [ 1, 2, 3, 4, 5 ]
      s.out = [ OutPort( Bits32 ) for _ in xrange(5) ]
      for i in xrange(5):
        s.connect( s.STATES[i], s.out[i] )
  a = A()
  a._ref_ports = { a : \
"""\
  input logic [0:0] clk,
  output logic [31:0] out [0:4],
  input logic [0:0] reset\
"""
}
  a._ref_wires = { a : "" }
  a._ref_consts = { a : \
"""\
  localparam [31:0] STATES [0:4] = { 32'd1, 32'd2, 32'd3, 32'd4, 32'd5 };\
"""
}
  # Structural reference to constant number will be replaced
  # with that constant value. This is because the DSL does not
  # add a `my_name` field in _dsl for constant numbers...
  # You can still refer to this constant number in upblks because
  # we define that as a localparam.
  a._ref_conns = { a : \
"""\
  assign out[0] = 32'd1;
  assign out[1] = 32'd2;
  assign out[2] = 32'd3;
  assign out[3] = 32'd4;
  assign out[4] = 32'd5;\
"""
}
  do_test( a )

def test_port_bit_selection( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      s.connect( s.out, s.in_[2] )
  a = A()
  a._ref_ports = { a : \
"""\
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [0:0] out,
  input logic [0:0] reset\
"""
}
  a._ref_wires = { a : "" }
  a._ref_consts = { a : "" }
  # DSL treats a bit selection as a one-bit part selection
  a._ref_conns = { a : \
"""\
  assign out = in_[2:2];\
"""
}
  do_test( a )

def test_port_part_selection( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits4 )
      s.connect( s.out, s.in_[2:6] )
  a = A()
  a._ref_ports = { a : \
"""\
  input logic [0:0] clk,
  input logic [31:0] in_,
  output logic [3:0] out,
  input logic [0:0] reset\
"""
}
  a._ref_wires = { a : "" }
  a._ref_consts = { a : "" }
  # DSL treats a bit selection as a one-bit part selection
  a._ref_conns = { a : \
"""\
  assign out = in_[5:2];\
"""
}
  do_test( a )

def test_port_wire_array_index( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = [ OutPort( Bits32 ) for _ in xrange(5) ]
      s.wire = [ Wire(Bits32) for _ in xrange(5) ]
      for i in xrange(5):
        s.connect( s.wire[i], s.out[i] )
        s.connect( s.wire[i], i )
  a = A()
  a._ref_ports = { a : \
"""\
  input logic [0:0] clk,
  output logic [31:0] out [0:4],
  input logic [0:0] reset\
"""
}
  a._ref_wires = { a : \
"""\
  logic [31:0] wire [0:4];\
"""
}
  a._ref_consts = { a : "" }
  # DSL treats a bit selection as a one-bit part selection
  a._ref_conns = { a : \
"""\
  assign out[0] = wire[0];
  assign wire[0] = 32'd0;
  assign out[1] = wire[1];
  assign wire[1] = 32'd1;
  assign out[2] = wire[2];
  assign wire[2] = 32'd2;
  assign out[3] = wire[3];
  assign wire[3] = 32'd3;
  assign out[4] = wire[4];
  assign wire[4] = 32'd4;\
"""
}
  do_test( a )
