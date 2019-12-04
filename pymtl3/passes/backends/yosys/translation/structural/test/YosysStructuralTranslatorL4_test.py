#=========================================================================
# YosysStructuralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 13, 2019
"""Test the level 4 yosys-SystemVerilog structural translator."""

from pymtl3.datatypes import Bits1, Bits32, bitstruct
from pymtl3.dsl import Component, InPort, Interface, OutPort, connect
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
      connect( s.foo, 0 )
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      s.b = [ B() for _ in range(2) ]
      connect( s.out, s.b[1].foo )
  a = A()
  a._ref_comps_port_yosys = { a : \
"""\
  logic [0:0] b__0__clk;
  logic [31:0] b__0__foo;
  logic [0:0] b__0__reset;

  B b__0
  (
    .clk( b__0__clk ),
    .foo( b__0__foo ),
    .reset( b__0__reset )
  );

  logic [0:0] b__1__clk;
  logic [31:0] b__1__foo;
  logic [0:0] b__1__reset;

  B b__1
  (
    .clk( b__1__clk ),
    .foo( b__1__foo ),
    .reset( b__1__reset )
  );\
""" }
  a._ref_comps_wire_yosys = { a : \
"""\
  logic [0:0] b__clk [0:1];
  logic [31:0] b__foo [0:1];
  logic [0:0] b__reset [0:1];\
""" }
  a._ref_comps_conn_yosys = { a : \
"""\
  assign b__0__clk = b__clk[0];
  assign b__1__clk = b__clk[1];
  assign b__foo[0] = b__0__foo;
  assign b__foo[1] = b__1__foo;
  assign b__0__reset = b__reset[0];
  assign b__1__reset = b__reset[1];\
"""
}
  a._ref_conns_yosys = { a : \
"""\
  assign out = b__foo[1];\
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
  @bitstruct
  class bstruct:
    bar: [ Bits32 ]
  class Ifc( Interface ):
    def construct( s ):
      s.foo = [ InPort( bstruct ) for _ in range(1) ]
  class B( Component ):
    def construct( s ):
      s.ifc = [ Ifc() for _ in range(1) ]
      s.out = OutPort( Bits32 )
      connect( s.out, s.ifc[0].foo[0].bar[0] )
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.b = [ B() for _ in range(1) ]
      s.out = OutPort( Bits32 )
      connect( s.in_, s.b[0].ifc[0].foo[0].bar[0] )
      connect( s.out, s.b[0].out )
  a = A()
  a._ref_comps_port_yosys = { a : \
"""\
  logic [0:0] b__0__clk;
  logic [31:0] b__0__out;
  logic [0:0] b__0__reset;
  logic [31:0] b__0__ifc__0__foo__0__bar__0;

  B b__0
  (
    .clk( b__0__clk ),
    .out( b__0__out ),
    .reset( b__0__reset ),
    .ifc__0__foo__0__bar__0( b__0__ifc__0__foo__0__bar__0 )
  );\
""" }
  a._ref_comps_wire_yosys = { a : \
"""\
  logic [0:0] b__clk [0:0];
  logic [31:0] b__out [0:0];
  logic [0:0] b__reset [0:0];
  logic [31:0] b__ifc__foo__bar [0:0][0:0][0:0][0:0];
  logic [31:0] b__ifc__foo [0:0][0:0][0:0];\
""" }
  a._ref_comps_conn_yosys = { a : \
"""\
  assign b__0__clk = b__clk[0];
  assign b__out[0] = b__0__out;
  assign b__0__reset = b__reset[0];
  assign b__0__ifc__0__foo__0__bar__0 = b__ifc__foo__bar[0][0][0][0];
  assign b__0__ifc__0__foo__0__bar__0 = b__ifc__foo[0][0][0][31:0];\
"""
}
  a._ref_conns_yosys = { a : \
"""\
  assign b__ifc__foo__bar[0][0][0][0] = in_;
  assign out = b__out[0];\
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
