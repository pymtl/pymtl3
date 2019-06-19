#=========================================================================
# YosysStructuralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 13, 2019
"""Test the level 4 yosys-SystemVerilog structural translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits1, Bits32, BitStruct
from pymtl3.dsl import Component, InPort, Interface, OutPort
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.structural.test.SVStructuralTranslatorL1_test import (
    check_eq,
    is_sverilog_reserved,
)
from pymtl3.passes.sverilog.translation.structural.test.SVStructuralTranslatorL4_test import (
    test_multi_components_ifc_hierarchy_connect,
    test_subcomp_decl,
)
from pymtl3.passes.yosys.translation.structural.YosysStructuralTranslatorL4 import (
    YosysStructuralTranslatorL4,
)


def local_do_test( m ):
  m.elaborate()
  YosysStructuralTranslatorL4.is_sverilog_reserved = is_sverilog_reserved
  tr = YosysStructuralTranslatorL4( m )
  tr.clear( m )
  tr.translate_structural( m )

  comps = tr.structural.decl_subcomps[m]

  check_eq( comps["port_decls"], m._ref_comps_port_yosys[m] )
  check_eq( comps["wire_decls"], m._ref_comps_wire_yosys[m] )
  check_eq( comps["connections"], m._ref_comps_conn_yosys[m] )

def test_comp_array( do_test ):
  class B( Component ):
    def construct( s ):
      s.foo = OutPort( Bits32 )
      s.connect( s.foo, 0 )
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      s.b = [ B() for _ in range(2) ]
      s.connect( s.out, s.b[1].foo )
  a = A()
  a._ref_comps_port_yosys = { a : \
"""\
  logic [0:0] b$__0$clk;
  logic [31:0] b$__0$foo;
  logic [0:0] b$__0$reset;

  B b$__0
  (
    .clk( b$__0$clk ),
    .foo( b$__0$foo ),
    .reset( b$__0$reset )
  );

  logic [0:0] b$__1$clk;
  logic [31:0] b$__1$foo;
  logic [0:0] b$__1$reset;

  B b$__1
  (
    .clk( b$__1$clk ),
    .foo( b$__1$foo ),
    .reset( b$__1$reset )
  );\
""" }
  a._ref_comps_wire_yosys = { a : \
"""\
  logic [0:0] b$clk [0:1];
  logic [31:0] b$foo [0:1];
  logic [0:0] b$reset [0:1];\
""" }
  a._ref_comps_conn_yosys = { a : \
"""\
  assign b$__0$clk = b$clk[0];
  assign b$__1$clk = b$clk[1];
  assign b$foo[0] = b$__0$foo;
  assign b$foo[1] = b$__1$foo;
  assign b$__0$reset = b$reset[0];
  assign b$__1$reset = b$reset[1];\
"""
}
  a._ref_conns_yosys = { a : \
"""\
  assign out = b$foo[1];\
""" }

  # TestVectorSimulator properties
  def tv_in( m, tv ):
    pass
  def tv_out( m, tv ):
    assert m.out == Bits32(0)
  a._test_vectors = []
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )

def test_comp_array_ifc_array_port_array_packed_array( do_test ):
  class bstruct( BitStruct ):
    def __init__( s, bar=42 ):
      s.bar = [ Bits32(bar) for _ in range(1) ]
  class Ifc( Interface ):
    def construct( s ):
      s.foo = [ InPort( bstruct ) for _ in range(1) ]
  class B( Component ):
    def construct( s ):
      s.ifc = [ Ifc() for _ in range(1) ]
      s.out = OutPort( Bits32 )
      s.connect( s.out, s.ifc[0].foo[0].bar[0] )
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.b = [ B() for _ in range(1) ]
      s.out = OutPort( Bits32 )
      s.connect( s.in_, s.b[0].ifc[0].foo[0].bar[0] )
      s.connect( s.out, s.b[0].out )
  a = A()
  a._ref_comps_port_yosys = { a : \
"""\
  logic [0:0] b$__0$clk;
  logic [31:0] b$__0$out;
  logic [0:0] b$__0$reset;
  logic [31:0] b$__0$ifc$__0$foo$__0$bar$__0;

  B b$__0
  (
    .clk( b$__0$clk ),
    .out( b$__0$out ),
    .reset( b$__0$reset ),
    .ifc$__0$foo$__0$bar$__0( b$__0$ifc$__0$foo$__0$bar$__0 )
  );\
""" }
  a._ref_comps_wire_yosys = { a : \
"""\
  logic [0:0] b$clk [0:0];
  logic [31:0] b$out [0:0];
  logic [0:0] b$reset [0:0];
  logic [31:0] b$ifc$foo$bar [0:0][0:0][0:0][0:0];
  logic [31:0] b$ifc$foo [0:0][0:0][0:0];\
""" }
  a._ref_comps_conn_yosys = { a : \
"""\
  assign b$__0$clk = b$clk[0];
  assign b$out[0] = b$__0$out;
  assign b$__0$reset = b$reset[0];
  assign b$__0$ifc$__0$foo$__0$bar$__0 = b$ifc$foo$bar[0][0][0][0];
  assign b$__0$ifc$__0$foo$__0$bar$__0 = b$ifc$foo[0][0][0][31:0];\
"""
}
  a._ref_conns_yosys = { a : \
"""\
  assign b$ifc$foo$bar[0][0][0][0] = in_;
  assign out = b$out[0];\
""" }

  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.b[0].ifc[0].foo[0].bar[0] = Bits32(tv[0])
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[1])
  a._test_vectors = [
    [    42,  42 ],
    [    -1,  -1 ],
    [    -2,  -2 ],
    [     2,   2 ],
    [    24,  24 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )
