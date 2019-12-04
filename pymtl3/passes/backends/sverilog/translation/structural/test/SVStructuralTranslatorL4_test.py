#=========================================================================
# SVStructuralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 4 SystemVerilog structural translator."""

from pymtl3.datatypes import Bits1, Bits32
from pymtl3.dsl import Component, InPort, Interface, OutPort, connect
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.structural.SVStructuralTranslatorL4 import (
    SVStructuralTranslatorL4,
)

from .SVStructuralTranslatorL1_test import check_eq, is_sverilog_reserved


def local_do_test( m ):
  m.elaborate()
  SVStructuralTranslatorL4.is_sverilog_reserved = is_sverilog_reserved
  tr = SVStructuralTranslatorL4( m )
  tr.clear( m )
  tr.translate_structural( m )
  subcomps = tr.structural.decl_subcomps
  for comp in m._ref_subcomps.keys():
    check_eq( subcomps[comp], m._ref_subcomps[comp] )

def test_subcomp_decl( do_test ):
  class B( Component ):
    def construct( s ):
      s.out_b = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out_b = Bits32(0)
  class A( Component ):
    def construct( s ):
      s.out_a = OutPort( Bits32 )
      s.b = B()
      connect( s.b.out_b, s.out_a )
  a = A()
  a._ref_subcomps = { a : \
"""\
  logic [0:0] b__clk;
  logic [31:0] b__out_b;
  logic [0:0] b__reset;

  B b
  (
    .clk( b__clk ),
    .out_b( b__out_b ),
    .reset( b__reset )
  );\
"""
}

  a._ref_comps_port_yosys = a._ref_subcomps
  a._ref_comps_wire_yosys = { a : "" }
  a._ref_comps_conn_yosys = { a : "" }

  # TestVectorSimulator properties
  def tv_in( m, tv ):
    pass
  def tv_out( m, tv ):
    assert m.out_a == Bits32(tv[0])
  a._test_vectors = [
    [    0   ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )

def test_multi_components_ifc_hierarchy_connect( do_test ):
  class OutIfc( Interface ):
    def construct( s ):
      s.msg = OutPort( Bits32 )
      s.rdy = InPort( Bits1 )
      s.val = OutPort( Bits1 )
  class B( Component ):
    def construct( s ):
      s.out_b = OutPort( Bits32 )
      s.ifc_b = OutIfc()
      connect( s.out_b, 0 )
      connect( s.ifc_b.msg, 0 )
      connect( s.ifc_b.val, 1 )
  class A( Component ):
    def construct( s ):
      s.out_a = OutPort( Bits32 )
      s.b = B()
      s.ifc_a = OutIfc()
      connect( s.b.out_b, s.out_a )
      connect( s.b.ifc_b, s.ifc_a )
  a = A()
  a._ref_subcomps = { a : \
"""\
  logic [0:0] b__clk;
  logic [31:0] b__out_b;
  logic [0:0] b__reset;
  logic [31:0] b__ifc_b__msg;
  logic [0:0] b__ifc_b__rdy;
  logic [0:0] b__ifc_b__val;

  B b
  (
    .clk( b__clk ),
    .out_b( b__out_b ),
    .reset( b__reset ),
    .ifc_b__msg( b__ifc_b__msg ),
    .ifc_b__rdy( b__ifc_b__rdy ),
    .ifc_b__val( b__ifc_b__val )
  );\
"""
}

  a._ref_comps_port_yosys = a._ref_subcomps
  a._ref_comps_wire_yosys = { a : "" }
  a._ref_comps_conn_yosys = { a : "" }

  # TestVectorSimulator properties
  def tv_in( m, tv ):
    pass
  def tv_out( m, tv ):
    assert m.out_a == Bits32(0)
    assert m.ifc_a.msg == Bits32(0)
    assert m.ifc_a.val == Bits32(1)
  a._test_vectors = []
  a._tv_in, a._tv_out = tv_in, tv_out
  do_test( a )
