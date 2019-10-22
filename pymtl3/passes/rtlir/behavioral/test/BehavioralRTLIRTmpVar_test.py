#=========================================================================
# BehavioralRTLIRTmpVar_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Test the temporary variable generation of behavioral RTLIR passes."""

import pytest

import pymtl3.dsl as dsl
from pymtl3.datatypes import Bits16, Bits32, bitstruct
from pymtl3.passes.rtlir.behavioral import (
    BehavioralRTLIRGenPass,
    BehavioralRTLIRTypeCheckPass,
    BehavioralRTLIRVisualizationPass,
)
from pymtl3.passes.rtlir.errors import PyMTLTypeError
from pymtl3.passes.rtlir.rtype import RTLIRDataType as rdt
from pymtl3.passes.rtlir.rtype import RTLIRType as rt
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure


def local_do_test( m ):
  """Check if generated behavioral RTLIR is the same as reference."""
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )
  m.apply( BehavioralRTLIRVisualizationPass() )
  ref = m._rtlir_tmpvar_ref
  ns = m._pass_behavioral_rtlir_type_check

  for tvar_name in ref.keys():
    assert tvar_name in ns.rtlir_tmpvars
    assert ns.rtlir_tmpvars[tvar_name] == ref[tvar_name]

def test_tmp_wire( do_test ):
  class A( dsl.Component ):
    def construct( s ):
      s.in_ = dsl.InPort( Bits32 )
      s.out = dsl.OutPort( Bits32 )
      @s.update
      def upblk():
        u = s.in_ + Bits32(42)
        s.out = u
  a = A()
  a.elaborate()
  a._rtlir_tmpvar_ref = {('u', 'upblk') : rt.Wire(rdt.Vector(32))}
  do_test( a )

def test_tmp_wire_struct( do_test ):
  @bitstruct
  class B:
    foo: Bits32
  class A( dsl.Component ):
    def construct( s ):
      s.in_ = dsl.InPort( B )
      s.out = dsl.OutPort( Bits32 )
      @s.update
      def upblk():
        u = s.in_
        s.out = u.foo
  a = A()
  a.elaborate()
  a._rtlir_tmpvar_ref = \
    {('u', 'upblk') : rt.Wire(rdt.Struct('B', {'foo':rdt.Vector(32)}))}
  do_test( a )

def test_tmp_wire_overwrite_conflict_type( do_test ):
  class A( dsl.Component ):
    def construct( s ):
      s.in_1 = dsl.InPort( Bits32 )
      s.in_2 = dsl.InPort( Bits16 )
      s.out = dsl.OutPort( Bits32 )
      @s.update
      def upblk():
        u = s.in_1 + Bits32(42)
        u = s.in_2 + Bits16(1)
        s.out = u
  a = A()
  a.elaborate()
  with expected_failure( PyMTLTypeError, "conflicting type" ):
    do_test( a )

def test_tmp_scope_conflict_type( do_test ):
  class A( dsl.Component ):
    def construct( s ):
      s.in_1 = dsl.InPort( Bits32 )
      s.in_2 = dsl.InPort( Bits16 )
      s.out = dsl.OutPort( Bits32 )
      @s.update
      def upblk():
        if 1:
          u = s.in_1 + Bits32(42)
          s.out = u
        else:
          u = s.in_2 + Bits16(1)
          s.out = u
  a = A()
  a.elaborate()
  with expected_failure( PyMTLTypeError, "conflicting type" ):
    do_test( a )
