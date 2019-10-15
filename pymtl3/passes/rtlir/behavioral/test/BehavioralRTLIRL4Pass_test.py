#=========================================================================
# BehavioralRTLIRL4Pass_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : Feb 2, 2019
"""Test the level 4 behavioral RTLIR passes.

The L4 generation, L4 type check, and visualization passes are invoked. The
generation pass results are verified against a reference AST.
"""

import pytest

from pymtl3.datatypes import Bits32
from pymtl3.dsl import Component, Interface, OutPort
from pymtl3.dsl.errors import VarNotDeclaredError
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIR import *
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRGenL4Pass import (
    BehavioralRTLIRGenL4Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRTypeCheckL4Pass import (
    BehavioralRTLIRTypeCheckL4Pass,
)
from pymtl3.passes.rtlir.behavioral.BehavioralRTLIRVisualizationPass import (
    BehavioralRTLIRVisualizationPass,
)
from pymtl3.passes.rtlir.errors import PyMTLSyntaxError, PyMTLTypeError
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure


def local_do_test( m ):
  """Check if generated behavioral RTLIR is the same as reference."""
  m.elaborate()
  m.apply( BehavioralRTLIRGenL4Pass() )
  m.apply( BehavioralRTLIRTypeCheckL4Pass() )
  m.apply( BehavioralRTLIRVisualizationPass() )

  try:
    ref = m._rtlir_test_ref
    for blk in m.get_update_blocks():
      upblk = m._pass_behavioral_rtlir_gen.rtlir_upblks[ blk ]
      assert upblk == ref[ blk.__name__ ]
  except AttributeError:
    pass

#-------------------------------------------------------------------------
# Correct test cases
#-------------------------------------------------------------------------

def test_L4_interface_attr( do_test ):
  class Ifc( Interface ):
    def construct( s ):
      s.foo = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.in_ = Ifc()
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_.foo
  a = A()
  a._rtlir_test_ref = { 'upblk' : CombUpblk( 'upblk', [ Assign(
      Attribute( Base( a ), 'out' ), Attribute(
        Attribute( Base( a ), 'in_' ), 'foo' ), True ) ] ) }
  do_test( a )

def test_L4_interface_array_index( do_test ):
  class Ifc( Interface ):
    def construct( s ):
      s.foo = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.in_ = [ Ifc() for _ in range(4) ]
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_[2].foo
  a = A()
  a._rtlir_test_ref = { 'upblk' : CombUpblk( 'upblk', [ Assign(
      Attribute( Base( a ), 'out' ), Attribute( Index(
        Attribute( Base( a ), 'in_' ), Number(2) ), 'foo' ), True ) ] ) }
  do_test( a )

#-------------------------------------------------------------------------
# PyMTL type errors
#-------------------------------------------------------------------------

def test_L4_interface_no_field( do_test ):
  class Ifc( Interface ):
    def construct( s ):
      s.foo = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.in_ = Ifc()
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_.bar
  with expected_failure( VarNotDeclaredError, 's.in_ does not have field "bar"' ):
    do_test( A() )
