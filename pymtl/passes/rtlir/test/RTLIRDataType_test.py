#=========================================================================
# RTLIRDataType_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the implementation of RTLIR data types."""

from __future__ import absolute_import, division, print_function

import pytest

from pymtl import *
from pymtl.passes.rtlir import RTLIRDataType as rdt
from pymtl.passes.rtlir import get_rtlir_dtype
from pymtl.passes.rtlir.errors import RTLIRConversionError

from .test_utility import expected_failure


def test_py_int():
  assert rdt.Vector(32) == get_rtlir_dtype( 42 )

def test_py_float():
  with expected_failure( RTLIRConversionError ):
    get_rtlir_dtype( 3.14 )

def test_py_string():
  with expected_failure( RTLIRConversionError ):
    get_rtlir_dtype( 'RTLIR' )

def test_py_list():
  with expected_failure( RTLIRConversionError, 'should be a field of some struct' ):
    get_rtlir_dtype( [ 1, 2, 3 ] )

def test_py_struct_arg_no_default_value():
  class B( object ):
    def __init__( s, foo ):
      s.foo = Bits32( foo )
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
  a = A()
  with expected_failure( TypeError, 'takes exactly 2 arguments (1 given)' ):
    a.elaborate()
    get_rtlir_dtype( a.in_ )

def test_py_struct():
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = Bits32( foo )
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
  a = A()
  a.elaborate()
  assert rdt.Struct( 'B', {'foo':rdt.Vector(32)}, ['foo'] ) == get_rtlir_dtype( a.in_ )

def test_pymtl_Bits():
  assert rdt.Vector(1) == get_rtlir_dtype( Bits1(0) )
  assert rdt.Vector(2) == get_rtlir_dtype( Bits2(0) )
  assert rdt.Vector(8) == get_rtlir_dtype( Bits8(0) )
  assert rdt.Vector(32) == get_rtlir_dtype( Bits32(0) )
  assert rdt.Vector(255) == get_rtlir_dtype( Bits255(0) )

def test_pymtl_signal():
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
  a = A()
  a.elaborate()
  assert rdt.Vector(32) == get_rtlir_dtype( a.in_ )

def test_pymtl_packed_array():
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = [ Bits32( foo ) for _ in xrange(5) ]
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
  a = A()
  a.elaborate()
  assert rdt.Struct( 'B', {'foo':rdt.PackedArray([5], rdt.Vector(32))}, ['foo'] ) == \
         get_rtlir_dtype( a.in_ )
