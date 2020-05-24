#=========================================================================
# VImportSignalGen.py
#=========================================================================
# Author : Peitian Pan
# Date   : June 1, 2019
"""Test the SystemVerilog signal generation of imported component."""

from pymtl3.datatypes import Bits1, Bits32, bitstruct, mk_bits
from pymtl3.dsl import Component, InPort, Interface, OutPort
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir.util.test_utility import do_test

from ..VerilogVerilatorImportPass import VerilogVerilatorImportPass


def local_do_test( m ):
  m.elaborate()
  rtype = rt.RTLIRGetter(cache=False).get_component_ifc_rtlir( m )
  ipass = VerilogVerilatorImportPass()
  symbols, decls = ipass.gen_signal_decl_py( rtype )
  assert symbols == m._ref_symbols
  assert decls == m._ref_decls

def test_port_single( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( mk_bits( 322 ) )
  a = A()
  a._ref_symbols = { 'Bits322' : mk_bits(322) }
  a._ref_decls = [
    "s.in_ = InPort( Bits322 )",
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
  a._ref_symbols = { 'struct__bar_32__foo_32' : struct }
  a._ref_decls = [
    "s.in_ = InPort( struct__bar_32__foo_32 )",
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
  a._ref_symbols = { 'struct__bar_32__foo_32' : struct }
  a._ref_decls = [
    "s.in_ = [ InPort( struct__bar_32__foo_32 ) for _ in range(2) ]",
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
  a._ref_symbols = { 'struct__bar_32__foo_32x3x2' : struct }
  a._ref_decls = [
    "s.in_ = [ InPort( struct__bar_32__foo_32x3x2 ) for _ in range(2) ]",
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
  a._ref_symbols = { 'struct__bar_32__inner_inner_struct__foo_32' : struct }
  a._ref_decls = [
    "s.in_ = [ InPort( struct__bar_32__inner_inner_struct__foo_32 ) for _ in range(2) ]",
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
  do_test( a )
