#=========================================================================
# BehavioralRTLIRTmpVar_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Test the temporary variable generation of behavioral RTLIR passes."""

from __future__ import absolute_import, division, print_function

import pytest

import pymtl.passes.rtlir.RTLIRDataType as rdt
import pymtl.passes.rtlir.RTLIRType as rt
from pymtl import *
from pymtl.passes.rtlir.behavioral import (
    BehavioralRTLIRGenPass,
    BehavioralRTLIRTypeCheckPass,
    BehavioralRTLIRVisualizationPass,
)
from pymtl.passes.rtlir.behavioral.BehavioralRTLIR import *
from pymtl.passes.rtlir.errors import PyMTLTypeError
from pymtl.passes.rtlir.test_utility import do_test, expected_failure


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
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        u = s.in_ + Bits32(42)
        s.out = u
  a = A()
  a.elaborate()
  a._rtlir_tmpvar_ref = {('u', 'upblk') : rt.Wire(rdt.Vector(32))}
  do_test( a )

def test_tmp_wire_struct( do_test ):
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = Bits32(foo)
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        u = s.in_
        s.out = u.foo
  a = A()
  a.elaborate()
  a._rtlir_tmpvar_ref = \
    {('u', 'upblk') : rt.Wire(rdt.Struct('B', {'foo':rdt.Vector(32)}, ['foo']))}
  do_test( a )

def test_tmp_wire_overwrite_conflict_type( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits16 )
      s.out = OutPort( Bits32 )
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
  class A( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits16 )
      s.out = OutPort( Bits32 )
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
