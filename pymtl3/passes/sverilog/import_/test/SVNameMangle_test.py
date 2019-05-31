#=========================================================================
# SVNameMangle_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 30, 2019
"""Test the SystemVerilog name mangling."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits1, Bits32
from pymtl3.dsl import Component, InPort, Interface, OutPort
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.import_.helpers import gen_all_ports


def local_do_test( m ):
  m.elaborate()
  rtype = rt.get_component_ifc_rtlir( m )
  result = gen_all_ports( m, rtype )
  assert result == m._ref_ports

def test_port_single( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
  a = A()
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in_', rt.Port('input', rdt.Vector(32)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
  ]
  do_test( a )

def test_port_array( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange( 3 ) ]
  a = A()
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in__$0', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$1', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$2', rt.Port('input', rdt.Vector(32)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
  ]
  do_test( a )

def test_port_2d_array( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ [ InPort( Bits32 ) for _ in xrange(2) ] for _ in xrange(3) ]
  a = A()
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in__$0_$0', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$0_$1', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$1_$0', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$1_$1', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$2_$0', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$2_$1', rt.Port('input', rdt.Vector(32)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
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
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in__$bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$foo', rt.Port('input', rdt.Vector(32)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
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
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in__$0_$bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$0_$foo', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$1_$bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$1_$foo', rt.Port('input', rdt.Vector(32)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
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
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in__$0_$bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$0_$foo_$0_$0', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$0_$foo_$0_$1', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$0_$foo_$1_$0', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$0_$foo_$1_$1', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$0_$foo_$2_$0', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$0_$foo_$2_$1', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$1_$bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$1_$foo_$0_$0', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$1_$foo_$0_$1', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$1_$foo_$1_$0', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$1_$foo_$1_$1', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$1_$foo_$2_$0', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$1_$foo_$2_$1', rt.Port('input', rdt.Vector(32)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
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
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in__$0_$bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$0_$inner_$foo', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$1_$bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'in__$1_$inner_$foo', rt.Port('input', rdt.Vector(32)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
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
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) ),
    ( 'ifc_$msg', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc_$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc_$val', rt.Port('input', rdt.Vector(1)) )
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
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) ),
    ( 'ifc_$0_$msg', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc_$0_$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc_$0_$val', rt.Port('input', rdt.Vector(1)) ),
    ( 'ifc_$1_$msg', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc_$1_$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc_$1_$val', rt.Port('input', rdt.Vector(1)) )
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
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) ),
    ( 'ifc_$0_$ctrl_bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc_$0_$ctrl_foo', rt.Port('output', rdt.Vector(32)) ),
    ( 'ifc_$0_$valrdy_ifc_$msg', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc_$0_$valrdy_ifc_$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc_$0_$valrdy_ifc_$val', rt.Port('input', rdt.Vector(1)) ),
    ( 'ifc_$1_$ctrl_bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc_$1_$ctrl_foo', rt.Port('output', rdt.Vector(32)) ),
    ( 'ifc_$1_$valrdy_ifc_$msg', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc_$1_$valrdy_ifc_$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc_$1_$valrdy_ifc_$val', rt.Port('input', rdt.Vector(1)) )
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
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) ),
    ( 'ifc_$0_$ctrl_bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc_$0_$ctrl_foo', rt.Port('output', rdt.Vector(32)) ),
    ( 'ifc_$0_$valrdy_ifc_$msg_$0', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc_$0_$valrdy_ifc_$msg_$1', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc_$0_$valrdy_ifc_$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc_$0_$valrdy_ifc_$val', rt.Port('input', rdt.Vector(1)) ),
    ( 'ifc_$1_$ctrl_bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc_$1_$ctrl_foo', rt.Port('output', rdt.Vector(32)) ),
    ( 'ifc_$1_$valrdy_ifc_$msg_$0', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc_$1_$valrdy_ifc_$msg_$1', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc_$1_$valrdy_ifc_$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc_$1_$valrdy_ifc_$val', rt.Port('input', rdt.Vector(1)) )
  ]
  do_test( a )
