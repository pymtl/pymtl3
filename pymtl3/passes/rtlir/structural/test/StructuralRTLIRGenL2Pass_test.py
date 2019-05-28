#=========================================================================
# StructuralRTLIRGenL2Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the generation of level 2 structural RTLIR."""

from __future__ import absolute_import, division, print_function

import pytest

from pymtl3.datatypes import Bits32
import pymtl3.dsl as dsl
from pymtl3.passes.rtlir.structural.StructuralRTLIRSignalExpr import *
from pymtl3.passes.rtlir.structural.StructuralRTLIRGenL2Pass import (
    StructuralRTLIRGenL2Pass,
)


def test_L2_struct_attr():
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = Bits32( foo )
  class A( dsl.Component ):
    def construct( s ):
      s.in_ = dsl.InPort( B )
      s.out = dsl.OutPort( Bits32 )
      s.connect( s.out, s.in_.foo )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL2Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  assert ns.connections == \
    [(StructAttr(CurCompAttr(comp, 'in_'), 'foo'), CurCompAttr(comp, 'out'))]

def test_L2_packed_index():
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = [ Bits32( foo ) for _ in xrange(5) ]
  class A( dsl.Component ):
    def construct( s ):
      s.in_ = dsl.InPort( B )
      s.out = dsl.OutPort( Bits32 )
      s.connect( s.out, s.in_.foo[1] )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL2Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  assert ns.connections == \
    [(PackedIndex(StructAttr(CurCompAttr(comp, 'in_'), 'foo'), 1),
      CurCompAttr(comp, 'out'))]
