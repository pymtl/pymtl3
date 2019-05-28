#=========================================================================
# RTLIRType_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the implementation of RTLIR types."""

from __future__ import absolute_import, division, print_function

import pytest

import pymtl3.datatypes as pymtl3_datatypes
import pymtl3.dsl as pymtl3_dsl
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt, RTLIRType as rt
from pymtl3.passes.rtlir.rtype.RTLIRType import get_rtlir, is_rtlir_convertible
from pymtl3.passes.rtlir.rtype.RTLIRDataType import get_rtlir_dtype
from pymtl3.passes.rtlir.errors import RTLIRConversionError
from pymtl3.passes.rtlir.util.test_utility import expected_failure


def test_pymtl3_list_ports():
  class A( pymtl3_dsl.Component ):
    def construct( s ):
      s.in_ = [ pymtl3_dsl.InPort( pymtl3_datatypes.Bits32 ) for _ in xrange(5) ]
  a = A()
  a.elaborate()
  assert is_rtlir_convertible( a.in_ )
  assert rt.Array([5], rt.Port('input', rdt.Vector(32))) == get_rtlir( a.in_ )

def test_pymtl3_list_wires():
  class A( pymtl3_dsl.Component ):
    def construct( s ):
      s.in_ = [ pymtl3_dsl.Wire( pymtl3_datatypes.Bits32 ) for _ in xrange(5) ]
  a = A()
  a.elaborate()
  assert is_rtlir_convertible( a.in_ )
  assert rt.Array([5], rt.Wire(rdt.Vector(32))) == get_rtlir( a.in_ )

def test_pymtl3_list_consts():
  class A( pymtl3_dsl.Component ):
    def construct( s ):
      s.in_ = [ pymtl3_datatypes.Bits32(42) for _ in xrange(5) ]
  a = A()
  a.elaborate()
  assert is_rtlir_convertible( a.in_ )
  assert rt.Array([5], rt.Const(rdt.Vector(32))) == get_rtlir( a.in_ )

def test_pymtl3_list_interface_views():
  class Ifc( pymtl3_dsl.Interface ):
    def construct( s ):
      s.msg = pymtl3_dsl.OutPort( pymtl3_datatypes.Bits32 )
      s.rdy = pymtl3_dsl.InPort ( pymtl3_datatypes.Bits1 )
  class A( pymtl3_dsl.Component ):
    def construct( s ):
      s.in_ = [ Ifc() for _ in xrange(5) ]
  a = A()
  a.elaborate()
  assert is_rtlir_convertible( a.in_ )
  assert rt.Array([5],
    rt.InterfaceView('Ifc',
      {'msg':rt.Port('output', rdt.Vector(32)), 'rdy':rt.Port('input', rdt.Vector(1))})) == \
        get_rtlir( a.in_ )

def test_pymtl_list_components():
  class B( pymtl3_dsl.Component ):
    def construct( s ):
      s.in_ = pymtl3_dsl.InPort( pymtl3_datatypes.Bits32 )
      s.out = pymtl3_dsl.OutPort( pymtl3_datatypes.Bits32 )
  class A( pymtl3_dsl.Component ):
    def construct( s ):
      s.b = [ B() for _ in xrange(5) ]
  a = A()
  a.elaborate()
  assert is_rtlir_convertible( a.b )
  assert rt.Array([5], rt.Component( a.b[0],
    {'in_':rt.Port('input', rdt.Vector(32)), 'out':rt.Port('output', rdt.Vector(32))})) == \
        get_rtlir( a.b )

def test_pymtl_list_multi_dimension():
  class A( pymtl3_dsl.Component ):
    def construct( s ):
      s.out = [[[pymtl3_dsl.OutPort(pymtl3_datatypes.Bits32) for _ in xrange(1)] \
              for _ in xrange(2)] for _ in xrange(3)]
  a = A()
  a.elaborate()
  assert is_rtlir_convertible( a.out )
  assert rt.Array([3, 2, 1], rt.Port('output', rdt.Vector(32))) == get_rtlir(a.out)

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
    get_rtlir( [ 4, pymtl3_datatypes.Bits16(42) ] )

def test_pymtl3_interface_wire():
  class Ifc( pymtl3_dsl.Interface ):
    def construct( s ):
      s.foo = pymtl3_dsl.Wire( pymtl3_datatypes.Bits32 )
      s.bar = pymtl3_dsl.InPort( pymtl3_datatypes.Bits32 )
  class A( pymtl3_dsl.Component ):
    def construct( s ):
      s.in_ = Ifc()
  a = A()
  a.elaborate()
  with expected_failure( RTLIRConversionError ):
    get_rtlir( a.in_ )
