#=========================================================================
# BehavioralTranslatorL4_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Test the level 4 behavioral translator."""

from __future__ import absolute_import, division, print_function

from functools import reduce

import pymtl.passes.rtlir.RTLIRDataType as rdt
import pymtl.passes.rtlir.RTLIRType as rt
from pymtl import *
from pymtl.passes.rtlir.test_utility import do_test
from pymtl.passes.rtlir.translation.behavioral.BehavioralTranslatorL4 import (
    BehavioralTranslatorL4,
)

from .TestBehavioralTranslator import mk_TestBehavioralTranslator


def local_do_test( m ):
  m.elaborate()
  tr = mk_TestBehavioralTranslator(BehavioralTranslatorL4)(m)
  tr.translate_behavioral( m )
  upblk_src = tr.behavioral.upblk_srcs[m]
  decl_freevars = tr.behavioral.decl_freevars[m]
  decl_tmpvars = tr.behavioral.decl_tmpvars[m]
  assert reduce(lambda r, o: r or upblk_src == o, m._ref_upblk_repr, False)
  assert reduce(lambda r, o: r or decl_freevars == o, m._ref_freevar_repr, False)
  assert reduce(lambda r, o: r or decl_tmpvars == o, m._ref_tmpvar_repr, False)

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
  a._ref_upblk_repr = [
"""\
upblk_decls:
  upblk_decl: upblk
""" ]
  a._ref_freevar_repr = [ "freevars:\n" ]
  a._ref_tmpvar_repr = [
"""\
tmpvars:
  tmpvar: u in upblk of Vector32
""" ]
  do_test( a )

def test_tmp_ifc_port_struct( do_test ):
  class C( object ):
    def __init__( s, bar=42 ):
      s.bar = Bits32(bar)
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = Bits32(foo)
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
  a._ref_upblk_repr = [
"""\
upblk_decls:
  upblk_decl: upblk
""" ]
  a._ref_freevar_repr = [ "freevars:\n" ]
  a._ref_tmpvar_repr = [
"""\
tmpvars:
  tmpvar: u in upblk of Struct B
""" ]
  do_test( a )
