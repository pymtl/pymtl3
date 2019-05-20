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
from pymtl.passes.rtlir.RTLIRDataType import Vector
from pymtl.passes.rtlir.structural.StructuralRTLIRGenL2Pass import (
    StructuralRTLIRGenL2Pass,
)
from pymtl.passes.rtlir.structural.StructuralRTLIRSignalExpr import *


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
  comp = CurComp(a, 's')
  assert ns.connections == \
    [(StructAttr(CurCompAttr(comp, 'in_'), 'foo'), CurCompAttr(comp, 'out'))]

@pytest.mark.xfail( reason = 'PyMTL DSL connection parsing failed' )
def test_L2_packed_index():
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = [ Bits32( foo ) for _ in xrange(5) ]
  class A( pymtl.Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits32 )
      # PyMTL mistakenly takes s.in_.foo[1] as a single bit!
      s.connect( s.out, s.in_.foo[1] )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL2Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  assert ns.connections == \
    [(PackedIndex(StructAttr(CurCompAttr(comp, 'in_'), 'foo'), 1),
      CurCompAttr(comp, 'out'))]
