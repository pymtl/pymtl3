#=========================================================================
# SVStructuralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 4 SystemVerilog structural translator."""

from __future__ import absolute_import, division, print_function

from pymtl import Bits1, Bits32, Component, InPort, Interface, OutPort
from pymtl.passes.rtlir.test.test_utility import do_test
from pymtl.passes.sverilog.translation.structural.SVStructuralTranslatorL4 import (
    SVStructuralTranslatorL4,
)


def local_do_test( m ):
  m.elaborate()
  tr = SVStructuralTranslatorL4( m )
  tr.translate_structural( m )
  subcomps = tr.structural.decl_subcomps
  for comp in m._ref_subcomps.keys():
    assert subcomps[comp] == m._ref_subcomps[comp]

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
      s.connect( s.b.out_b, s.out_a )
  a = A()
  a._ref_subcomps = { a : \
"""\
  logic [0:0] b$clk;
  logic [31:0] b$out_b;
  logic [0:0] b$reset;

  B b (
    .clk( b$clk ),
    .out_b( b$out_b ),
    .reset( b$reset )
  );\
"""
}
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
      s.connect( s.out_b, 0 )
      s.connect( s.ifc_b.msg, 0 )
      s.connect( s.ifc_b.val, 1 )
  class A( Component ):
    def construct( s ):
      s.out_a = OutPort( Bits32 )
      s.b = B()
      s.ifc_a = OutIfc()
      s.connect( s.b.out_b, s.out_a )
      s.connect( s.b.ifc_b, s.ifc_a )
  a = A()
  a._ref_subcomps = { a : \
"""\
  logic [0:0] b$clk;
  logic [31:0] b$out_b;
  logic [0:0] b$reset;
  logic [31:0] b$ifc_b_$msg;
  logic [0:0] b$ifc_b_$rdy;
  logic [0:0] b$ifc_b_$val;

  B b (
    .clk( b$clk ),
    .out_b( b$out_b ),
    .reset( b$reset ),
    .ifc_b_$msg( b$ifc_b_$msg ),
    .ifc_b_$rdy( b$ifc_b_$rdy ),
    .ifc_b_$val( b$ifc_b_$val )
  );\
"""
}
