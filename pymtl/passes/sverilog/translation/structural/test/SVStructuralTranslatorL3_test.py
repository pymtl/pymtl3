#=========================================================================
# SVStructuralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 29, 2019
"""Test the level 3 SystemVerilog structural translator."""

from pymtl import Component, Interface, InPort, OutPort, Bits1, Bits32
from pymtl.passes.rtlir.test.test_utility import do_test
from pymtl.passes.rtlir import RTLIRDataType as rdt
from pymtl.passes.sverilog.translation.structural.SVStructuralTranslatorL3 import \
    SVStructuralTranslatorL3

def local_do_test( m ):
  m.elaborate()
  tr = SVStructuralTranslatorL3( m )
  tr.translate_structural( m )

  ifcs = tr.structural.decl_ifcs[m]
  assert ifcs == m._ref_ifcs[m]
  conns = tr.structural.connections[m]
  assert conns == m._ref_conns[m]

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
      s.connect( s.ifc.msg, 42 )
      # This 1 will be converted to Bits1(1) by DSL
      s.connect( s.ifc.val, 1 )
  a = A()
  a._ref_ifcs = { a : \
"""\
  output logic [31:0] ifc_$msg,
  input logic [0:0] ifc_$rdy,
  output logic [0:0] ifc_$val\
"""
}
  a._ref_conns = { a : \
"""\
  assign ifc_$msg = 32'd42;
  assign ifc_$val = 1'd1;\
"""
}
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
      s.connect( s.out, s.in_ )
  a = A()
  a._ref_ifcs = { a : \
"""\
  input logic [31:0] in__$msg,
  output logic [0:0] in__$rdy,
  input logic [0:0] in__$val,
  output logic [31:0] out_$msg,
  input logic [0:0] out_$rdy,
  output logic [0:0] out_$val\
"""
}
  a._ref_conns = { a : \
"""\
  assign out_$msg = in__$msg;
  assign in__$rdy = out_$rdy;
  assign out_$val = in__$val;\
"""
}
  do_test( a )
