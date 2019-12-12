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
from pymtl3.testcases import (
    CaseBits32PortOnly,
    CasePackedArrayStructPortOnly,
    CaseStructPortOnly,
)


def test_py_int():
  assert rdt.Vector(32) == rdt.get_rtlir_dtype( 42 )

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
  assert rdt.Struct( 'Bits32Foo', {'foo':rdt.Vector(32)} ) == rdt.get_rtlir_dtype( a.in_ )

def test_pymtl_Bits():
  assert rdt.Vector(1) == rdt.get_rtlir_dtype( Bits1(0) )
  assert rdt.Vector(2) == rdt.get_rtlir_dtype( Bits2(0) )
  assert rdt.Vector(8) == rdt.get_rtlir_dtype( Bits8(0) )
  assert rdt.Vector(32) == rdt.get_rtlir_dtype( Bits32(0) )
  assert rdt.Vector(255) == rdt.get_rtlir_dtype( Bits255(0) )

def test_pymtl_signal():
  a = CaseBits32PortOnly.DUT()
  a.elaborate()
  assert rdt.Vector(32) == rdt.get_rtlir_dtype( a.in_ )

def test_pymtl_packed_array():
  a = CasePackedArrayStructPortOnly.DUT()
  a.elaborate()
  assert rdt.Struct( 'Bits32x5Foo', {'foo':rdt.PackedArray([5], rdt.Vector(32))} ) == \
         rdt.get_rtlir_dtype( a.in_ )
