#=========================================================================
# YosysStructuralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 13, 2019
"""Test the level 3 yosys-SystemVerilog structural translator."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits1, Bits32, BitStruct
from pymtl3.dsl import Component, InPort, Interface, OutPort
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
      s.connect( s.out[0], s.in_[1] )
      s.connect( s.out[1], s.in_[0] )
      @s.update
      def upblk():
        s.out_sel = s.in_[ s.sel ].msg
  a = A()
  a._ref_ifcs_port_yosys = { a : \
"""\
  input logic [31:0] in_$__0$msg,
  input logic [31:0] in_$__1$msg,
  output logic [0:0] in_$__0$rdy,
  output logic [0:0] in_$__1$rdy,
  input logic [0:0] in_$__0$val,
  input logic [0:0] in_$__1$val,
  output logic [31:0] out$__0$msg,
  output logic [31:0] out$__1$msg,
  input logic [0:0] out$__0$rdy,
  input logic [0:0] out$__1$rdy,
  output logic [0:0] out$__0$val,
  output logic [0:0] out$__1$val\
""" }
  a._ref_ifcs_wire_yosys = { a : \
"""\
  logic [31:0] in_$msg [0:1];
  logic [0:0] in_$rdy [0:1];
  logic [0:0] in_$val [0:1];
  logic [31:0] out$msg [0:1];
  logic [0:0] out$rdy [0:1];
  logic [0:0] out$val [0:1];\
""" }
  a._ref_ifcs_conn_yosys = { a : \
"""\
  assign in_$msg[0] = in_$__0$msg;
  assign in_$msg[1] = in_$__1$msg;
  assign in_$__0$rdy = in_$rdy[0];
  assign in_$__1$rdy = in_$rdy[1];
  assign in_$val[0] = in_$__0$val;
  assign in_$val[1] = in_$__1$val;
  assign out$__0$msg = out$msg[0];
  assign out$__1$msg = out$msg[1];
  assign out$rdy[0] = out$__0$rdy;
  assign out$rdy[1] = out$__1$rdy;
  assign out$__0$val = out$val[0];
  assign out$__1$val = out$val[1];\
"""
}
  a._ref_conns_yosys = { a : \
"""\
  assign out$msg[0] = in_$msg[1];
  assign in_$rdy[1] = out$rdy[0];
  assign out$val[0] = in_$val[1];
  assign out$msg[1] = in_$msg[0];
  assign in_$rdy[0] = out$rdy[1];
  assign out$val[1] = in_$val[0];\
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
  class bstruct( BitStruct ):
    def __init__( s, bar=42 ):
      s.bar = Bits32(bar)
  class Ifc( Interface ):
    def construct( s ):
      s.foo = InPort( bstruct )
  class A( Component ):
    def construct( s ):
      s.in_ = [ Ifc() for _ in range(2) ]
      s.out = OutPort( Bits32 )
      s.connect( s.out, s.in_[1].foo.bar )
  a = A()
  a._ref_ifcs_port_yosys = { a : \
"""\
  input logic [31:0] in_$__0$foo$bar,
  input logic [31:0] in_$__1$foo$bar\
""" }
  a._ref_ifcs_wire_yosys = { a : \
"""\
  logic [31:0] in_$foo$bar [0:1];
  logic [31:0] in_$foo [0:1];\
""" }
  a._ref_ifcs_conn_yosys = { a : \
"""\
  assign in_$foo$bar[0] = in_$__0$foo$bar;
  assign in_$foo$bar[1] = in_$__1$foo$bar;
  assign in_$foo[0][31:0] = in_$__0$foo$bar;
  assign in_$foo[1][31:0] = in_$__1$foo$bar;\
"""
}
  a._ref_conns_yosys = { a : \
"""\
  assign out = in_$foo$bar[1];\
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
