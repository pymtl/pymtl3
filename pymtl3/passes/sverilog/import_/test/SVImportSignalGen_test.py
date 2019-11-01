#=========================================================================
# SVImportSignalGen.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 1, 2019
"""Test the SystemVerilog signal generation of imported component."""

from pymtl3.datatypes import Bits1, Bits32, bitstruct, mk_bits
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
    "connect( s.clk, s.mangled__clk[0:1] )",
    "connect( s.in_, s.mangled__in_[0:322] )",
    "connect( s.reset, s.mangled__reset[0:1] )"
  ]
  a._ref_conns_yosys = [
    "connect( s.clk, s.mangled__clk )",
    "connect( s.in_, s.mangled__in_ )",
    "connect( s.reset, s.mangled__reset )"
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
    "connect( s.clk, s.mangled__clk[0:1] )",
    "connect( s.in_[0], s.mangled__in_[0][0:32] )",
    "connect( s.in_[1], s.mangled__in_[1][0:32] )",
    "connect( s.in_[2], s.mangled__in_[2][0:32] )",
    "connect( s.reset, s.mangled__reset[0:1] )"
  ]
  a._ref_conns_yosys = [
    "connect( s.clk, s.mangled__clk )",
    "connect( s.in_[0], s.mangled__in___05F_0 )",
    "connect( s.in_[1], s.mangled__in___05F_1 )",
    "connect( s.in_[2], s.mangled__in___05F_2 )",
    "connect( s.reset, s.mangled__reset )"
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
    "connect( s.clk, s.mangled__clk[0:1] )",
    "connect( s.in_[0][0], s.mangled__in_[0][0][0:32] )",
    "connect( s.in_[0][1], s.mangled__in_[0][1][0:32] )",
    "connect( s.in_[1][0], s.mangled__in_[1][0][0:32] )",
    "connect( s.in_[1][1], s.mangled__in_[1][1][0:32] )",
    "connect( s.in_[2][0], s.mangled__in_[2][0][0:32] )",
    "connect( s.in_[2][1], s.mangled__in_[2][1][0:32] )",
    "connect( s.reset, s.mangled__reset[0:1] )"
  ]
  a._ref_conns_yosys = [
    "connect( s.clk, s.mangled__clk )",
    "connect( s.in_[0][0], s.mangled__in___05F_0___05F0 )",
    "connect( s.in_[0][1], s.mangled__in___05F_0___05F1 )",
    "connect( s.in_[1][0], s.mangled__in___05F_1___05F0 )",
    "connect( s.in_[1][1], s.mangled__in___05F_1___05F1 )",
    "connect( s.in_[2][0], s.mangled__in___05F_2___05F0 )",
    "connect( s.in_[2][1], s.mangled__in___05F_2___05F1 )",
    "connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_struct_port_single( do_test ):
  @bitstruct
  class struct:
    bar: Bits32
    foo: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( struct )
  a = A()
  a._ref_symbols = { 'struct' : struct }
  a._ref_decls = [
    "s.in_ = InPort( struct )",
  ]
  a._ref_conns = [
    "connect( s.clk, s.mangled__clk[0:1] )",
    "@s.update",
    "def in_():",
    "  s.mangled__in_[0:32] = s.in_.foo",
    "  s.mangled__in_[32:64] = s.in_.bar",
    "connect( s.reset, s.mangled__reset[0:1] )"
  ]
  a._ref_conns_yosys = [
    "connect( s.clk, s.mangled__clk )",
    "@s.update",
    "def in_():",
    "  s.mangled__in___05F_foo = s.in_.foo",
    "  s.mangled__in___05F_bar = s.in_.bar",
    "connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_struct_port_array( do_test ):
  @bitstruct
  class struct:
    bar: Bits32
    foo: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( struct ) for _ in range(2) ]
  a = A()
  a._ref_symbols = { 'struct' : struct }
  a._ref_decls = [
    "s.in_ = [ InPort( struct ) for _ in range(2) ]",
  ]
  a._ref_conns = [
    "connect( s.clk, s.mangled__clk[0:1] )",
    "@s.update",
    "def in__LBR_0_RBR_():",
    "  s.mangled__in_[0][0:32] = s.in_[0].foo",
    "  s.mangled__in_[0][32:64] = s.in_[0].bar",
    "@s.update",
    "def in__LBR_1_RBR_():",
    "  s.mangled__in_[1][0:32] = s.in_[1].foo",
    "  s.mangled__in_[1][32:64] = s.in_[1].bar",
    "connect( s.reset, s.mangled__reset[0:1] )"
  ]
  a._ref_conns_yosys = [
    "connect( s.clk, s.mangled__clk )",
    "@s.update",
    "def in__LBR_0_RBR_():",
    "  s.mangled__in___05F_0___05Ffoo = s.in_[0].foo",
    "  s.mangled__in___05F_0___05Fbar = s.in_[0].bar",
    "@s.update",
    "def in__LBR_1_RBR_():",
    "  s.mangled__in___05F_1___05Ffoo = s.in_[1].foo",
    "  s.mangled__in___05F_1___05Fbar = s.in_[1].bar",
    "connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_packed_array_port_array( do_test ):
  @bitstruct
  class struct:
    bar: Bits32
    foo: [ [ Bits32 for _ in range(2) ] for _ in range(3) ]
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( struct ) for _ in range(2) ]
  a = A()
  a._ref_symbols = { 'struct' : struct }
  a._ref_decls = [
    "s.in_ = [ InPort( struct ) for _ in range(2) ]",
  ]
  a._ref_conns = [
    "connect( s.clk, s.mangled__clk[0:1] )",
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
    "connect( s.reset, s.mangled__reset[0:1] )"
  ]
  a._ref_conns_yosys = [
    "connect( s.clk, s.mangled__clk )",
    "@s.update",
    "def in__LBR_0_RBR_():",
    "  s.mangled__in___05F_0___05Ffoo___05F0___05F0 = s.in_[0].foo[0][0]",
    "  s.mangled__in___05F_0___05Ffoo___05F0___05F1 = s.in_[0].foo[0][1]",
    "  s.mangled__in___05F_0___05Ffoo___05F1___05F0 = s.in_[0].foo[1][0]",
    "  s.mangled__in___05F_0___05Ffoo___05F1___05F1 = s.in_[0].foo[1][1]",
    "  s.mangled__in___05F_0___05Ffoo___05F2___05F0 = s.in_[0].foo[2][0]",
    "  s.mangled__in___05F_0___05Ffoo___05F2___05F1 = s.in_[0].foo[2][1]",
    "  s.mangled__in___05F_0___05Fbar = s.in_[0].bar",
    "@s.update",
    "def in__LBR_1_RBR_():",
    "  s.mangled__in___05F_1___05Ffoo___05F0___05F0 = s.in_[1].foo[0][0]",
    "  s.mangled__in___05F_1___05Ffoo___05F0___05F1 = s.in_[1].foo[0][1]",
    "  s.mangled__in___05F_1___05Ffoo___05F1___05F0 = s.in_[1].foo[1][0]",
    "  s.mangled__in___05F_1___05Ffoo___05F1___05F1 = s.in_[1].foo[1][1]",
    "  s.mangled__in___05F_1___05Ffoo___05F2___05F0 = s.in_[1].foo[2][0]",
    "  s.mangled__in___05F_1___05Ffoo___05F2___05F1 = s.in_[1].foo[2][1]",
    "  s.mangled__in___05F_1___05Fbar = s.in_[1].bar",
    "connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_nested_struct( do_test ):
  @bitstruct
  class inner_struct:
    foo: Bits32
  @bitstruct
  class struct:
    bar: Bits32
    inner: inner_struct
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
    "connect( s.clk, s.mangled__clk[0:1] )",
    "@s.update",
    "def in__LBR_0_RBR_():",
    "  s.mangled__in_[0][0:32] = s.in_[0].inner.foo",
    "  s.mangled__in_[0][32:64] = s.in_[0].bar",
    "@s.update",
    "def in__LBR_1_RBR_():",
    "  s.mangled__in_[1][0:32] = s.in_[1].inner.foo",
    "  s.mangled__in_[1][32:64] = s.in_[1].bar",
    "connect( s.reset, s.mangled__reset[0:1] )"
  ]
  a._ref_conns_yosys = [
    "connect( s.clk, s.mangled__clk )",
    "@s.update",
    "def in__LBR_0_RBR_():",
    "  s.mangled__in___05F_0___05Finner___05Ffoo = s.in_[0].inner.foo",
    "  s.mangled__in___05F_0___05Fbar = s.in_[0].bar",
    "@s.update",
    "def in__LBR_1_RBR_():",
    "  s.mangled__in___05F_1___05Finner___05Ffoo = s.in_[1].inner.foo",
    "  s.mangled__in___05F_1___05Fbar = s.in_[1].bar",
    "connect( s.reset, s.mangled__reset )"
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
    "connect( s.clk, s.mangled__clk[0:1] )",
    "connect( s.reset, s.mangled__reset[0:1] )",
    "connect( s.ifc.msg, s.mangled__ifc___05Fmsg[0:32] )",
    "connect( s.ifc.rdy, s.mangled__ifc___05Frdy[0:1] )",
    "connect( s.ifc.val, s.mangled__ifc___05Fval[0:1] )",
  ]
  a._ref_conns_yosys = [
    "connect( s.clk, s.mangled__clk )",
    "connect( s.reset, s.mangled__reset )",
    "connect( s.ifc.msg, s.mangled__ifc___05Fmsg )",
    "connect( s.ifc.rdy, s.mangled__ifc___05Frdy )",
    "connect( s.ifc.val, s.mangled__ifc___05Fval )",
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
    "connect( s.clk, s.mangled__clk[0:1] )",
    "connect( s.reset, s.mangled__reset[0:1] )",
    "connect( s.ifc.msg, s.mangled__ifc___05Fmsg[0:32] )",
    "connect( s.ifc.rdy, s.mangled__ifc___05Frdy[0:1] )",
    "connect( s.ifc.val, s.mangled__ifc___05Fval[0:1] )",
  ]
  a._ref_conns_yosys = [
    "connect( s.clk, s.mangled__clk )",
    "connect( s.reset, s.mangled__reset )",
    "connect( s.ifc.msg, s.mangled__ifc___05Fmsg )",
    "connect( s.ifc.rdy, s.mangled__ifc___05Frdy )",
    "connect( s.ifc.val, s.mangled__ifc___05Fval )",
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
    "connect( s.clk, s.mangled__clk[0:1] )",
    "connect( s.reset, s.mangled__reset[0:1] )",
    "connect( s.ifc.msg, s.mangled__ifc___05Fmsg[0:322] )",
    "connect( s.ifc.rdy, s.mangled__ifc___05Frdy[0:322] )",
    "connect( s.ifc.val, s.mangled__ifc___05Fval[0:1] )",
  ]
  a._ref_conns_yosys = [
    "connect( s.clk, s.mangled__clk )",
    "connect( s.reset, s.mangled__reset )",
    "connect( s.ifc.msg, s.mangled__ifc___05Fmsg )",
    "connect( s.ifc.rdy, s.mangled__ifc___05Frdy )",
    "connect( s.ifc.val, s.mangled__ifc___05Fval )",
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
    "connect( s.clk, s.mangled__clk[0:1] )",
    "connect( s.reset, s.mangled__reset[0:1] )",
    "connect( s.ifc[0].msg, s.mangled__ifc___05F0___05Fmsg[0:32] )",
    "connect( s.ifc[0].rdy, s.mangled__ifc___05F0___05Frdy[0:1] )",
    "connect( s.ifc[0].val, s.mangled__ifc___05F0___05Fval[0:1] )",
    "connect( s.ifc[1].msg, s.mangled__ifc___05F1___05Fmsg[0:32] )",
    "connect( s.ifc[1].rdy, s.mangled__ifc___05F1___05Frdy[0:1] )",
    "connect( s.ifc[1].val, s.mangled__ifc___05F1___05Fval[0:1] )"
  ]
  a._ref_conns_yosys = [
    "connect( s.clk, s.mangled__clk )",
    "connect( s.reset, s.mangled__reset )",
    "connect( s.ifc[0].msg, s.mangled__ifc___05F0___05Fmsg )",
    "connect( s.ifc[0].rdy, s.mangled__ifc___05F0___05Frdy )",
    "connect( s.ifc[0].val, s.mangled__ifc___05F0___05Fval )",
    "connect( s.ifc[1].msg, s.mangled__ifc___05F1___05Fmsg )",
    "connect( s.ifc[1].rdy, s.mangled__ifc___05F1___05Frdy )",
    "connect( s.ifc[1].val, s.mangled__ifc___05F1___05Fval )"
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
    "connect( s.clk, s.mangled__clk[0:1] )",
    "connect( s.reset, s.mangled__reset[0:1] )",
    "connect( s.ifc[0].ctrl_bar, s.mangled__ifc___05F0___05Fctrl_bar[0:32] )",
    "connect( s.ifc[0].ctrl_foo, s.mangled__ifc___05F0___05Fctrl_foo[0:32] )",
    "connect( s.ifc[0].valrdy_ifc.msg, s.mangled__ifc___05F0___05Fvalrdy_ifc___05Fmsg[0:32] )",
    "connect( s.ifc[0].valrdy_ifc.rdy, s.mangled__ifc___05F0___05Fvalrdy_ifc___05Frdy[0:1] )",
    "connect( s.ifc[0].valrdy_ifc.val, s.mangled__ifc___05F0___05Fvalrdy_ifc___05Fval[0:1] )",
    "connect( s.ifc[1].ctrl_bar, s.mangled__ifc___05F1___05Fctrl_bar[0:32] )",
    "connect( s.ifc[1].ctrl_foo, s.mangled__ifc___05F1___05Fctrl_foo[0:32] )",
    "connect( s.ifc[1].valrdy_ifc.msg, s.mangled__ifc___05F1___05Fvalrdy_ifc___05Fmsg[0:32] )",
    "connect( s.ifc[1].valrdy_ifc.rdy, s.mangled__ifc___05F1___05Fvalrdy_ifc___05Frdy[0:1] )",
    "connect( s.ifc[1].valrdy_ifc.val, s.mangled__ifc___05F1___05Fvalrdy_ifc___05Fval[0:1] )",
  ]
  a._ref_conns_yosys = [
    "connect( s.clk, s.mangled__clk )",
    "connect( s.reset, s.mangled__reset )",
    "connect( s.ifc[0].ctrl_bar, s.mangled__ifc___05F0___05Fctrl_bar )",
    "connect( s.ifc[0].ctrl_foo, s.mangled__ifc___05F0___05Fctrl_foo )",
    "connect( s.ifc[0].valrdy_ifc.msg, s.mangled__ifc___05F0___05Fvalrdy_ifc___05Fmsg )",
    "connect( s.ifc[0].valrdy_ifc.rdy, s.mangled__ifc___05F0___05Fvalrdy_ifc___05Frdy )",
    "connect( s.ifc[0].valrdy_ifc.val, s.mangled__ifc___05F0___05Fvalrdy_ifc___05Fval )",
    "connect( s.ifc[1].ctrl_bar, s.mangled__ifc___05F1___05Fctrl_bar )",
    "connect( s.ifc[1].ctrl_foo, s.mangled__ifc___05F1___05Fctrl_foo )",
    "connect( s.ifc[1].valrdy_ifc.msg, s.mangled__ifc___05F1___05Fvalrdy_ifc___05Fmsg )",
    "connect( s.ifc[1].valrdy_ifc.rdy, s.mangled__ifc___05F1___05Fvalrdy_ifc___05Frdy )",
    "connect( s.ifc[1].valrdy_ifc.val, s.mangled__ifc___05F1___05Fvalrdy_ifc___05Fval )",
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
    "connect( s.clk, s.mangled__clk[0:1] )",
    "connect( s.reset, s.mangled__reset[0:1] )",
    "connect( s.ifc[0].ctrl_bar, s.mangled__ifc___05F0___05Fctrl_bar[0:32] )",
    "connect( s.ifc[0].ctrl_foo, s.mangled__ifc___05F0___05Fctrl_foo[0:32] )",
    "connect( s.ifc[0].valrdy_ifc.msg[0], s.mangled__ifc___05F0___05Fvalrdy_ifc___05Fmsg[0][0:32] )",
    "connect( s.ifc[0].valrdy_ifc.msg[1], s.mangled__ifc___05F0___05Fvalrdy_ifc___05Fmsg[1][0:32] )",
    "connect( s.ifc[0].valrdy_ifc.rdy, s.mangled__ifc___05F0___05Fvalrdy_ifc___05Frdy[0:1] )",
    "connect( s.ifc[0].valrdy_ifc.val, s.mangled__ifc___05F0___05Fvalrdy_ifc___05Fval[0:1] )",
    "connect( s.ifc[1].ctrl_bar, s.mangled__ifc___05F1___05Fctrl_bar[0:32] )",
    "connect( s.ifc[1].ctrl_foo, s.mangled__ifc___05F1___05Fctrl_foo[0:32] )",
    "connect( s.ifc[1].valrdy_ifc.msg[0], s.mangled__ifc___05F1___05Fvalrdy_ifc___05Fmsg[0][0:32] )",
    "connect( s.ifc[1].valrdy_ifc.msg[1], s.mangled__ifc___05F1___05Fvalrdy_ifc___05Fmsg[1][0:32] )",
    "connect( s.ifc[1].valrdy_ifc.rdy, s.mangled__ifc___05F1___05Fvalrdy_ifc___05Frdy[0:1] )",
    "connect( s.ifc[1].valrdy_ifc.val, s.mangled__ifc___05F1___05Fvalrdy_ifc___05Fval[0:1] )",
  ]
  a._ref_conns_yosys = [
    "connect( s.clk, s.mangled__clk )",
    "connect( s.reset, s.mangled__reset )",
    "connect( s.ifc[0].ctrl_bar, s.mangled__ifc___05F0___05Fctrl_bar )",
    "connect( s.ifc[0].ctrl_foo, s.mangled__ifc___05F0___05Fctrl_foo )",
    "connect( s.ifc[0].valrdy_ifc.msg[0], s.mangled__ifc___05F0___05Fvalrdy_ifc___05Fmsg___05F0 )",
    "connect( s.ifc[0].valrdy_ifc.msg[1], s.mangled__ifc___05F0___05Fvalrdy_ifc___05Fmsg___05F1 )",
    "connect( s.ifc[0].valrdy_ifc.rdy, s.mangled__ifc___05F0___05Fvalrdy_ifc___05Frdy )",
    "connect( s.ifc[0].valrdy_ifc.val, s.mangled__ifc___05F0___05Fvalrdy_ifc___05Fval )",
    "connect( s.ifc[1].ctrl_bar, s.mangled__ifc___05F1___05Fctrl_bar )",
    "connect( s.ifc[1].ctrl_foo, s.mangled__ifc___05F1___05Fctrl_foo )",
    "connect( s.ifc[1].valrdy_ifc.msg[0], s.mangled__ifc___05F1___05Fvalrdy_ifc___05Fmsg___05F0 )",
    "connect( s.ifc[1].valrdy_ifc.msg[1], s.mangled__ifc___05F1___05Fvalrdy_ifc___05Fmsg___05F1 )",
    "connect( s.ifc[1].valrdy_ifc.rdy, s.mangled__ifc___05F1___05Fvalrdy_ifc___05Frdy )",
    "connect( s.ifc[1].valrdy_ifc.val, s.mangled__ifc___05F1___05Fvalrdy_ifc___05Fval )",
  ]
  do_test( a )
