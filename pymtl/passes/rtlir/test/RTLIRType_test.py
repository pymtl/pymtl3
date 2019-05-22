#=========================================================================
# RTLIRType_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the implementation of RTLIR types."""

from __future__ import absolute_import, division, print_function

import pytest

import pymtl
from pymtl import Bits1, Bits16, Bits32, InPort, Interface, OutPort
from pymtl.passes.rtlir.errors import RTLIRConversionError
from pymtl.passes.rtlir.RTLIRDataType import (
    BaseRTLIRDataType,
    Bool,
    PackedArray,
    Struct,
    Vector,
    get_rtlir_dtype,
)
from pymtl.passes.rtlir.RTLIRType import *
from pymtl.passes.rtlir.test_utility import expected_failure


def test_pymtl_list_ports():
  class A( pymtl.Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange(5) ]
  a = A()
  a.elaborate()
  assert is_rtlir_convertible( a.in_ )
  assert Array([5], Port('input', Vector(32))) == get_rtlir( a.in_ )

def test_pymtl_list_wires():
  class A( pymtl.Component ):
    def construct( s ):
      s.in_ = [ pymtl.Wire( Bits32 ) for _ in xrange(5) ]
  a = A()
  a.elaborate()
  assert is_rtlir_convertible( a.in_ )
  assert Array([5], Wire(Vector(32))) == get_rtlir( a.in_ )

def test_pymtl_list_consts():
  class A( pymtl.Component ):
    def construct( s ):
      s.in_ = [ Bits32(42) for _ in xrange(5) ]
  a = A()
  a.elaborate()
  assert is_rtlir_convertible( a.in_ )
  assert Array([5], Const(Vector(32))) == get_rtlir( a.in_ )

def test_pymtl_list_interface_views():
  class Ifc( Interface ):
    def construct( s ):
      s.msg = OutPort( Bits32 )
      s.rdy = InPort( Bits1 )
  class A( pymtl.Component ):
    def construct( s ):
      s.in_ = [ Ifc() for _ in xrange(5) ]
  a = A()
  a.elaborate()
  assert is_rtlir_convertible( a.in_ )
  assert Array([5],
    InterfaceView('Ifc',
      {'msg':Port('output', Vector(32)), 'rdy':Port('input', Vector(1))})) == \
        get_rtlir( a.in_ )

def test_pymtl_list_components():
  class B( pymtl.Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
  class A( pymtl.Component ):
    def construct( s ):
      s.b = [ B() for _ in xrange(5) ]
  a = A()
  a.elaborate()
  assert is_rtlir_convertible( a.b )
  assert Array([5], Component( a.b[0],
    {'in_':Port('input', Vector(32)), 'out':Port('output', Vector(32))})) == \
        get_rtlir( a.b )

def test_pymtl_list_multi_dimension():
  class A( pymtl.Component ):
    def construct( s ):
      s.out = [[[OutPort(Bits32) for _ in xrange(1)] \
              for _ in xrange(2)] for _ in xrange(3)]
  a = A()
  a.elaborate()
  assert is_rtlir_convertible( a.out )
  assert Array([3, 2, 1], Port('output', Vector(32))) == get_rtlir(a.out)

def test_py_float():
  with expected_failure( RTLIRConversionError ):
    get_rtlir( 3.14 )

def test_py_string():
  with expected_failure( RTLIRConversionError ):
    get_rtlir( 'abc' )

def test_py_empty_list():
  with expected_failure( RTLIRConversionError, 'list [] is empty' ):
    get_rtlir( [] )

def test_py_untyped_list():
  with expected_failure( RTLIRConversionError, 'must have the same type' ):
    get_rtlir( [ 4, Bits16(42) ] )

def test_pymtl_interface_wire():
  class Ifc( Interface ):
    def construct( s ):
      s.foo = pymtl.Wire( Bits32 )
      s.bar = InPort( Bits32 )
  class A( pymtl.Component ):
    def construct( s ):
      s.in_ = Ifc()
  a = A()
  a.elaborate()
  with expected_failure( RTLIRConversionError ):
    get_rtlir( a.in_ )
