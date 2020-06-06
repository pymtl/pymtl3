#=========================================================================
# VNameMangle_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 30, 2019
"""Test the SystemVerilog name mangling."""

from pymtl3.datatypes import Bits1, Bits32, bitstruct
from pymtl3.dsl import Component, InPort, Interface, OutPort
from pymtl3.passes.backends.verilog.util.utility import gen_mapped_ports
from pymtl3.passes.rtlir import RTLIRDataType as rdt
from pymtl3.passes.rtlir import RTLIRType as rt
from pymtl3.passes.rtlir.util.test_utility import do_test


def local_do_test( m ):
  m.elaborate()
  result = gen_mapped_ports( m, {} )
  assert result == m._ref_ports

def test_port_single( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
  a = A()
  a._ref_ports = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['in_'], 'in_', rt.Port('input', rdt.Vector(32)), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
  ]
  a._ref_ports_yosys = a._ref_ports
  do_test( a )

def test_port_array( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range( 3 ) ]
  a = A()
  a._ref_ports = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['in_'], 'in_', rt.Array([3], rt.Port('input', rdt.Vector(32))), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
  ]
  a._ref_ports_yosys = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['in_[0]'], 'in___0', rt.Port('input', rdt.Vector(32)), 0 ),
    ( ['in_[1]'], 'in___1', rt.Port('input', rdt.Vector(32)), 0 ),
    ( ['in_[2]'], 'in___2', rt.Port('input', rdt.Vector(32)), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
  ]
  do_test( a )

def test_port_2d_array( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ [ InPort( Bits32 ) for _ in range(2) ] for _ in range(3) ]
  a = A()
  a._ref_ports = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['in_'], 'in_', rt.Array( [3, 2], rt.Port('input', rdt.Vector(32)) ), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
    ]
  a._ref_ports_yosys = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['in_[0][0]'], 'in___0__0', rt.Port('input', rdt.Vector(32)), 0 ),
    ( ['in_[0][1]'], 'in___0__1', rt.Port('input', rdt.Vector(32)), 0 ),
    ( ['in_[1][0]'], 'in___1__0', rt.Port('input', rdt.Vector(32)), 0 ),
    ( ['in_[1][1]'], 'in___1__1', rt.Port('input', rdt.Vector(32)), 0 ),
    ( ['in_[2][0]'], 'in___2__0', rt.Port('input', rdt.Vector(32)), 0 ),
    ( ['in_[2][1]'], 'in___2__1', rt.Port('input', rdt.Vector(32)), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
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
  st = rdt.Struct(struct, {'bar':rdt.Vector(32), 'foo':rdt.Vector(32)})
  a._ref_ports = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['in_'], 'in_', rt.Port('input', st ), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
  ]
  a._ref_ports_yosys = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['in_.bar'], 'in___bar', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_.foo'], 'in___foo', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
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
  st = rdt.Struct(struct, {'bar':rdt.Vector(32), 'foo':rdt.Vector(32)})
  a._ref_ports = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['in_'], 'in_', rt.Array([2], rt.Port('input', st)), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
  ]
  a._ref_ports_yosys = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['in_[0].bar'], 'in___0__bar', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[0].foo'], 'in___0__foo', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[1].bar'], 'in___1__bar', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[1].foo'], 'in___1__foo', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
  ]
  do_test( a )

def test_packed_array_port_array( do_test ):
  @bitstruct
  class struct:
    bar: Bits32
    foo: [ [ Bits32 ] * 2 ] * 3
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( struct ) for _ in range(2) ]
  a = A()
  foo = rdt.PackedArray([3,2], rdt.Vector(32))
  st = rdt.Struct(struct, {'bar':rdt.Vector(32), 'foo':foo})
  a._ref_ports = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['in_'], 'in_', rt.Array([2], rt.Port('input', st)), 0),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
  ]
  a._ref_ports_yosys = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['in_[0].bar'], 'in___0__bar', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[0].foo[0][0]'], 'in___0__foo__0__0', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[0].foo[0][1]'], 'in___0__foo__0__1', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[0].foo[1][0]'], 'in___0__foo__1__0', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[0].foo[1][1]'], 'in___0__foo__1__1', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[0].foo[2][0]'], 'in___0__foo__2__0', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[0].foo[2][1]'], 'in___0__foo__2__1', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[1].bar'], 'in___1__bar', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[1].foo[0][0]'], 'in___1__foo__0__0', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[1].foo[0][1]'], 'in___1__foo__0__1', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[1].foo[1][0]'], 'in___1__foo__1__0', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[1].foo[1][1]'], 'in___1__foo__1__1', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[1].foo[2][0]'], 'in___1__foo__2__0', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[1].foo[2][1]'], 'in___1__foo__2__1', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
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
  inner = rdt.Struct(inner_struct, {'foo':rdt.Vector(32)})
  st = rdt.Struct(struct, {'bar':rdt.Vector(32), 'inner':inner})
  a._ref_ports = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['in_'], 'in_', rt.Array([2], rt.Port('input', st )), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
  ]
  a._ref_ports_yosys = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['in_[0].bar'], 'in___0__bar', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[0].inner.foo'], 'in___0__inner__foo', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[1].bar'], 'in___1__bar', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['in_[1].inner.foo'], 'in___1__inner__foo', rt.Port('input', rdt.Vector(32) ), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
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
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['ifc.msg'], 'ifc__msg', rt.Port('input', rdt.Vector(32)), 0 ),
    ( ['ifc.rdy'], 'ifc__rdy', rt.Port('output', rdt.Vector(1)), 0 ),
    ( ['ifc.val'], 'ifc__val', rt.Port('input', rdt.Vector(1)), 0 ),
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
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['ifc[0].msg', 'ifc[1].msg'], 'ifc__msg', rt.Array([2], rt.Port('input', rdt.Vector(32))), 1 ),
    ( ['ifc[0].rdy', 'ifc[1].rdy'], 'ifc__rdy', rt.Array([2], rt.Port('output', rdt.Vector(1))), 1 ),
    ( ['ifc[0].val', 'ifc[1].val'], 'ifc__val', rt.Array([2], rt.Port('input', rdt.Vector(1))), 1 ),
  ]
  a._ref_ports_yosys = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['ifc[0].msg'], 'ifc__0__msg', rt.Port('input', rdt.Vector(32)), 1 ),
    ( ['ifc[0].rdy'], 'ifc__0__rdy', rt.Port('output', rdt.Vector(1)), 1 ),
    ( ['ifc[0].val'], 'ifc__0__val', rt.Port('input', rdt.Vector(1)), 1 ),
    ( ['ifc[1].msg'], 'ifc__1__msg', rt.Port('input', rdt.Vector(32)), 1 ),
    ( ['ifc[1].rdy'], 'ifc__1__rdy', rt.Port('output', rdt.Vector(1)), 1 ),
    ( ['ifc[1].val'], 'ifc__1__val', rt.Port('input', rdt.Vector(1)), 1 ),
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
  a._ref_ports = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['ifc[0].ctrl_bar', 'ifc[1].ctrl_bar'], 'ifc__ctrl_bar', rt.Array([2], rt.Port('input', rdt.Vector(32))), 1 ),
    ( ['ifc[0].ctrl_foo', 'ifc[1].ctrl_foo'], 'ifc__ctrl_foo', rt.Array([2], rt.Port('output', rdt.Vector(32))), 1 ),
    ( ['ifc[0].valrdy_ifc.msg', 'ifc[1].valrdy_ifc.msg'], 'ifc__valrdy_ifc__msg', rt.Array([2], rt.Port('input', rdt.Vector(32))), 1 ),
    ( ['ifc[0].valrdy_ifc.rdy', 'ifc[1].valrdy_ifc.rdy'], 'ifc__valrdy_ifc__rdy', rt.Array([2], rt.Port('output', rdt.Vector(1))), 1 ),
    ( ['ifc[0].valrdy_ifc.val', 'ifc[1].valrdy_ifc.val'], 'ifc__valrdy_ifc__val', rt.Array([2], rt.Port('input', rdt.Vector(1))), 1 ),
  ]
  a._ref_ports_yosys = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['ifc[0].ctrl_bar'], 'ifc__0__ctrl_bar', rt.Port('input', rdt.Vector(32)), 1 ),
    ( ['ifc[0].ctrl_foo'], 'ifc__0__ctrl_foo', rt.Port('output', rdt.Vector(32)), 1 ),
    ( ['ifc[0].valrdy_ifc.msg'], 'ifc__0__valrdy_ifc__msg', rt.Port('input', rdt.Vector(32)), 1 ),
    ( ['ifc[0].valrdy_ifc.rdy'], 'ifc__0__valrdy_ifc__rdy', rt.Port('output', rdt.Vector(1)), 1 ),
    ( ['ifc[0].valrdy_ifc.val'], 'ifc__0__valrdy_ifc__val', rt.Port('input', rdt.Vector(1)), 1 ),
    ( ['ifc[1].ctrl_bar'], 'ifc__1__ctrl_bar', rt.Port('input', rdt.Vector(32)), 1 ),
    ( ['ifc[1].ctrl_foo'], 'ifc__1__ctrl_foo', rt.Port('output', rdt.Vector(32)), 1 ),
    ( ['ifc[1].valrdy_ifc.msg'], 'ifc__1__valrdy_ifc__msg', rt.Port('input', rdt.Vector(32)), 1 ),
    ( ['ifc[1].valrdy_ifc.rdy'], 'ifc__1__valrdy_ifc__rdy', rt.Port('output', rdt.Vector(1)), 1 ),
    ( ['ifc[1].valrdy_ifc.val'], 'ifc__1__valrdy_ifc__val', rt.Port('input', rdt.Vector(1)), 1 ),
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
  a._ref_ports = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['ifc[0].ctrl_bar', 'ifc[1].ctrl_bar'], 'ifc__ctrl_bar', rt.Array([2], rt.Port('input', rdt.Vector(32))), 1 ),
    ( ['ifc[0].ctrl_foo', 'ifc[1].ctrl_foo'], 'ifc__ctrl_foo', rt.Array([2], rt.Port('output', rdt.Vector(32))), 1 ),
    ( ['ifc[0].valrdy_ifc.msg', 'ifc[1].valrdy_ifc.msg'], 'ifc__valrdy_ifc__msg', rt.Array([2, 2], rt.Port('input', rdt.Vector(32))), 1 ),
    ( ['ifc[0].valrdy_ifc.rdy', 'ifc[1].valrdy_ifc.rdy'], 'ifc__valrdy_ifc__rdy', rt.Array([2], rt.Port('output', rdt.Vector(1))), 1 ),
    ( ['ifc[0].valrdy_ifc.val', 'ifc[1].valrdy_ifc.val'], 'ifc__valrdy_ifc__val', rt.Array([2], rt.Port('input', rdt.Vector(1))), 1 ),
  ]
  a._ref_ports_yosys = [
    ( ['clk'], 'clk', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['reset'], 'reset', rt.Port('input', rdt.Vector(1)), 0 ),
    ( ['ifc[0].ctrl_bar'], 'ifc__0__ctrl_bar', rt.Port('input', rdt.Vector(32)), 1 ),
    ( ['ifc[0].ctrl_foo'], 'ifc__0__ctrl_foo', rt.Port('output', rdt.Vector(32)), 1 ),
    ( ['ifc[0].valrdy_ifc.msg[0]'], 'ifc__0__valrdy_ifc__msg__0', rt.Port('input', rdt.Vector(32)), 1 ),
    ( ['ifc[0].valrdy_ifc.msg[1]'], 'ifc__0__valrdy_ifc__msg__1', rt.Port('input', rdt.Vector(32)), 1 ),
    ( ['ifc[0].valrdy_ifc.rdy'], 'ifc__0__valrdy_ifc__rdy', rt.Port('output', rdt.Vector(1)), 1 ),
    ( ['ifc[0].valrdy_ifc.val'], 'ifc__0__valrdy_ifc__val', rt.Port('input', rdt.Vector(1)), 1 ),
    ( ['ifc[1].ctrl_bar'], 'ifc__1__ctrl_bar', rt.Port('input', rdt.Vector(32)), 1 ),
    ( ['ifc[1].ctrl_foo'], 'ifc__1__ctrl_foo', rt.Port('output', rdt.Vector(32)), 1 ),
    ( ['ifc[1].valrdy_ifc.msg[0]'], 'ifc__1__valrdy_ifc__msg__0', rt.Port('input', rdt.Vector(32)), 1 ),
    ( ['ifc[1].valrdy_ifc.msg[1]'], 'ifc__1__valrdy_ifc__msg__1', rt.Port('input', rdt.Vector(32)), 1 ),
    ( ['ifc[1].valrdy_ifc.rdy'], 'ifc__1__valrdy_ifc__rdy', rt.Port('output', rdt.Vector(1)), 1 ),
    ( ['ifc[1].valrdy_ifc.val'], 'ifc__1__valrdy_ifc__val', rt.Port('input', rdt.Vector(1)), 1 ),
  ]
  do_test( a )
