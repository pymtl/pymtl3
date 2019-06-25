#=========================================================================
# BehavioralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 20, 2019
"""Test the level 2 behavioral translator."""

from pymtl3.datatypes import Bits16, Bits32
from pymtl3.dsl import Component, InPort, OutPort
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.translator.behavioral.BehavioralTranslatorL2 import (
    BehavioralTranslatorL2,
)

from .TestBehavioralTranslator import mk_TestBehavioralTranslator


def local_do_test( m ):
  m.elaborate()
  tr = mk_TestBehavioralTranslator(BehavioralTranslatorL2)(m)
  tr.clear( m )
  tr.translate_behavioral( m )
  upblk_src = tr.behavioral.upblk_srcs[m]
  decl_freevars = tr.behavioral.decl_freevars[m]
  decl_tmpvars = tr.behavioral.decl_tmpvars[m]
  assert upblk_src == m._ref_upblk_repr
  assert decl_freevars == m._ref_freevar_repr
  assert decl_tmpvars == m._ref_tmpvar_repr

def test_tmp_wire( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        u = s.in_ + Bits32(42)
        s.out = u
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

def test_tmpvar_alias( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @s.update
      def upblk1():
        u = s.in_ + Bits32(42)
        s.out[0] = u
      @s.update
      def upblk2():
        u = s.in_ + Bits32(42)
        s.out[1] = u
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
  tmpvar: u in upblk1 of Vector32
  tmpvar: u in upblk2 of Vector32
"""
  do_test( a )

def test_multi_tmpvar( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @s.update
      def upblk1():
        u = s.in_ + Bits32(42)
        v = s.in_ + Bits32(40)
        s.out[0] = u
        s.out[1] = u
  a = A()
  a._ref_upblk_repr = \
"""\
upblk_srcs:
  upblk_src: upblk1
"""
  a._ref_freevar_repr = "freevars:\n"
  a._ref_tmpvar_repr = \
"""\
tmpvars:
  tmpvar: u in upblk1 of Vector32
  tmpvar: v in upblk1 of Vector32
"""
  do_test( a )

def test_freevar_to_tmpvar( do_test ):
  class A( Component ):
    def construct( s ):
      STATE_IDLE = Bits32(0)
      s.out = OutPort( Bits32 )
      @s.update
      def upblk1():
        u = STATE_IDLE
        s.out = u
  a = A()
  a._ref_upblk_repr = \
"""\
upblk_srcs:
  upblk_src: upblk1
"""
  a._ref_freevar_repr = \
"""\
freevars:
  freevar: STATE_IDLE
"""
  a._ref_tmpvar_repr = \
"""\
tmpvars:
  tmpvar: u in upblk1 of Vector32
"""
  do_test( a )

def test_Bits_to_tmpvar( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits16 )
      @s.update
      def upblk1():
        u = Bits16(0)
        s.out = u
  a = A()
  a._ref_upblk_repr = \
"""\
upblk_srcs:
  upblk_src: upblk1
"""
  a._ref_freevar_repr = "freevars:\n"
  a._ref_tmpvar_repr = \
"""\
tmpvars:
  tmpvar: u in upblk1 of Vector16
"""
  do_test( a )

def test_py_int_to_tmpvar( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      @s.update
      def upblk1():
        u = 1
        s.out = u
  a = A()
  a._ref_upblk_repr = \
"""\
upblk_srcs:
  upblk_src: upblk1
"""
  a._ref_freevar_repr = "freevars:\n"
  a._ref_tmpvar_repr = \
"""\
tmpvars:
  tmpvar: u in upblk1 of Vector32
"""
  do_test( a )
