#=========================================================================
# SVBehavioralTranslatorL5_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 28, 2019
"""Test the SystemVerilog translator implementation."""

from __future__ import absolute_import, division, print_function

from pymtl import Bits1, Bits32, Component, InPort, Interface, OutPort, concat
from pymtl.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl.passes.rtlir.test.test_utility import do_test
from pymtl.passes.sverilog.translation.behavioral.SVBehavioralTranslatorL5 import (
    BehavioralRTLIRToSVVisitorL5,
)


def local_do_test( m ):
  visitor = BehavioralRTLIRToSVVisitorL5()
  for comp, _all_upblks in m._ref_upblk_srcs.iteritems():
    comp.apply( BehavioralRTLIRGenPass() )
    comp.apply( BehavioralRTLIRTypeCheckPass() )
    upblks = comp._pass_behavioral_rtlir_gen.rtlir_upblks
    m_all_upblks = comp.get_update_blocks()
    for blk in m_all_upblks:
      upblk_src = visitor.enter( blk, upblks[blk] )
      upblk_src = "\n".join( upblk_src )
      assert upblk_src == _all_upblks[blk.__name__]

def test_subcomponent( do_test ):
  class B( Component ):
    def construct( s ):
      s.foo = OutPort( Bits32 )
      @s.update
      def upblk():
        s.foo = Bits32(42)
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
      s.b = B()
      @s.update
      def upblk():
        s.out = s.b.foo
  a = A()
  a.elaborate()
  a._ref_upblk_srcs = { a : { 'upblk' : \
"""\
always_comb begin : upblk
  out = b$foo;
end\
""" }, a.b : { 'upblk' : \
"""\
always_comb begin : upblk
  foo = 32'd42;
end\
"""
} }
  do_test( a )

def test_subcomponent_index( do_test ):
  class B( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.comp = [ B() for _ in xrange(4) ]
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.comp[2].out
  a = A()
  a.elaborate()
  a._ref_upblk_srcs = { a : { 'upblk' : \
"""\
always_comb begin : upblk
  out = comp_$2$out;
end\
""" } }
  do_test( a )
