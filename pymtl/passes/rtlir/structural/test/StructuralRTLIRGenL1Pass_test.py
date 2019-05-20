#=========================================================================
# StructuralRTLIRGenL1Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 19, 2019
"""Test the generation of level 1 structural RTLIR."""

from __future__ import absolute_import, division, print_function

import pymtl
from pymtl import Bits1, Bits4, Bits32, InPort, OutPort
from pymtl.passes.BasePass import PassMetadata
from pymtl.passes.rtlir.RTLIRDataType import Vector
from pymtl.passes.rtlir.structural.StructuralRTLIRGenL1Pass import (
    StructuralRTLIRGenL1Pass,
)
from pymtl.passes.rtlir.structural.StructuralRTLIRSignalExpr import *


def test_L1_const_numbers():
  class A( pymtl.Component ):
    def construct( s ):
      s.const = [ Bits32(42) for _ in xrange(5) ]
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL1Pass() )
  ns = a._pass_structural_rtlir_gen
  assert ns.consts == [('const', Array([5], Const(Vector(32))), a.const)]

def test_L1_connection_order():
  class A( pymtl.Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.out1 = OutPort( Bits32 )
      s.out2 = OutPort( Bits32 )
      s.connect( s.in_1, s.out1 )
      s.connect( s.in_2, s.out2 )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL1Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  assert ns.connections == \
    [(CurCompAttr(comp, 'in_1'), CurCompAttr(comp, 'out1')),
     (CurCompAttr(comp, 'in_2'), CurCompAttr(comp, 'out2'))]

def test_L1_port_index():
  class A( pymtl.Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange(5) ]
      s.out = OutPort( Bits32 )
      s.connect( s.in_[2], s.out )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL1Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  assert ns.connections == \
    [(PortIndex(CurCompAttr(comp, 'in_'), 2), CurCompAttr(comp, 'out'))]

def test_L1_wire_index():
  class A( pymtl.Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange(5) ]
      s.wire = [ pymtl.Wire( Bits32 ) for _ in xrange(5) ]
      s.out = OutPort( Bits32 )
      s.connect( s.wire[2], s.out )
      for i in xrange(5):
        s.connect( s.wire[i], s.in_[i] )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL1Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  assert ns.connections[0] == \
    (WireIndex(CurCompAttr(comp, 'wire'), 2), CurCompAttr(comp, 'out'))

def test_L1_const_index():
  class A( pymtl.Component ):
    def construct( s ):
      s.const = [ 42 for _ in xrange(5) ]
      s.out = OutPort( Bits32 )
      s.connect( s.const[2], s.out )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL1Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  # The expression structure is removed and only the constant value
  # is left in this node.
  assert ns.connections == \
    [(ConstInstance(a.const[2], 42), CurCompAttr(comp, 'out'))]

def test_L1_bit_selection():
  class A( pymtl.Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      s.connect( s.in_[0], s.out )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL1Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  # PyMTL DSL converts bit selection into 1-bit part selection!
  assert ns.connections == \
    [(PartSelection(CurCompAttr(comp, 'in_'), 0, 1), CurCompAttr(comp, 'out'))]

def test_L1_part_selection():
  class A( pymtl.Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits4 )
      s.connect( s.in_[4:8], s.out )
  a = A()
  a.elaborate()
  a.apply( StructuralRTLIRGenL1Pass() )
  ns = a._pass_structural_rtlir_gen
  comp = CurComp(a, 's')
  assert ns.connections == \
    [(PartSelection(CurCompAttr(comp, 'in_'), 4, 8), CurCompAttr(comp, 'out'))]
