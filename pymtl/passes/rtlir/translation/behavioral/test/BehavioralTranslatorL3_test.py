#=========================================================================
# BehavioralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Test the level 3 behavioral translator."""

from __future__ import absolute_import, division, print_function

from functools import reduce

import pymtl.passes.rtlir.RTLIRDataType as rdt
import pymtl.passes.rtlir.RTLIRType as rt
from pymtl import *
from pymtl.passes.rtlir.test_utility import do_test
from pymtl.passes.rtlir.translation.behavioral.BehavioralTranslatorL3 import (
    BehavioralTranslatorL3,
)
from TestBehavioralTranslator import mk_TestBehavioralTranslator


def local_do_test( m ):
  m.elaborate()
  tr = mk_TestBehavioralTranslator(BehavioralTranslatorL3)(m)
  tr.translate_behavioral( m )
  upblk_src = tr.behavioral.upblk_srcs[m]
  decl_freevars = tr.behavioral.decl_freevars[m]
  decl_tmpvars = tr.behavioral.decl_tmpvars[m]
  assert reduce(lambda r, o: r or upblk_src == o, m._ref_upblk_repr, False)
  assert reduce(lambda r, o: r or decl_freevars == o, m._ref_freevar_repr, False)
  assert reduce(lambda r, o: r or decl_tmpvars == o, m._ref_tmpvar_repr, False)

def test_tmp_wire_struct( do_test ):
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = Bits32(foo)
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        u = s.in_
        s.out = u.foo
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

def test_multi_tmp_wire_struct( do_test ):
  class C( object ):
    def __init__( s, bar=42 ):
      s.bar = Bits32(bar)
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = Bits32(foo)
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
  a._ref_upblk_repr = [
"""\
upblk_decls:
  upblk_decl: upblk1
  upblk_decl: upblk2
""",
"""\
upblk_decls:
  upblk_decl: upblk2
  upblk_decl: upblk1
""" ]
  a._ref_freevar_repr = [ "freevars:\n" ]
  a._ref_tmpvar_repr = [
"""\
tmpvars:
  tmpvar: u in upblk1 of Struct B
  tmpvar: u in upblk2 of Struct C
""",
"""\
tmpvars:
  tmpvar: u in upblk2 of Struct C
  tmpvar: u in upblk1 of Struct B
""" ]
  do_test( a )
