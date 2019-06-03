#=========================================================================
# SVImportSignalGen.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 1, 2019
"""Test the SystemVerilog signal generation of imported component."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits1, Bits32, mk_bits
from pymtl3.dsl import Component, InPort, Interface, OutPort
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.import_.helpers import gen_signal_decl_py


def local_do_test( m ):
  m.elaborate()
  rtype = rt.get_component_ifc_rtlir( m )
  symbols, decls, conns = gen_signal_decl_py( rtype )
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
    "s.clk = InPort( Bits1 )",
    "s.in_ = InPort( Bits322 )",
    "s.reset = InPort( Bits1 )"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.in_, s.mangled__in_ )",
    "s.connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_port_array( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange( 3 ) ]
  a = A()
  a._ref_symbols = {}
  a._ref_decls = [
    "s.clk = InPort( Bits1 )",
    "s.in_ = [ InPort( Bits32 ) for _ in xrange(3) ]",
    "s.reset = InPort( Bits1 )"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.in_[0], s.mangled__in__$0 )",
    "s.connect( s.in_[1], s.mangled__in__$1 )",
    "s.connect( s.in_[2], s.mangled__in__$2 )",
    "s.connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_port_2d_array( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ [ InPort( Bits32 ) for _ in xrange(2) ] for _ in xrange(3) ]
  a = A()
  a._ref_symbols = {}
  a._ref_decls = [
    "s.clk = InPort( Bits1 )",
    "s.in_ = [ [ InPort( Bits32 ) for _ in xrange(2) ] for _ in xrange(3) ]",
    "s.reset = InPort( Bits1 )"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.in_[0][0], s.mangled__in__$0_$0 )",
    "s.connect( s.in_[0][1], s.mangled__in__$0_$1 )",
    "s.connect( s.in_[1][0], s.mangled__in__$1_$0 )",
    "s.connect( s.in_[1][1], s.mangled__in__$1_$1 )",
    "s.connect( s.in_[2][0], s.mangled__in__$2_$0 )",
    "s.connect( s.in_[2][1], s.mangled__in__$2_$1 )",
    "s.connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_struct_port_single( do_test ):
  class struct( object ):
    def __init__( s, bar=1, foo=42 ):
      s.bar = Bits32(bar)
      s.foo = Bits32(foo)
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( struct )
  a = A()
  a._ref_symbols = { 'struct' : struct }
  a._ref_decls = [
    "s.clk = InPort( Bits1 )",
    "s.in_ = InPort( struct )",
    "s.reset = InPort( Bits1 )"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.in_.bar, s.mangled__in__$bar )",
    "s.connect( s.in_.foo, s.mangled__in__$foo )",
    "s.connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_struct_port_array( do_test ):
  class struct( object ):
    def __init__( s, bar=1, foo=42 ):
      s.bar = Bits32(bar)
      s.foo = Bits32(foo)
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( struct ) for _ in xrange(2) ]
  a = A()
  a._ref_symbols = { 'struct' : struct }
  a._ref_decls = [
    "s.clk = InPort( Bits1 )",
    "s.in_ = [ InPort( struct ) for _ in xrange(2) ]",
    "s.reset = InPort( Bits1 )"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.in_[0].bar, s.mangled__in__$0_$bar )",
    "s.connect( s.in_[0].foo, s.mangled__in__$0_$foo )",
    "s.connect( s.in_[1].bar, s.mangled__in__$1_$bar )",
    "s.connect( s.in_[1].foo, s.mangled__in__$1_$foo )",
    "s.connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_packed_array_port_array( do_test ):
  class struct( object ):
    def __init__( s, bar=1, foo=42 ):
      s.bar = Bits32(bar)
      s.foo = [ [ Bits32(foo) for _ in xrange(2) ] for _ in xrange(3) ]
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( struct ) for _ in xrange(2) ]
  a = A()
  a._ref_symbols = { 'struct' : struct }
  a._ref_decls = [
    "s.clk = InPort( Bits1 )",
    "s.in_ = [ InPort( struct ) for _ in xrange(2) ]",
    "s.reset = InPort( Bits1 )"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.in_[0].bar, s.mangled__in__$0_$bar )",
    "s.connect( s.in_[0].foo[0][0], s.mangled__in__$0_$foo_$0_$0 )",
    "s.connect( s.in_[0].foo[0][1], s.mangled__in__$0_$foo_$0_$1 )",
    "s.connect( s.in_[0].foo[1][0], s.mangled__in__$0_$foo_$1_$0 )",
    "s.connect( s.in_[0].foo[1][1], s.mangled__in__$0_$foo_$1_$1 )",
    "s.connect( s.in_[0].foo[2][0], s.mangled__in__$0_$foo_$2_$0 )",
    "s.connect( s.in_[0].foo[2][1], s.mangled__in__$0_$foo_$2_$1 )",
    "s.connect( s.in_[1].bar, s.mangled__in__$1_$bar )",
    "s.connect( s.in_[1].foo[0][0], s.mangled__in__$1_$foo_$0_$0 )",
    "s.connect( s.in_[1].foo[0][1], s.mangled__in__$1_$foo_$0_$1 )",
    "s.connect( s.in_[1].foo[1][0], s.mangled__in__$1_$foo_$1_$0 )",
    "s.connect( s.in_[1].foo[1][1], s.mangled__in__$1_$foo_$1_$1 )",
    "s.connect( s.in_[1].foo[2][0], s.mangled__in__$1_$foo_$2_$0 )",
    "s.connect( s.in_[1].foo[2][1], s.mangled__in__$1_$foo_$2_$1 )",
    "s.connect( s.reset, s.mangled__reset )"
  ]
  do_test( a )

def test_nested_struct( do_test ):
  class inner_struct( object ):
    def __init__( s, foo = 42 ):
      s.foo = Bits32(foo)
  class struct( object ):
    def __init__( s, bar=1 ):
      s.bar = Bits32(bar)
      s.inner = inner_struct()
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( struct ) for _ in xrange(2) ]
  a = A()
  # Inner struct will not be added to `symbols` because struct
  # refers to it!
  a._ref_symbols = { 'struct' : struct }
  a._ref_decls = [
    "s.clk = InPort( Bits1 )",
    "s.in_ = [ InPort( struct ) for _ in xrange(2) ]",
    "s.reset = InPort( Bits1 )"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.in_[0].bar, s.mangled__in__$0_$bar )",
    "s.connect( s.in_[0].inner.foo, s.mangled__in__$0_$inner_$foo )",
    "s.connect( s.in_[1].bar, s.mangled__in__$1_$bar )",
    "s.connect( s.in_[1].inner.foo, s.mangled__in__$1_$inner_$foo )",
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
    "s.clk = InPort( Bits1 )",
    "s.reset = InPort( Bits1 )",
    "s.ifc = Ifc()"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.reset, s.mangled__reset )",
    "s.connect( s.ifc.msg, s.mangled__ifc_$msg )",
    "s.connect( s.ifc.rdy, s.mangled__ifc_$rdy )",
    "s.connect( s.ifc.val, s.mangled__ifc_$val )",
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
    "s.clk = InPort( Bits1 )",
    "s.reset = InPort( Bits1 )",
    "s.ifc = Ifc( Bits32, 1, Bits1( 1 ) )"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.reset, s.mangled__reset )",
    "s.connect( s.ifc.msg, s.mangled__ifc_$msg )",
    "s.connect( s.ifc.rdy, s.mangled__ifc_$rdy )",
    "s.connect( s.ifc.val, s.mangled__ifc_$val )",
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
    "s.clk = InPort( Bits1 )",
    "s.reset = InPort( Bits1 )",
    "s.ifc = Ifc( Bits322, 1, Bits322( 1 ) )"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.reset, s.mangled__reset )",
    "s.connect( s.ifc.msg, s.mangled__ifc_$msg )",
    "s.connect( s.ifc.rdy, s.mangled__ifc_$rdy )",
    "s.connect( s.ifc.val, s.mangled__ifc_$val )",
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
      s.ifc = [ Ifc() for _ in xrange(2) ]
  a = A()
  a._ref_symbols = { 'Ifc' : Ifc }
  a._ref_decls = [
    "s.clk = InPort( Bits1 )",
    "s.reset = InPort( Bits1 )",
    "s.ifc = [ Ifc() for _ in xrange(2) ]"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.reset, s.mangled__reset )",
    "s.connect( s.ifc[0].msg, s.mangled__ifc_$0_$msg )",
    "s.connect( s.ifc[0].rdy, s.mangled__ifc_$0_$rdy )",
    "s.connect( s.ifc[0].val, s.mangled__ifc_$0_$val )",
    "s.connect( s.ifc[1].msg, s.mangled__ifc_$1_$msg )",
    "s.connect( s.ifc[1].rdy, s.mangled__ifc_$1_$rdy )",
    "s.connect( s.ifc[1].val, s.mangled__ifc_$1_$val )"
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
      s.ifc = [ Ifc() for _ in xrange(2) ]
  a = A()
  # Inner interface will not be added to `symbols` because Ifc refers
  # to it!
  a._ref_symbols = { 'Ifc' : Ifc }
  a._ref_decls = [
    "s.clk = InPort( Bits1 )",
    "s.reset = InPort( Bits1 )",
    "s.ifc = [ Ifc() for _ in xrange(2) ]"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.reset, s.mangled__reset )",
    "s.connect( s.ifc[0].ctrl_bar, s.mangled__ifc_$0_$ctrl_bar )",
    "s.connect( s.ifc[0].ctrl_foo, s.mangled__ifc_$0_$ctrl_foo )",
    "s.connect( s.ifc[0].valrdy_ifc.msg, s.mangled__ifc_$0_$valrdy_ifc_$msg )",
    "s.connect( s.ifc[0].valrdy_ifc.rdy, s.mangled__ifc_$0_$valrdy_ifc_$rdy )",
    "s.connect( s.ifc[0].valrdy_ifc.val, s.mangled__ifc_$0_$valrdy_ifc_$val )",
    "s.connect( s.ifc[1].ctrl_bar, s.mangled__ifc_$1_$ctrl_bar )",
    "s.connect( s.ifc[1].ctrl_foo, s.mangled__ifc_$1_$ctrl_foo )",
    "s.connect( s.ifc[1].valrdy_ifc.msg, s.mangled__ifc_$1_$valrdy_ifc_$msg )",
    "s.connect( s.ifc[1].valrdy_ifc.rdy, s.mangled__ifc_$1_$valrdy_ifc_$rdy )",
    "s.connect( s.ifc[1].valrdy_ifc.val, s.mangled__ifc_$1_$valrdy_ifc_$val )",
  ]
  do_test( a )

def test_nested_interface_port_array( do_test ):
  class InnerIfc( Interface ):
    def construct( s ):
      s.msg = [ InPort( Bits32 ) for _ in xrange(2) ]
      s.val = InPort( Bits1 )
      s.rdy = OutPort( Bits1 )
  class Ifc( Interface ):
    def construct( s ):
      s.valrdy_ifc = InnerIfc()
      s.ctrl_bar = InPort( Bits32 )
      s.ctrl_foo = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.ifc = [ Ifc() for _ in xrange(2) ]
  a = A()
  # Inner interface will not be added to `symbols` because Ifc refers
  # to it!
  a._ref_symbols = { 'Ifc' : Ifc }
  a._ref_decls = [
    "s.clk = InPort( Bits1 )",
    "s.reset = InPort( Bits1 )",
    "s.ifc = [ Ifc() for _ in xrange(2) ]"
  ]
  a._ref_conns = [
    "s.connect( s.clk, s.mangled__clk )",
    "s.connect( s.reset, s.mangled__reset )",
    "s.connect( s.ifc[0].ctrl_bar, s.mangled__ifc_$0_$ctrl_bar )",
    "s.connect( s.ifc[0].ctrl_foo, s.mangled__ifc_$0_$ctrl_foo )",
    "s.connect( s.ifc[0].valrdy_ifc.msg[0], s.mangled__ifc_$0_$valrdy_ifc_$msg_$0 )",
    "s.connect( s.ifc[0].valrdy_ifc.msg[1], s.mangled__ifc_$0_$valrdy_ifc_$msg_$1 )",
    "s.connect( s.ifc[0].valrdy_ifc.rdy, s.mangled__ifc_$0_$valrdy_ifc_$rdy )",
    "s.connect( s.ifc[0].valrdy_ifc.val, s.mangled__ifc_$0_$valrdy_ifc_$val )",
    "s.connect( s.ifc[1].ctrl_bar, s.mangled__ifc_$1_$ctrl_bar )",
    "s.connect( s.ifc[1].ctrl_foo, s.mangled__ifc_$1_$ctrl_foo )",
    "s.connect( s.ifc[1].valrdy_ifc.msg[0], s.mangled__ifc_$1_$valrdy_ifc_$msg_$0 )",
    "s.connect( s.ifc[1].valrdy_ifc.msg[1], s.mangled__ifc_$1_$valrdy_ifc_$msg_$1 )",
    "s.connect( s.ifc[1].valrdy_ifc.rdy, s.mangled__ifc_$1_$valrdy_ifc_$rdy )",
    "s.connect( s.ifc[1].valrdy_ifc.val, s.mangled__ifc_$1_$valrdy_ifc_$val )",
  ]
  do_test( a )
