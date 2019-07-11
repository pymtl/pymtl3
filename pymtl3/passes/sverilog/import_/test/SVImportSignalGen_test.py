#=========================================================================
# SVImportSignalGen.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 1, 2019
"""Test the SystemVerilog signal generation of imported component."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits1, Bits32, BitStruct, mk_bits
from pymtl3.dsl import Component, InPort, Interface, OutPort
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.import_.ImportPass import ImportPass


def local_do_test( m ):
  m.elaborate()
  rtype = rt.get_component_ifc_rtlir( m )
  ipass = ImportPass()
  symbols, decls, conns = ipass.gen_signal_decl_py( rtype )
  assert symbols == m._ref_symbols
  assert decls == m._ref_decls
  assert conns == m._ref_conns

def test_port_single( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( mk_bits( 322 ) )
  a = A()
  a._ref_symbols = { 'Bits322' : mk_bits(322) }
  a._ref_decls = [
    "s.in_ = InPort( Bits322 )",
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk[0:1] )",
    "s.connect( s.in_, s.mangled__in_[0:322] )",
    "s.connect( s.reset, s.mangled__reset[0:1] )"
  ]
  a._ref_conns_yosys = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.in_, s.mangled__in_ )",
    "s.connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_port_array( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range( 3 ) ]
  a = A()
  a._ref_symbols = {}
  a._ref_decls = [
    "s.in_ = [ InPort( Bits32 ) for _ in range(3) ]",
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk[0:1] )",
    "s.connect( s.in_[0], s.mangled__in_[0][0:32] )",
    "s.connect( s.in_[1], s.mangled__in_[1][0:32] )",
    "s.connect( s.in_[2], s.mangled__in_[2][0:32] )",
    "s.connect( s.reset, s.mangled__reset[0:1] )"
  ]
  a._ref_conns_yosys = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.in_[0], s.mangled__in___024___05F0 )",
    "s.connect( s.in_[1], s.mangled__in___024___05F1 )",
    "s.connect( s.in_[2], s.mangled__in___024___05F2 )",
    "s.connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_port_2d_array( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ [ InPort( Bits32 ) for _ in range(2) ] for _ in range(3) ]
  a = A()
  a._ref_symbols = {}
  a._ref_decls = [
    "s.in_ = [ [ InPort( Bits32 ) for _ in range(2) ] for _ in range(3) ]",
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk[0:1] )",
    "s.connect( s.in_[0][0], s.mangled__in_[0][0][0:32] )",
    "s.connect( s.in_[0][1], s.mangled__in_[0][1][0:32] )",
    "s.connect( s.in_[1][0], s.mangled__in_[1][0][0:32] )",
    "s.connect( s.in_[1][1], s.mangled__in_[1][1][0:32] )",
    "s.connect( s.in_[2][0], s.mangled__in_[2][0][0:32] )",
    "s.connect( s.in_[2][1], s.mangled__in_[2][1][0:32] )",
    "s.connect( s.reset, s.mangled__reset[0:1] )"
  ]
  a._ref_conns_yosys = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.in_[0][0], s.mangled__in___024___05F0__024___05F0 )",
    "s.connect( s.in_[0][1], s.mangled__in___024___05F0__024___05F1 )",
    "s.connect( s.in_[1][0], s.mangled__in___024___05F1__024___05F0 )",
    "s.connect( s.in_[1][1], s.mangled__in___024___05F1__024___05F1 )",
    "s.connect( s.in_[2][0], s.mangled__in___024___05F2__024___05F0 )",
    "s.connect( s.in_[2][1], s.mangled__in___024___05F2__024___05F1 )",
    "s.connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_struct_port_single( do_test ):
  class struct( BitStruct ):
    def __init__( s, bar=1, foo=42 ):
      s.bar = Bits32(bar)
      s.foo = Bits32(foo)
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( struct )
  a = A()
  a._ref_symbols = { 'struct' : struct }
  a._ref_decls = [
    "s.in_ = InPort( struct )",
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk[0:1] )",
    "@s.update",
    "def in_():",
    "  s.mangled__in_[0:32] = s.in_.foo",
    "  s.mangled__in_[32:64] = s.in_.bar",
    "s.connect( s.reset, s.mangled__reset[0:1] )"
  ]
  a._ref_conns_yosys = [
    "s.connect( s.clk, s.mangled__clk )",
    "@s.update",
    "def in_():",
    "  s.mangled__in___024foo = s.in_.foo",
    "  s.mangled__in___024bar = s.in_.bar",
    "s.connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_struct_port_array( do_test ):
  class struct( BitStruct ):
    def __init__( s, bar=1, foo=42 ):
      s.bar = Bits32(bar)
      s.foo = Bits32(foo)
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( struct ) for _ in range(2) ]
  a = A()
  a._ref_symbols = { 'struct' : struct }
  a._ref_decls = [
    "s.in_ = [ InPort( struct ) for _ in range(2) ]",
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk[0:1] )",
    "@s.update",
    "def in__LBR_0_RBR_():",
    "  s.mangled__in_[0][0:32] = s.in_[0].foo",
    "  s.mangled__in_[0][32:64] = s.in_[0].bar",
    "@s.update",
    "def in__LBR_1_RBR_():",
    "  s.mangled__in_[1][0:32] = s.in_[1].foo",
    "  s.mangled__in_[1][32:64] = s.in_[1].bar",
    "s.connect( s.reset, s.mangled__reset[0:1] )"
  ]
  a._ref_conns_yosys = [
    "s.connect( s.clk, s.mangled__clk )",
    "@s.update",
    "def in__LBR_0_RBR_():",
    "  s.mangled__in___024___05F0__024foo = s.in_[0].foo",
    "  s.mangled__in___024___05F0__024bar = s.in_[0].bar",
    "@s.update",
    "def in__LBR_1_RBR_():",
    "  s.mangled__in___024___05F1__024foo = s.in_[1].foo",
    "  s.mangled__in___024___05F1__024bar = s.in_[1].bar",
    "s.connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_packed_array_port_array( do_test ):
  class struct( BitStruct ):
    def __init__( s, bar=1, foo=42 ):
      s.bar = Bits32(bar)
      s.foo = [ [ Bits32(foo) for _ in range(2) ] for _ in range(3) ]
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( struct ) for _ in range(2) ]
  a = A()
  a._ref_symbols = { 'struct' : struct }
  a._ref_decls = [
    "s.in_ = [ InPort( struct ) for _ in range(2) ]",
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk[0:1] )",
    "@s.update",
    "def in__LBR_0_RBR_():",
    "  s.mangled__in_[0][0:32] = s.in_[0].foo[0][0]",
    "  s.mangled__in_[0][32:64] = s.in_[0].foo[0][1]",
    "  s.mangled__in_[0][64:96] = s.in_[0].foo[1][0]",
    "  s.mangled__in_[0][96:128] = s.in_[0].foo[1][1]",
    "  s.mangled__in_[0][128:160] = s.in_[0].foo[2][0]",
    "  s.mangled__in_[0][160:192] = s.in_[0].foo[2][1]",
    "  s.mangled__in_[0][192:224] = s.in_[0].bar",
    "@s.update",
    "def in__LBR_1_RBR_():",
    "  s.mangled__in_[1][0:32] = s.in_[1].foo[0][0]",
    "  s.mangled__in_[1][32:64] = s.in_[1].foo[0][1]",
    "  s.mangled__in_[1][64:96] = s.in_[1].foo[1][0]",
    "  s.mangled__in_[1][96:128] = s.in_[1].foo[1][1]",
    "  s.mangled__in_[1][128:160] = s.in_[1].foo[2][0]",
    "  s.mangled__in_[1][160:192] = s.in_[1].foo[2][1]",
    "  s.mangled__in_[1][192:224] = s.in_[1].bar",
    "s.connect( s.reset, s.mangled__reset[0:1] )"
  ]
  a._ref_conns_yosys = [
    "s.connect( s.clk, s.mangled__clk )",
    "@s.update",
    "def in__LBR_0_RBR_():",
    "  s.mangled__in___024___05F0__024foo__024___05F0__024___05F0 = s.in_[0].foo[0][0]",
    "  s.mangled__in___024___05F0__024foo__024___05F0__024___05F1 = s.in_[0].foo[0][1]",
    "  s.mangled__in___024___05F0__024foo__024___05F1__024___05F0 = s.in_[0].foo[1][0]",
    "  s.mangled__in___024___05F0__024foo__024___05F1__024___05F1 = s.in_[0].foo[1][1]",
    "  s.mangled__in___024___05F0__024foo__024___05F2__024___05F0 = s.in_[0].foo[2][0]",
    "  s.mangled__in___024___05F0__024foo__024___05F2__024___05F1 = s.in_[0].foo[2][1]",
    "  s.mangled__in___024___05F0__024bar = s.in_[0].bar",
    "@s.update",
    "def in__LBR_1_RBR_():",
    "  s.mangled__in___024___05F1__024foo__024___05F0__024___05F0 = s.in_[1].foo[0][0]",
    "  s.mangled__in___024___05F1__024foo__024___05F0__024___05F1 = s.in_[1].foo[0][1]",
    "  s.mangled__in___024___05F1__024foo__024___05F1__024___05F0 = s.in_[1].foo[1][0]",
    "  s.mangled__in___024___05F1__024foo__024___05F1__024___05F1 = s.in_[1].foo[1][1]",
    "  s.mangled__in___024___05F1__024foo__024___05F2__024___05F0 = s.in_[1].foo[2][0]",
    "  s.mangled__in___024___05F1__024foo__024___05F2__024___05F1 = s.in_[1].foo[2][1]",
    "  s.mangled__in___024___05F1__024bar = s.in_[1].bar",
    "s.connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_nested_struct( do_test ):
  class inner_struct( BitStruct ):
    def __init__( s, foo = 42 ):
      s.foo = Bits32(foo)
  class struct( BitStruct ):
    def __init__( s, bar=1 ):
      s.bar = Bits32(bar)
      s.inner = inner_struct()
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( struct ) for _ in range(2) ]
  a = A()
  # Inner struct will not be added to `symbols` because struct
  # refers to it!
  a._ref_symbols = { 'struct' : struct }
  a._ref_decls = [
    "s.in_ = [ InPort( struct ) for _ in range(2) ]",
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk[0:1] )",
    "@s.update",
    "def in__LBR_0_RBR_():",
    "  s.mangled__in_[0][0:32] = s.in_[0].inner.foo",
    "  s.mangled__in_[0][32:64] = s.in_[0].bar",
    "@s.update",
    "def in__LBR_1_RBR_():",
    "  s.mangled__in_[1][0:32] = s.in_[1].inner.foo",
    "  s.mangled__in_[1][32:64] = s.in_[1].bar",
    "s.connect( s.reset, s.mangled__reset[0:1] )"
  ]
  a._ref_conns_yosys = [
    "s.connect( s.clk, s.mangled__clk )",
    "@s.update",
    "def in__LBR_0_RBR_():",
    "  s.mangled__in___024___05F0__024inner__024foo = s.in_[0].inner.foo",
    "  s.mangled__in___024___05F0__024bar = s.in_[0].bar",
    "@s.update",
    "def in__LBR_1_RBR_():",
    "  s.mangled__in___024___05F1__024inner__024foo = s.in_[1].inner.foo",
    "  s.mangled__in___024___05F1__024bar = s.in_[1].bar",
    "s.connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_interface( do_test ):
  class Ifc( Interface ):
    def construct( s ):
      s.msg = InPort( Bits32 )
      s.val = InPort( Bits1 )
      s.rdy = OutPort( Bits1 )
  class A( Component ):
    def construct( s ):
      s.ifc = Ifc()
  a = A()
  a._ref_symbols = { 'Ifc' : Ifc }
  a._ref_decls = [
    "s.ifc = Ifc()"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk[0:1] )",
    "s.connect( s.reset, s.mangled__reset[0:1] )",
    "s.connect( s.ifc.msg, s.mangled__ifc__024msg[0:32] )",
    "s.connect( s.ifc.rdy, s.mangled__ifc__024rdy[0:1] )",
    "s.connect( s.ifc.val, s.mangled__ifc__024val[0:1] )",
  ]
  a._ref_conns_yosys = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.reset, s.mangled__reset )",
    "s.connect( s.ifc.msg, s.mangled__ifc__024msg )",
    "s.connect( s.ifc.rdy, s.mangled__ifc__024rdy )",
    "s.connect( s.ifc.val, s.mangled__ifc__024val )",
  ]
  do_test( a )

def test_interface_parameter( do_test ):
  class Ifc( Interface ):
    def construct( s, Type, nbits_val, nbits_rdy ):
      s.msg = InPort( Type )
      s.val = InPort( mk_bits(nbits_val) )
      # Added support for BitsN values in case someone wants to do
      # tricky things like this.
      s.rdy = OutPort( mk_bits(nbits_rdy.nbits) )
  class A( Component ):
    def construct( s ):
      s.ifc = Ifc( Bits32, 1, Bits1(1) )
  a = A()
  a._ref_symbols = { 'Ifc' : Ifc }
  a._ref_decls = [
    "s.ifc = Ifc( Bits32, 1, Bits1( 1 ) )"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk[0:1] )",
    "s.connect( s.reset, s.mangled__reset[0:1] )",
    "s.connect( s.ifc.msg, s.mangled__ifc__024msg[0:32] )",
    "s.connect( s.ifc.rdy, s.mangled__ifc__024rdy[0:1] )",
    "s.connect( s.ifc.val, s.mangled__ifc__024val[0:1] )",
  ]
  a._ref_conns_yosys = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.reset, s.mangled__reset )",
    "s.connect( s.ifc.msg, s.mangled__ifc__024msg )",
    "s.connect( s.ifc.rdy, s.mangled__ifc__024rdy )",
    "s.connect( s.ifc.val, s.mangled__ifc__024val )",
  ]
  do_test( a )

def test_interface_parameter_long_vector( do_test ):
  class Ifc( Interface ):
    def construct( s, Type, nbits_val, nbits_rdy ):
      s.msg = InPort( Type )
      s.val = InPort( mk_bits(nbits_val) )
      # Added support for BitsN values in case someone wants to do
      # tricky things like this.
      s.rdy = OutPort( mk_bits(nbits_rdy.nbits) )
  class A( Component ):
    def construct( s ):
      Bits322 = mk_bits(322)
      s.ifc = Ifc( Bits322, 1, Bits322(1) )
  a = A()
  a._ref_symbols = { 'Ifc' : Ifc, 'Bits322' : mk_bits(322) }
  a._ref_decls = [
    "s.ifc = Ifc( Bits322, 1, Bits322( 1 ) )"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk[0:1] )",
    "s.connect( s.reset, s.mangled__reset[0:1] )",
    "s.connect( s.ifc.msg, s.mangled__ifc__024msg[0:322] )",
    "s.connect( s.ifc.rdy, s.mangled__ifc__024rdy[0:322] )",
    "s.connect( s.ifc.val, s.mangled__ifc__024val[0:1] )",
  ]
  a._ref_conns_yosys = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.reset, s.mangled__reset )",
    "s.connect( s.ifc.msg, s.mangled__ifc__024msg )",
    "s.connect( s.ifc.rdy, s.mangled__ifc__024rdy )",
    "s.connect( s.ifc.val, s.mangled__ifc__024val )",
  ]
  do_test( a )

def test_interface_array( do_test ):
  class Ifc( Interface ):
    def construct( s ):
      s.msg = InPort( Bits32 )
      s.val = InPort( Bits1 )
      s.rdy = OutPort( Bits1 )
  class A( Component ):
    def construct( s ):
      s.ifc = [ Ifc() for _ in range(2) ]
  a = A()
  a._ref_symbols = { 'Ifc' : Ifc }
  a._ref_decls = [
    "s.ifc = [ Ifc() for _ in range(2) ]"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk[0:1] )",
    "s.connect( s.reset, s.mangled__reset[0:1] )",
    "s.connect( s.ifc[0].msg, s.mangled__ifc__024___05F0__024msg[0:32] )",
    "s.connect( s.ifc[0].rdy, s.mangled__ifc__024___05F0__024rdy[0:1] )",
    "s.connect( s.ifc[0].val, s.mangled__ifc__024___05F0__024val[0:1] )",
    "s.connect( s.ifc[1].msg, s.mangled__ifc__024___05F1__024msg[0:32] )",
    "s.connect( s.ifc[1].rdy, s.mangled__ifc__024___05F1__024rdy[0:1] )",
    "s.connect( s.ifc[1].val, s.mangled__ifc__024___05F1__024val[0:1] )"
  ]
  a._ref_conns_yosys = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.reset, s.mangled__reset )",
    "s.connect( s.ifc[0].msg, s.mangled__ifc__024___05F0__024msg )",
    "s.connect( s.ifc[0].rdy, s.mangled__ifc__024___05F0__024rdy )",
    "s.connect( s.ifc[0].val, s.mangled__ifc__024___05F0__024val )",
    "s.connect( s.ifc[1].msg, s.mangled__ifc__024___05F1__024msg )",
    "s.connect( s.ifc[1].rdy, s.mangled__ifc__024___05F1__024rdy )",
    "s.connect( s.ifc[1].val, s.mangled__ifc__024___05F1__024val )"
  ]
  do_test( a )

def test_nested_interface( do_test ):
  class InnerIfc( Interface ):
    def construct( s ):
      s.msg = InPort( Bits32 )
      s.val = InPort( Bits1 )
      s.rdy = OutPort( Bits1 )
  class Ifc( Interface ):
    def construct( s ):
      s.valrdy_ifc = InnerIfc()
      s.ctrl_bar = InPort( Bits32 )
      s.ctrl_foo = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.ifc = [ Ifc() for _ in range(2) ]
  a = A()
  # Inner interface will not be added to `symbols` because Ifc refers
  # to it!
  a._ref_symbols = { 'Ifc' : Ifc }
  a._ref_decls = [
    "s.ifc = [ Ifc() for _ in range(2) ]"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk[0:1] )",
    "s.connect( s.reset, s.mangled__reset[0:1] )",
    "s.connect( s.ifc[0].ctrl_bar, s.mangled__ifc__024___05F0__024ctrl_bar[0:32] )",
    "s.connect( s.ifc[0].ctrl_foo, s.mangled__ifc__024___05F0__024ctrl_foo[0:32] )",
    "s.connect( s.ifc[0].valrdy_ifc.msg, s.mangled__ifc__024___05F0__024valrdy_ifc__024msg[0:32] )",
    "s.connect( s.ifc[0].valrdy_ifc.rdy, s.mangled__ifc__024___05F0__024valrdy_ifc__024rdy[0:1] )",
    "s.connect( s.ifc[0].valrdy_ifc.val, s.mangled__ifc__024___05F0__024valrdy_ifc__024val[0:1] )",
    "s.connect( s.ifc[1].ctrl_bar, s.mangled__ifc__024___05F1__024ctrl_bar[0:32] )",
    "s.connect( s.ifc[1].ctrl_foo, s.mangled__ifc__024___05F1__024ctrl_foo[0:32] )",
    "s.connect( s.ifc[1].valrdy_ifc.msg, s.mangled__ifc__024___05F1__024valrdy_ifc__024msg[0:32] )",
    "s.connect( s.ifc[1].valrdy_ifc.rdy, s.mangled__ifc__024___05F1__024valrdy_ifc__024rdy[0:1] )",
    "s.connect( s.ifc[1].valrdy_ifc.val, s.mangled__ifc__024___05F1__024valrdy_ifc__024val[0:1] )",
  ]
  a._ref_conns_yosys = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.reset, s.mangled__reset )",
    "s.connect( s.ifc[0].ctrl_bar, s.mangled__ifc__024___05F0__024ctrl_bar )",
    "s.connect( s.ifc[0].ctrl_foo, s.mangled__ifc__024___05F0__024ctrl_foo )",
    "s.connect( s.ifc[0].valrdy_ifc.msg, s.mangled__ifc__024___05F0__024valrdy_ifc__024msg )",
    "s.connect( s.ifc[0].valrdy_ifc.rdy, s.mangled__ifc__024___05F0__024valrdy_ifc__024rdy )",
    "s.connect( s.ifc[0].valrdy_ifc.val, s.mangled__ifc__024___05F0__024valrdy_ifc__024val )",
    "s.connect( s.ifc[1].ctrl_bar, s.mangled__ifc__024___05F1__024ctrl_bar )",
    "s.connect( s.ifc[1].ctrl_foo, s.mangled__ifc__024___05F1__024ctrl_foo )",
    "s.connect( s.ifc[1].valrdy_ifc.msg, s.mangled__ifc__024___05F1__024valrdy_ifc__024msg )",
    "s.connect( s.ifc[1].valrdy_ifc.rdy, s.mangled__ifc__024___05F1__024valrdy_ifc__024rdy )",
    "s.connect( s.ifc[1].valrdy_ifc.val, s.mangled__ifc__024___05F1__024valrdy_ifc__024val )",
  ]
  do_test( a )

def test_nested_interface_port_array( do_test ):
  class InnerIfc( Interface ):
    def construct( s ):
      s.msg = [ InPort( Bits32 ) for _ in range(2) ]
      s.val = InPort( Bits1 )
      s.rdy = OutPort( Bits1 )
  class Ifc( Interface ):
    def construct( s ):
      s.valrdy_ifc = InnerIfc()
      s.ctrl_bar = InPort( Bits32 )
      s.ctrl_foo = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.ifc = [ Ifc() for _ in range(2) ]
  a = A()
  # Inner interface will not be added to `symbols` because Ifc refers
  # to it!
  a._ref_symbols = { 'Ifc' : Ifc }
  a._ref_decls = [
    "s.ifc = [ Ifc() for _ in range(2) ]"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk[0:1] )",
    "s.connect( s.reset, s.mangled__reset[0:1] )",
    "s.connect( s.ifc[0].ctrl_bar, s.mangled__ifc__024___05F0__024ctrl_bar[0:32] )",
    "s.connect( s.ifc[0].ctrl_foo, s.mangled__ifc__024___05F0__024ctrl_foo[0:32] )",
    "s.connect( s.ifc[0].valrdy_ifc.msg[0], s.mangled__ifc__024___05F0__024valrdy_ifc__024msg[0][0:32] )",
    "s.connect( s.ifc[0].valrdy_ifc.msg[1], s.mangled__ifc__024___05F0__024valrdy_ifc__024msg[1][0:32] )",
    "s.connect( s.ifc[0].valrdy_ifc.rdy, s.mangled__ifc__024___05F0__024valrdy_ifc__024rdy[0:1] )",
    "s.connect( s.ifc[0].valrdy_ifc.val, s.mangled__ifc__024___05F0__024valrdy_ifc__024val[0:1] )",
    "s.connect( s.ifc[1].ctrl_bar, s.mangled__ifc__024___05F1__024ctrl_bar[0:32] )",
    "s.connect( s.ifc[1].ctrl_foo, s.mangled__ifc__024___05F1__024ctrl_foo[0:32] )",
    "s.connect( s.ifc[1].valrdy_ifc.msg[0], s.mangled__ifc__024___05F1__024valrdy_ifc__024msg[0][0:32] )",
    "s.connect( s.ifc[1].valrdy_ifc.msg[1], s.mangled__ifc__024___05F1__024valrdy_ifc__024msg[1][0:32] )",
    "s.connect( s.ifc[1].valrdy_ifc.rdy, s.mangled__ifc__024___05F1__024valrdy_ifc__024rdy[0:1] )",
    "s.connect( s.ifc[1].valrdy_ifc.val, s.mangled__ifc__024___05F1__024valrdy_ifc__024val[0:1] )",
  ]
  a._ref_conns_yosys = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.reset, s.mangled__reset )",
    "s.connect( s.ifc[0].ctrl_bar, s.mangled__ifc__024___05F0__024ctrl_bar )",
    "s.connect( s.ifc[0].ctrl_foo, s.mangled__ifc__024___05F0__024ctrl_foo )",
    "s.connect( s.ifc[0].valrdy_ifc.msg[0], s.mangled__ifc__024___05F0__024valrdy_ifc__024msg__024___05F0 )",
    "s.connect( s.ifc[0].valrdy_ifc.msg[1], s.mangled__ifc__024___05F0__024valrdy_ifc__024msg__024___05F1 )",
    "s.connect( s.ifc[0].valrdy_ifc.rdy, s.mangled__ifc__024___05F0__024valrdy_ifc__024rdy )",
    "s.connect( s.ifc[0].valrdy_ifc.val, s.mangled__ifc__024___05F0__024valrdy_ifc__024val )",
    "s.connect( s.ifc[1].ctrl_bar, s.mangled__ifc__024___05F1__024ctrl_bar )",
    "s.connect( s.ifc[1].ctrl_foo, s.mangled__ifc__024___05F1__024ctrl_foo )",
    "s.connect( s.ifc[1].valrdy_ifc.msg[0], s.mangled__ifc__024___05F1__024valrdy_ifc__024msg__024___05F0 )",
    "s.connect( s.ifc[1].valrdy_ifc.msg[1], s.mangled__ifc__024___05F1__024valrdy_ifc__024msg__024___05F1 )",
    "s.connect( s.ifc[1].valrdy_ifc.rdy, s.mangled__ifc__024___05F1__024valrdy_ifc__024rdy )",
    "s.connect( s.ifc[1].valrdy_ifc.val, s.mangled__ifc__024___05F1__024valrdy_ifc__024val )",
  ]
  do_test( a )
