#=========================================================================
# RTLIRType_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the implementation of RTLIR types."""

from pymtl3 import Bits16
from pymtl3.passes.rtlir.errors import RTLIRConversionError
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.rtlir.rtype import RTLIRType as rt
from pymtl3.passes.rtlir.util.test_utility import expected_failure
from pymtl3.passes.testcases import (
    CaseBits32InOutx5CompOnly,
    CaseBits32MsgRdyIfcOnly,
    CaseBits32Outx3x2x1PortOnly,
    CaseBits32WireIfcOnly,
    CaseBits32x5ConstOnly,
    CaseBits32x5PortOnly,
    CaseBits32x5WireOnly,
)

rtlir_getter = rt.RTLIRGetter()

def test_pymtl3_list_ports():
  a = CaseBits32x5PortOnly.DUT()
  a.elaborate()
  assert rt.is_rtlir_convertible( a.in_ )
  assert rtlir_getter.get_rtlir( a.in_ ) == rt.Array([5], rt.Port('input', rdt.Vector(32)))

def test_pymtl3_list_wires():
  a = CaseBits32x5WireOnly.DUT()
  a.elaborate()
  assert rt.is_rtlir_convertible( a.in_ )
  assert rtlir_getter.get_rtlir( a.in_ ) == rt.Array([5], rt.Wire(rdt.Vector(32)))

def test_pymtl3_list_consts():
  a = CaseBits32x5ConstOnly.DUT()
  a.elaborate()
  getter = rt.RTLIRGetter()
  assert rt.is_rtlir_convertible( a.in_ )
  assert rtlir_getter.get_rtlir( a.in_ ) == rt.Array([5], rt.Const(rdt.Vector(32)))

def test_pymtl3_list_interface_views():
  a = CaseBits32MsgRdyIfcOnly.DUT()
  a.elaborate()
  assert rt.is_rtlir_convertible( a.in_ )
  assert rtlir_getter.get_rtlir( a.in_ ) == \
      rt.Array([5], rt.InterfaceView('Bits32MsgRdyIfc',
      {'msg':rt.Port('output', rdt.Vector(32)), 'rdy':rt.Port('input', rdt.Vector(1))}))

def test_pymtl_list_components():
  a = CaseBits32InOutx5CompOnly.DUT()
  a.elaborate()
  assert rt.is_rtlir_convertible( a.b )
  assert rtlir_getter.get_rtlir( a.b ) == \
  rt.Array([5], rt.Component( a.b[0], {
          'clk':rt.Port('input', rdt.Vector(1)),
          'reset':rt.Port('input', rdt.Vector(1)),
          'in_':rt.Port('input', rdt.Vector(32)),
          'out':rt.Port('output', rdt.Vector(32)),
        }))

def test_pymtl_list_multi_dimension():
  a = CaseBits32Outx3x2x1PortOnly.DUT()
  a.elaborate()
  assert rt.is_rtlir_convertible( a.out )
  assert rtlir_getter.get_rtlir(a.out) == rt.Array([3, 2, 1], rt.Port('output', rdt.Vector(32)))

def test_py_float():
  with expected_failure( RTLIRConversionError ):
    rtlir_getter.get_rtlir( 3.14 )

def test_py_string():
  with expected_failure( RTLIRConversionError ):
    rtlir_getter.get_rtlir( 'abc' )

def test_py_empty_list():
  # This is no longer an error: empty lists will be dropped instead of
  # triggering an error.
  # with expected_failure( RTLIRConversionError, 'list [] is empty' ):
  assert rtlir_getter.get_rtlir( [] ) == None

def test_py_untyped_list():
  with expected_failure( RTLIRConversionError, 'must have the same type' ):
    rtlir_getter.get_rtlir( [ 4, Bits16(42) ] )

def test_pymtl3_interface_wire():
  a = CaseBits32WireIfcOnly.DUT()
  a.elaborate()
  # in_.foo will be silently dropped!
  assert rtlir_getter.get_rtlir( a.in_ ) == rt.InterfaceView('Bits32FooWireBarInIfc',
      {'bar':rt.Port('input', rdt.Vector(32))})
