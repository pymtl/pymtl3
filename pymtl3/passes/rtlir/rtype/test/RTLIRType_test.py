#=========================================================================
# RTLIRType_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the implementation of RTLIR types."""

import pytest

import pymtl3.dsl as dsl
from pymtl3.datatypes import Bits1, Bits16, Bits32
from pymtl3.passes.rtlir.errors import RTLIRConversionError
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.rtlir.rtype import RTLIRType as rt
from pymtl3.passes.rtlir.util.test_utility import expected_failure


def test_pymtl3_list_ports():
  class A( dsl.Component ):
    def construct( s ):
      s.in_ = [ dsl.InPort( Bits32 ) for _ in range(5) ]
  a = A()
  a.elaborate()
  assert rt.is_rtlir_convertible( a.in_ )
  assert rt.Array([5], rt.Port('input', rdt.Vector(32))) == rt.get_rtlir( a.in_ )

def test_pymtl3_list_wires():
  class A( dsl.Component ):
    def construct( s ):
      s.in_ = [ dsl.Wire( Bits32 ) for _ in range(5) ]
  a = A()
  a.elaborate()
  assert rt.is_rtlir_convertible( a.in_ )
  assert rt.Array([5], rt.Wire(rdt.Vector(32))) == rt.get_rtlir( a.in_ )

def test_pymtl3_list_consts():
  class A( dsl.Component ):
    def construct( s ):
      s.in_ = [ Bits32(42) for _ in range(5) ]
  a = A()
  a.elaborate()
  assert rt.is_rtlir_convertible( a.in_ )
  assert rt.Array([5], rt.Const(rdt.Vector(32))) == rt.get_rtlir( a.in_ )

def test_pymtl3_list_interface_views():
  class Ifc( dsl.Interface ):
    def construct( s ):
      s.msg = dsl.OutPort( Bits32 )
      s.rdy = dsl.InPort ( Bits1 )
  class A( dsl.Component ):
    def construct( s ):
      s.in_ = [ Ifc() for _ in range(5) ]
  a = A()
  a.elaborate()
  assert rt.is_rtlir_convertible( a.in_ )
  assert rt.Array([5],
    rt.InterfaceView('Ifc',
      {'msg':rt.Port('output', rdt.Vector(32)), 'rdy':rt.Port('input', rdt.Vector(1))})) == \
        rt.get_rtlir( a.in_ )

def test_pymtl_list_components():
  class B( dsl.Component ):
    def construct( s ):
      s.in_ = dsl.InPort( Bits32 )
      s.out = dsl.OutPort( Bits32 )
  class A( dsl.Component ):
    def construct( s ):
      s.b = [ B() for _ in range(5) ]
  a = A()
  a.elaborate()
  assert rt.is_rtlir_convertible( a.b )
  assert rt.Array([5], rt.Component( a.b[0],
    {'in_':rt.Port('input', rdt.Vector(32)), 'out':rt.Port('output', rdt.Vector(32))})) == \
        rt.get_rtlir( a.b )

def test_pymtl_list_multi_dimension():
  class A( dsl.Component ):
    def construct( s ):
      s.out = [[[dsl.OutPort(Bits32) for _ in range(1)] \
              for _ in range(2)] for _ in range(3)]
  a = A()
  a.elaborate()
  assert rt.is_rtlir_convertible( a.out )
  assert rt.Array([3, 2, 1], rt.Port('output', rdt.Vector(32))) == rt.get_rtlir(a.out)

def test_py_float():
  with expected_failure( RTLIRConversionError ):
    rt.get_rtlir( 3.14 )

def test_py_string():
  with expected_failure( RTLIRConversionError ):
    rt.get_rtlir( 'abc' )

def test_py_empty_list():
  # This is no longer an error: empty lists will be dropped instead of
  # triggering an error.
  # with expected_failure( RTLIRConversionError, 'list [] is empty' ):
  rt.get_rtlir( [] )

def test_py_untyped_list():
  with expected_failure( RTLIRConversionError, 'must have the same type' ):
    rt.get_rtlir( [ 4, Bits16(42) ] )

def test_pymtl3_interface_wire():
  class Ifc( dsl.Interface ):
    def construct( s ):
      s.foo = dsl.Wire( Bits32 )
      s.bar = dsl.InPort( Bits32 )
  class A( dsl.Component ):
    def construct( s ):
      s.in_ = Ifc()
  a = A()
  a.elaborate()
  # in_.foo will be silently dropped!
  rt.get_rtlir( a.in_ )
