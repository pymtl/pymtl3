#=========================================================================
# StructuralRTLIRGenL2Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the generation of level 2 structural RTLIR."""

from __future__ import absolute_import, division, print_function

import pytest

import pymtl
from pymtl import Bits1, Bits4, Bits32, InPort, OutPort
from pymtl.passes.BasePass import PassMetadata
from pymtl.passes.rtlir import StructuralRTLIRSignalExpr as sexp
from pymtl.passes.rtlir.structural.StructuralRTLIRGenL2Pass import (
    StructuralRTLIRGenL2Pass,
)


def test_L2_struct_attr():
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = Bits32( foo )
  class A( pymtl.Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits32 )
      s.connect( s.out, s.in_.foo )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL2Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = sexp.CurComp(a, 's')
  assert ns.connections == \
    [(sexp.StructAttr(sexp.CurCompAttr(comp, 'in_'), 'foo'), sexp.CurCompAttr(comp, 'out'))]

def test_L2_packed_index():
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = [ Bits32( foo ) for _ in xrange(5) ]
  class A( pymtl.Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits32 )
      s.connect( s.out, s.in_.foo[1] )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL2Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = sexp.CurComp(a, 's')
  assert ns.connections == \
    [(sexp.PackedIndex(sexp.StructAttr(sexp.CurCompAttr(comp, 'in_'), 'foo'), 1),
      sexp.CurCompAttr(comp, 'out'))]
