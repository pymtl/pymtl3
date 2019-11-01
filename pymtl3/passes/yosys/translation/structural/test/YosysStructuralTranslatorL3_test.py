#=========================================================================
# YosysStructuralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 13, 2019
"""Test the level 3 yosys-SystemVerilog structural translator."""

from pymtl3.datatypes import Bits1, Bits32, bitstruct
from pymtl3.dsl import Component, InPort, Interface, OutPort, connect
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.structural.test.SVStructuralTranslatorL1_test import (
    check_eq,
    is_sverilog_reserved,
)
from pymtl3.passes.sverilog.translation.structural.test.SVStructuralTranslatorL3_test import (
    test_ifc_decls,
    test_multi_ifc_decls,
)
from pymtl3.passes.yosys.translation.structural.YosysStructuralTranslatorL3 import (
    YosysStructuralTranslatorL3,
)


def local_do_test( m ):
  m.elaborate()
  YosysStructuralTranslatorL3.is_sverilog_reserved = is_sverilog_reserved
  tr = YosysStructuralTranslatorL3( m )
  tr.clear( m )
  tr.translate_structural( m )

  ports = tr.structural.decl_ifcs[m]
  conns = tr.structural.connections[m]

  check_eq( ports["port_decls"], m._ref_ifcs_port_yosys[m] )
  check_eq( ports["wire_decls"], m._ref_ifcs_wire_yosys[m] )
  check_eq( ports["connections"], m._ref_ifcs_conn_yosys[m] )
  check_eq( conns, m._ref_conns_yosys[m] )

def test_ifc_array( do_test ):
  class InValRdy( Interface ):
    def construct( s, Type ):
      s.msg = InPort( Type )
      s.val = InPort( Bits1 )
      s.rdy = OutPort( Bits1 )
  class OutValRdy( Interface ):
    def construct( s, Type ):
      s.msg = OutPort( Type )
      s.val = OutPort( Bits1 )
      s.rdy = InPort( Bits1 )
  class A( Component ):
    def construct( s ):
      s.in_ = [ InValRdy( Bits32 ) for _ in range(2) ]
      s.out = [ OutValRdy( Bits32 ) for _ in range(2) ]
      s.sel = InPort( Bits1 )
      s.out_sel = OutPort( Bits32 )
      connect( s.out[0], s.in_[1] )
      connect( s.out[1], s.in_[0] )
      @s.update
      def upblk():
        s.out_sel = s.in_[ s.sel ].msg
  a = A()
  a._ref_ifcs_port_yosys = { a : \
"""\
  input logic [31:0] in___0__msg,
  input logic [31:0] in___1__msg,
  output logic [0:0] in___0__rdy,
  output logic [0:0] in___1__rdy,
  input logic [0:0] in___0__val,
  input logic [0:0] in___1__val,
  output logic [31:0] out__0__msg,
  output logic [31:0] out__1__msg,
  input logic [0:0] out__0__rdy,
  input logic [0:0] out__1__rdy,
  output logic [0:0] out__0__val,
  output logic [0:0] out__1__val\
""" }
  a._ref_ifcs_wire_yosys = { a : \
"""\
  logic [31:0] in___msg [0:1];
  logic [0:0] in___rdy [0:1];
  logic [0:0] in___val [0:1];
  logic [31:0] out__msg [0:1];
  logic [0:0] out__rdy [0:1];
  logic [0:0] out__val [0:1];\
""" }
  a._ref_ifcs_conn_yosys = { a : \
"""\
  assign in___msg[0] = in___0__msg;
  assign in___msg[1] = in___1__msg;
  assign in___0__rdy = in___rdy[0];
  assign in___1__rdy = in___rdy[1];
  assign in___val[0] = in___0__val;
  assign in___val[1] = in___1__val;
  assign out__0__msg = out__msg[0];
  assign out__1__msg = out__msg[1];
  assign out__rdy[0] = out__0__rdy;
  assign out__rdy[1] = out__1__rdy;
  assign out__0__val = out__val[0];
  assign out__1__val = out__val[1];\
"""
}
  a._ref_conns_yosys = { a : \
"""\
  assign out__msg[0] = in___msg[1];
  assign in___rdy[1] = out__rdy[0];
  assign out__val[0] = in___val[1];
  assign out__msg[1] = in___msg[0];
  assign in___rdy[0] = out__rdy[1];
  assign out__val[1] = in___val[0];\
""" }

  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.sel = Bits1(tv[0])
    m.in_[0].msg = Bits32(tv[1])
    m.in_[1].msg = Bits32(tv[2])
  def tv_out( m, tv ):
    assert m.out[0].msg == Bits32(tv[3])
    assert m.out[1].msg == Bits32(tv[4])
    assert m.out_sel == Bits32(tv[5])
  a._test_vectors = [
    [    0,    42,   1,    1,    42,   42 ],
    [    1,    -1,   1,    1,    -1,    1 ],
    [    1,    -2,   0,    0,    -2,    0 ],
    [    0,     2,   0,    0,     2,    2 ],
    [    1,    24,   1,    1,    24,    1 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )

def test_struct_ifc( do_test ):
  @bitstruct
  class bstruct:
    bar: Bits32
  class Ifc( Interface ):
    def construct( s ):
      s.foo = InPort( bstruct )
  class A( Component ):
    def construct( s ):
      s.in_ = [ Ifc() for _ in range(2) ]
      s.out = OutPort( Bits32 )
      connect( s.out, s.in_[1].foo.bar )
  a = A()
  a._ref_ifcs_port_yosys = { a : \
"""\
  input logic [31:0] in___0__foo__bar,
  input logic [31:0] in___1__foo__bar\
""" }
  a._ref_ifcs_wire_yosys = { a : \
"""\
  logic [31:0] in___foo__bar [0:1];
  logic [31:0] in___foo [0:1];\
""" }
  a._ref_ifcs_conn_yosys = { a : \
"""\
  assign in___foo__bar[0] = in___0__foo__bar;
  assign in___foo__bar[1] = in___1__foo__bar;
  assign in___foo[0][31:0] = in___0__foo__bar;
  assign in___foo[1][31:0] = in___1__foo__bar;\
"""
}
  a._ref_conns_yosys = { a : \
"""\
  assign out = in___foo__bar[1];\
""" }

  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_[0].foo.bar = Bits32(tv[0])
    m.in_[1].foo.bar = Bits32(tv[1])
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[2])
  a._test_vectors = [
    [    42,   1,     1 ],
    [    -1,   1,     1 ],
    [    -2,  42,    42 ],
    [     2,   0,     0 ],
    [    24,  -1,    -1 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )
