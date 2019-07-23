#=========================================================================
# RTLIRTranslator_L1_cases_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 23, 2019
"""Test the RTLIR transaltor."""

from pymtl3.datatypes import Bits1, Bits32
from pymtl3.dsl import Component, InPort, OutPort, connect
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure

from ..behavioral.test.BehavioralTranslatorL1_test import *
from ..errors import RTLIRTranslationError
from ..structural.test.StructuralTranslatorL1_test import *
from .TestRTLIRTranslator import TestRTLIRTranslator


def local_do_test( m ):
  if not m._dsl.constructed:
    m.elaborate()
  tr = TestRTLIRTranslator(m)
  tr.translate( m )
  src = tr.hierarchy.src
  try:
    assert src == m._ref_src
  except AttributeError:
    pass

def test_bit_sel_over_bit_sel( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      connect( s.out, s.in_[1][0] )
  with expected_failure( RTLIRTranslationError, "over bit/part selection" ):
    do_test( A() )

def test_bit_sel_over_part_sel( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      connect( s.out, s.in_[0:4][0] )
  with expected_failure( RTLIRTranslationError, "over bit/part selection" ):
    do_test( A() )

def test_part_sel_over_bit_sel( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      connect( s.out, s.in_[1][0:1] )
  with expected_failure( RTLIRTranslationError, "over bit/part selection" ):
    do_test( A() )

def test_part_sel_over_part_sel( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      connect( s.out, s.in_[0:4][0:1] )
  with expected_failure( RTLIRTranslationError, "over bit/part selection" ):
    do_test( A() )
