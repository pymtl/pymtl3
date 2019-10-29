#=========================================================================
# SVBehavioralTranslatorL5_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 28, 2019
"""Test the SystemVerilog translator implementation."""

from pymtl3.datatypes import Bits1, Bits32, concat
from pymtl3.dsl import Component, InPort, Interface, OutPort
from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.behavioral.SVBehavioralTranslatorL5 import (
    BehavioralRTLIRToSVVisitorL5,
)

from .SVBehavioralTranslatorL1_test import is_sverilog_reserved


def local_do_test( m ):
  visitor = BehavioralRTLIRToSVVisitorL5(is_sverilog_reserved)
  for comp, _all_upblks in m._ref_upblk_srcs.items():
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
  out = b__foo;
end\
""" }, a.b : { 'upblk' : \
"""\
always_comb begin : upblk
  foo = 32'd42;
end\
"""
} }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    pass
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[0])
  a._test_vectors = [
    [    42 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
  do_test( a )

def test_subcomponent_index( do_test ):
  class B( Component ):
    def construct( s ):
      s.out = OutPort( Bits32 )
  class A( Component ):
    def construct( s ):
      s.comp = [ B() for _ in range(4) ]
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.comp[2].out
  a = A()
  a.elaborate()
  a._ref_upblk_srcs = { a : { 'upblk' : \
"""\
always_comb begin : upblk
  out = comp__2__out;
end\
""" } }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    pass
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[0])
  a._test_vectors = [
    [    0 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = { a : { 'upblk' : \
"""\
always_comb begin : upblk
  out = comp__out[2];
end\
""" } }
  do_test( a )
