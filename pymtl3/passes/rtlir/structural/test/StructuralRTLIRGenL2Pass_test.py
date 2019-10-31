#=========================================================================
# StructuralRTLIRGenL2Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the generation of level 2 structural RTLIR."""

import pytest

import pymtl3.dsl as dsl
from pymtl3.datatypes import Bits32, bitstruct
from pymtl3.passes.rtlir.structural.StructuralRTLIRGenL2Pass import (
    StructuralRTLIRGenL2Pass,
)
from pymtl3.passes.rtlir.structural.StructuralRTLIRSignalExpr import *

from .StructuralRTLIRGenL1Pass_test import gen_connections


def test_L2_struct_attr():
  @bitstruct
  class B:
    foo: Bits32

  class A( dsl.Component ):
    def construct( s ):
      s.in_ = dsl.InPort( B )
      s.out = dsl.OutPort( Bits32 )
      dsl.connect( s.out, s.in_.foo )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL2Pass( gen_connections( a ) ) )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  assert ns.connections == \
    [(StructAttr(CurCompAttr(comp, 'in_'), 'foo'), CurCompAttr(comp, 'out'))]

def test_L2_packed_index():
  @bitstruct
  class B:
    foo: [ Bits32 ] * 5
  class A( dsl.Component ):
    def construct( s ):
      s.in_ = dsl.InPort( B )
      s.out = dsl.OutPort( Bits32 )
      dsl.connect( s.out, s.in_.foo[1] )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL2Pass( gen_connections( a ) ) )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  assert ns.connections == \
    [(PackedIndex(StructAttr(CurCompAttr(comp, 'in_'), 'foo'), 1),
      CurCompAttr(comp, 'out'))]
