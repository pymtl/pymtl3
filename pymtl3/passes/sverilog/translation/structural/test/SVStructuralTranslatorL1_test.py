#=========================================================================
# SVStructuralTranslatorL1_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 1 SystemVerilog structural translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits1, Bits4, Bits32
from pymtl3.dsl import Component, InPort, OutPort, Wire
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.structural.SVStructuralTranslatorL1 import (
    SVStructuralTranslatorL1,
)


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
      s.wire_ = Wire( Bits32 )
      s.out = OutPort( Bits32 )
      s.connect( s.in_, s.wire_ )
      s.connect( s.wire_, s.out )
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
  logic [31:0] wire_;\
"""
}
  a._ref_consts = { a : "" }
  a._ref_conns = { a : \
"""\
  assign wire_ = in_;
  assign out = wire_;\
"""
}
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = Bits32(tv[0])
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[1])
  a._test_vectors = [
    [    0,   0 ],
    [   42,   42 ],
    [   24,   24 ],
    [   -2,   -2 ],
    [   -1,   -1 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    pass
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[0])
  a._test_vectors = [
    [    42  ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    pass
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[0])
  a._test_vectors = [
    [    42  ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
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
  localparam [31:0] STATES [0:4] = '{ 32'd1, 32'd2, 32'd3, 32'd4, 32'd5 };\
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    pass
  def tv_out( m, tv ):
    assert m.out[0] == Bits32(tv[0])
    assert m.out[1] == Bits32(tv[1])
    assert m.out[2] == Bits32(tv[2])
    assert m.out[3] == Bits32(tv[3])
    assert m.out[4] == Bits32(tv[4])
  a._test_vectors = [
    [ 1, 2, 3, 4, 5 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = Bits32(tv[0])
  def tv_out( m, tv ):
    assert m.out == Bits1(tv[1])
  a._test_vectors = [
    [    0,   0, ],
    [    1,   0, ],
    [    2,   0, ],
    [    3,   0, ],
    [   -1,   1, ],
    [   -2,   1, ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = Bits32(tv[0])
  def tv_out( m, tv ):
    assert m.out == Bits4(tv[1])
  a._test_vectors = [
    [    0,   0, ],
    [    1,   0, ],
    [    2,   0, ],
    [    3,   0, ],
    [   -1,  -1, ],
    [   -2,  -1, ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )

def test_port_wire_array_index( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = [ OutPort( Bits32 ) for _ in xrange(5) ]
      s.wire_ = [ Wire(Bits32) for _ in xrange(5) ]
      for i in xrange(5):
        s.connect( s.wire_[i], s.out[i] )
        s.connect( s.wire_[i], i )
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
  logic [31:0] wire_ [0:4];\
"""
}
  a._ref_consts = { a : "" }
  # DSL treats a bit selection as a one-bit part selection
  a._ref_conns = { a : \
"""\
  assign out[0] = wire_[0];
  assign wire_[0] = 32'd0;
  assign out[1] = wire_[1];
  assign wire_[1] = 32'd1;
  assign out[2] = wire_[2];
  assign wire_[2] = 32'd2;
  assign out[3] = wire_[3];
  assign wire_[3] = 32'd3;
  assign out[4] = wire_[4];
  assign wire_[4] = 32'd4;\
"""
}
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    pass
  def tv_out( m, tv ):
    assert m.out[0] == Bits32(tv[0])
    assert m.out[1] == Bits32(tv[1])
    assert m.out[2] == Bits32(tv[2])
    assert m.out[3] == Bits32(tv[3])
    assert m.out[4] == Bits32(tv[4])
  a._test_vectors = [
    [    0,    1,   2,   3,   4 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )
