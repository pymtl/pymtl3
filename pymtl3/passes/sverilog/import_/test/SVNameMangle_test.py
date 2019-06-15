#=========================================================================
# SVNameMangle_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 30, 2019
"""Test the SystemVerilog name mangling."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits1, Bits32, BitStruct
from pymtl3.dsl import Component, InPort, Interface, OutPort
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.import_.ImportPass import ImportPass


def local_do_test( m ):
  m.elaborate()
  rtype = rt.get_component_ifc_rtlir( m )
  ipass = ImportPass()
  result = ipass.gen_packed_ports( rtype )
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
  a._ref_ports_yosys = a._ref_ports
  do_test( a )

def test_port_array( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range( 3 ) ]
  a = A()
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in_', rt.Array([3], rt.Port('input', rdt.Vector(32))) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
  ]
  a._ref_ports_yosys = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in_$__0', rt.Port('input', rdt.Vector(32)) ),
    ( 'in_$__1', rt.Port('input', rdt.Vector(32)) ),
    ( 'in_$__2', rt.Port('input', rdt.Vector(32)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
  ]
  do_test( a )

def test_port_2d_array( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ [ InPort( Bits32 ) for _ in range(2) ] for _ in range(3) ]
  a = A()
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in_', rt.Array( [3, 2], rt.Port('input', rdt.Vector(32)) ) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
  ]
  a._ref_ports_yosys = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in_$__0$__0', rt.Port('input', rdt.Vector(32)) ),
    ( 'in_$__0$__1', rt.Port('input', rdt.Vector(32)) ),
    ( 'in_$__1$__0', rt.Port('input', rdt.Vector(32)) ),
    ( 'in_$__1$__1', rt.Port('input', rdt.Vector(32)) ),
    ( 'in_$__2$__0', rt.Port('input', rdt.Vector(32)) ),
    ( 'in_$__2$__1', rt.Port('input', rdt.Vector(32)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
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
  st = rdt.Struct('struct', {'bar':rdt.Vector(32), 'foo':rdt.Vector(32)},
                  ['bar', 'foo'])
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in_', rt.Port('input', st ) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
  ]
  a._ref_ports_yosys = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in_$bar', rt.Port('input', rdt.Vector(32) ) ),
    ( 'in_$foo', rt.Port('input', rdt.Vector(32) ) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
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
  st = rdt.Struct('struct', {'bar':rdt.Vector(32), 'foo':rdt.Vector(32)},
                  ['bar', 'foo'])
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in_', rt.Array([2], rt.Port('input', st)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
  ]
  a._ref_ports_yosys = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in_$__0$bar', rt.Port('input', rdt.Vector(32) ) ),
    ( 'in_$__0$foo', rt.Port('input', rdt.Vector(32) ) ),
    ( 'in_$__1$bar', rt.Port('input', rdt.Vector(32) ) ),
    ( 'in_$__1$foo', rt.Port('input', rdt.Vector(32) ) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
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
  foo = rdt.PackedArray([3,2], rdt.Vector(32))
  st = rdt.Struct('struct', {'bar':rdt.Vector(32), 'foo':foo},
                  ['bar', 'foo'])
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in_', rt.Array([2], rt.Port('input', st ))),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
  ]
  a._ref_ports_yosys = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in_$__0$bar', rt.Port('input', rdt.Vector(32) )),
    ( 'in_$__0$foo$__0$__0', rt.Port('input', rdt.Vector(32) )),
    ( 'in_$__0$foo$__0$__1', rt.Port('input', rdt.Vector(32) )),
    ( 'in_$__0$foo$__1$__0', rt.Port('input', rdt.Vector(32) )),
    ( 'in_$__0$foo$__1$__1', rt.Port('input', rdt.Vector(32) )),
    ( 'in_$__0$foo$__2$__0', rt.Port('input', rdt.Vector(32) )),
    ( 'in_$__0$foo$__2$__1', rt.Port('input', rdt.Vector(32) )),
    ( 'in_$__1$bar', rt.Port('input', rdt.Vector(32) )),
    ( 'in_$__1$foo$__0$__0', rt.Port('input', rdt.Vector(32) )),
    ( 'in_$__1$foo$__0$__1', rt.Port('input', rdt.Vector(32) )),
    ( 'in_$__1$foo$__1$__0', rt.Port('input', rdt.Vector(32) )),
    ( 'in_$__1$foo$__1$__1', rt.Port('input', rdt.Vector(32) )),
    ( 'in_$__1$foo$__2$__0', rt.Port('input', rdt.Vector(32) )),
    ( 'in_$__1$foo$__2$__1', rt.Port('input', rdt.Vector(32) )),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
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
  inner = rdt.Struct('inner_struct', {'foo':rdt.Vector(32)}, ['foo'])
  st = rdt.Struct('struct', {'bar':rdt.Vector(32), 'inner':inner}, ['bar', 'inner'])
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in_', rt.Array([2], rt.Port('input', st )) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) )
  ]
  a._ref_ports_yosys = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'in_$__0$bar', rt.Port('input', rdt.Vector(32) ) ),
    ( 'in_$__0$inner$foo', rt.Port('input', rdt.Vector(32) ) ),
    ( 'in_$__1$bar', rt.Port('input', rdt.Vector(32) ) ),
    ( 'in_$__1$inner$foo', rt.Port('input', rdt.Vector(32) ) ),
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
    ( 'ifc$msg', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc$val', rt.Port('input', rdt.Vector(1)) )
  ]
  a._ref_ports_yosys = a._ref_ports
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
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) ),
    ( 'ifc$__0$msg', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc$__0$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc$__0$val', rt.Port('input', rdt.Vector(1)) ),
    ( 'ifc$__1$msg', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc$__1$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc$__1$val', rt.Port('input', rdt.Vector(1)) )
  ]
  a._ref_ports_yosys = a._ref_ports
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
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) ),
    ( 'ifc$__0$ctrl_bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc$__0$ctrl_foo', rt.Port('output', rdt.Vector(32)) ),
    ( 'ifc$__0$valrdy_ifc$msg', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc$__0$valrdy_ifc$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc$__0$valrdy_ifc$val', rt.Port('input', rdt.Vector(1)) ),
    ( 'ifc$__1$ctrl_bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc$__1$ctrl_foo', rt.Port('output', rdt.Vector(32)) ),
    ( 'ifc$__1$valrdy_ifc$msg', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc$__1$valrdy_ifc$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc$__1$valrdy_ifc$val', rt.Port('input', rdt.Vector(1)) )
  ]
  a._ref_ports_yosys = a._ref_ports
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
  a._ref_ports = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) ),
    ( 'ifc$__0$ctrl_bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc$__0$ctrl_foo', rt.Port('output', rdt.Vector(32)) ),
    ( 'ifc$__0$valrdy_ifc$msg', rt.Array([2], rt.Port('input', rdt.Vector(32))) ),
    ( 'ifc$__0$valrdy_ifc$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc$__0$valrdy_ifc$val', rt.Port('input', rdt.Vector(1)) ),
    ( 'ifc$__1$ctrl_bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc$__1$ctrl_foo', rt.Port('output', rdt.Vector(32)) ),
    ( 'ifc$__1$valrdy_ifc$msg', rt.Array([2], rt.Port('input', rdt.Vector(32))) ),
    ( 'ifc$__1$valrdy_ifc$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc$__1$valrdy_ifc$val', rt.Port('input', rdt.Vector(1)) )
  ]
  a._ref_ports_yosys = [
    ( 'clk', rt.Port('input', rdt.Vector(1)) ),
    ( 'reset', rt.Port('input', rdt.Vector(1)) ),
    ( 'ifc$__0$ctrl_bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc$__0$ctrl_foo', rt.Port('output', rdt.Vector(32)) ),
    ( 'ifc$__0$valrdy_ifc$msg$__0', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc$__0$valrdy_ifc$msg$__1', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc$__0$valrdy_ifc$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc$__0$valrdy_ifc$val', rt.Port('input', rdt.Vector(1)) ),
    ( 'ifc$__1$ctrl_bar', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc$__1$ctrl_foo', rt.Port('output', rdt.Vector(32)) ),
    ( 'ifc$__1$valrdy_ifc$msg$__0', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc$__1$valrdy_ifc$msg$__1', rt.Port('input', rdt.Vector(32)) ),
    ( 'ifc$__1$valrdy_ifc$rdy', rt.Port('output', rdt.Vector(1)) ),
    ( 'ifc$__1$valrdy_ifc$val', rt.Port('input', rdt.Vector(1)) )
  ]
  do_test( a )
