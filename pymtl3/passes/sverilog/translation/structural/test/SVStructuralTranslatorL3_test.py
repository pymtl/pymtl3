#=========================================================================
# SVStructuralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 3 SystemVerilog structural translator."""

from pymtl3.datatypes import Bits1, Bits32
from pymtl3.dsl import Component, InPort, Interface, OutPort, connect
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.structural.SVStructuralTranslatorL3 import (
    SVStructuralTranslatorL3,
)

from .SVStructuralTranslatorL1_test import check_eq, is_sverilog_reserved


def local_do_test( m ):
  m.elaborate()
  SVStructuralTranslatorL3.is_sverilog_reserved = is_sverilog_reserved
  tr = SVStructuralTranslatorL3( m )
  tr.clear( m )
  tr.translate_structural( m )

  ifcs = tr.structural.decl_ifcs[m]
  conns = tr.structural.connections[m]
  check_eq( ifcs, m._ref_ifcs[m] )
  check_eq( conns, m._ref_conns[m] )

def test_ifc_decls( do_test ):
  class Ifc( Interface ):
    def construct( s ):
      s.msg = OutPort( Bits32 )
      s.val = OutPort( Bits1 )
      s.rdy = InPort( Bits1 )
  class A( Component ):
    def construct( s ):
      s.ifc = Ifc()
      # This 42 will be converted to Bits32(42) by DSL
      connect( s.ifc.msg, 42 )
      # This 1 will be converted to Bits1(1) by DSL
      connect( s.ifc.val, 1 )
  a = A()
  a._ref_ifcs = { a : \
"""\
  output logic [31:0] ifc__msg,
  input logic [0:0] ifc__rdy,
  output logic [0:0] ifc__val\
""" }
  a._ref_conns = { a : \
"""\
  assign ifc__msg = 32'd42;
  assign ifc__val = 1'd1;\
""" }

  # Yosys backend test reference output
  a._ref_ifcs_port_yosys = a._ref_ifcs
  a._ref_ifcs_wire_yosys = { a : "" }
  a._ref_ifcs_conn_yosys = { a : "" }
  a._ref_conns_yosys = a._ref_conns

  # TestVectorSimulator properties
  def tv_in( m, tv ):
    pass
  def tv_out( m, tv ):
    assert m.ifc.msg == Bits32(42)
    assert m.ifc.val == Bits1(1)
  a._test_vectors = []
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )

def test_multi_ifc_decls( do_test ):
  class InIfc( Interface ):
    def construct( s ):
      s.msg = InPort( Bits32 )
      s.val = InPort( Bits1 )
      s.rdy = OutPort( Bits1 )
  class OutIfc( Interface ):
    def construct( s ):
      s.msg = OutPort( Bits32 )
      s.val = OutPort( Bits1 )
      s.rdy = InPort( Bits1 )
  class A( Component ):
    def construct( s ):
      s.in_ = InIfc()
      s.out = OutIfc()
      connect( s.out, s.in_ )
  a = A()
  a._ref_ifcs = { a : \
"""\
  input logic [31:0] in___msg,
  output logic [0:0] in___rdy,
  input logic [0:0] in___val,
  output logic [31:0] out__msg,
  input logic [0:0] out__rdy,
  output logic [0:0] out__val\
""" }
  a._ref_conns = { a : \
"""\
  assign out__msg = in___msg;
  assign in___rdy = out__rdy;
  assign out__val = in___val;\
""" }

  # Yosys backend test reference output
  a._ref_ifcs_port_yosys = a._ref_ifcs
  a._ref_ifcs_wire_yosys = { a : "" }
  a._ref_ifcs_conn_yosys = { a : "" }
  a._ref_conns_yosys = a._ref_conns

  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_.val = Bits1(tv[0])
    m.in_.msg = Bits32(tv[1])
    m.out.rdy = Bits1(tv[2])
  def tv_out( m, tv ):
    assert m.out.val == Bits1(tv[3])
    assert m.out.msg == Bits32(tv[4])
    assert m.in_.rdy == Bits1(tv[5])
  a._test_vectors = [
    [    0,    42,   1,    0,    42,    1 ],
    [    1,    -1,   1,    1,    -1,    1 ],
    [    1,    -2,   0,    1,    -2,    0 ],
    [    0,     2,   0,    0,     2,    0 ],
    [    1,    24,   1,    1,    24,    1 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )
