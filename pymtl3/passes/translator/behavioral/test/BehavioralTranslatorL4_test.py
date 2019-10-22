#=========================================================================
# BehavioralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Test the level 4 behavioral translator."""

from pymtl3.datatypes import Bits32, bitstruct
from pymtl3.dsl import Component, InPort, Interface, OutPort
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.translator.behavioral.BehavioralTranslatorL4 import (
    BehavioralTranslatorL4,
)

from .TestBehavioralTranslator import mk_TestBehavioralTranslator


def local_do_test( m ):
  m.elaborate()
  tr = mk_TestBehavioralTranslator(BehavioralTranslatorL4)(m)
  tr.clear( m )
  tr.translate_behavioral( m )
  upblk_src = tr.behavioral.upblk_srcs[m]
  decl_freevars = tr.behavioral.decl_freevars[m]
  decl_tmpvars = tr.behavioral.decl_tmpvars[m]
  assert upblk_src == m._ref_upblk_repr
  assert decl_freevars == m._ref_freevar_repr
  assert decl_tmpvars == m._ref_tmpvar_repr

def test_tmp_ifc_port( do_test ):
  class Ifc( Interface ):
    def construct( s ):
      s.foo = InPort( Bits32 )
      s.bar = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.ifc = Ifc()
      @s.update
      def upblk():
        u = s.ifc.foo
        s.ifc.bar = u
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
  tmpvar: u in upblk of Vector32
"""
  do_test( a )

def test_tmp_ifc_port_struct( do_test ):
  @bitstruct
  class C:
    bar: Bits32
  @bitstruct
  class B:
    foo: Bits32
  class Ifc( Interface ):
    def construct( s ):
      s.foo = InPort( B )
      s.bar = OutPort( C )
  class A( Component ):
    def construct( s ):
      s.ifc = Ifc()
      @s.update
      def upblk():
        u = s.ifc.foo
        s.ifc.bar.bar = u.foo
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
