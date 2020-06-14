#=========================================================================
# RTLIRDataType_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the implementation of RTLIR data types."""

import pytest

from pymtl3.datatypes import *
from pymtl3.dsl import Component, InPort, OutPort
from pymtl3.passes.rtlir.errors import RTLIRConversionError
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.rtlir.util.test_utility import expected_failure
from pymtl3.passes.testcases import (
    Bits32Foo,
    Bits32x5Foo,
    CaseBits32PortOnly,
    CasePackedArrayStructPortOnly,
    CaseStructPortOnly,
)


def test_py_int():
  assert rdt.get_rtlir_dtype( 42 ) == rdt.Vector(6)

def test_py_float():
  with expected_failure( RTLIRConversionError ):
    rdt.get_rtlir_dtype( 3.14 )

def test_py_string():
  with expected_failure( RTLIRConversionError ):
    rdt.get_rtlir_dtype( 'RTLIR' )

def test_py_list():
  with expected_failure( RTLIRConversionError, 'should be a field of some struct' ):
    rdt.get_rtlir_dtype( [ 1, 2, 3 ] )

def test_py_struct():
  a = CaseStructPortOnly.DUT()
  a.elaborate()
  assert rdt.get_rtlir_dtype( a.in_ ) == rdt.Struct( Bits32Foo, {'foo':rdt.Vector(32)} )

def test_pymtl_Bits():
  assert rdt.get_rtlir_dtype( Bits1(0) ) == rdt.Vector(1)
  assert rdt.get_rtlir_dtype( Bits2(0) ) == rdt.Vector(2)
  assert rdt.get_rtlir_dtype( Bits8(0) ) == rdt.Vector(8)
  assert rdt.get_rtlir_dtype( Bits32(0) ) == rdt.Vector(32)
  assert rdt.get_rtlir_dtype( Bits255(0) ) == rdt.Vector(255)

def test_pymtl_signal():
  a = CaseBits32PortOnly.DUT()
  a.elaborate()
  assert rdt.get_rtlir_dtype( a.in_ ) == rdt.Vector(32)

def test_pymtl_packed_array():
  a = CasePackedArrayStructPortOnly.DUT()
  a.elaborate()
  assert rdt.get_rtlir_dtype( a.in_ ) == \
      rdt.Struct( Bits32x5Foo, {'foo':rdt.PackedArray([5], rdt.Vector(32))} )
