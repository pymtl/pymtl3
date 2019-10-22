#=========================================================================
# BehavioralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Test the level 3 behavioral translator."""

from pymtl3.datatypes import Bits32, bitstruct
from pymtl3.dsl import Component, InPort, OutPort
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.translator.behavioral.BehavioralTranslatorL3 import (
    BehavioralTranslatorL3,
)

from .TestBehavioralTranslator import mk_TestBehavioralTranslator


def local_do_test( m ):
  m.elaborate()
  tr = mk_TestBehavioralTranslator(BehavioralTranslatorL3)(m)
  tr.clear( m )
  tr.translate_behavioral( m )
  upblk_src = tr.behavioral.upblk_srcs[m]
  decl_freevars = tr.behavioral.decl_freevars[m]
  decl_tmpvars = tr.behavioral.decl_tmpvars[m]
  assert upblk_src == m._ref_upblk_repr
  assert decl_freevars == m._ref_freevar_repr
  assert decl_tmpvars == m._ref_tmpvar_repr

def test_tmp_wire_struct( do_test ):
  @bitstruct
  class B:
    foo: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        u = s.in_
        s.out = u.foo
  a = A()
  a._ref_upblk_repr = \
"""\
upblk_srcs:
  upblk_src: upblk
"""
  a._ref_freevar_repr = "freevars:\n"
  a._ref_tmpvar_repr = \
"""\
tmpvars:
  tmpvar: u in upblk of Struct B
"""
  do_test( a )

def test_multi_tmp_wire_struct( do_test ):
  @bitstruct
  class C:
    bar: Bits32
  @bitstruct
  class B:
    foo: Bits32
  class A( Component ):
    def construct( s ):
      s.in_b = InPort( B )
      s.in_c = InPort( C )
      s.out_b = OutPort( Bits32 )
      s.out_c = OutPort( Bits32 )
      @s.update
      def upblk1():
        u = s.in_b
        s.out_b = u.foo
      @s.update
      def upblk2():
        u = s.in_c
        s.out_c = u.bar
  a = A()
  a._ref_upblk_repr = \
"""\
upblk_srcs:
  upblk_src: upblk1
  upblk_src: upblk2
"""
  a._ref_freevar_repr = "freevars:\n"
  a._ref_tmpvar_repr = \
"""\
tmpvars:
  tmpvar: u in upblk1 of Struct B
  tmpvar: u in upblk2 of Struct C
"""
  do_test( a )
