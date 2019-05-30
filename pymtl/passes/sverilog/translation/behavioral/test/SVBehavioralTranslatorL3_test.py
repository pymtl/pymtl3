#=========================================================================
# SVBehavioralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 28, 2019
"""Test the SystemVerilog translator implementation."""

from pymtl import Component, InPort, OutPort, Bits32, Bits96, concat
from pymtl.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl.passes.rtlir.test.test_utility import do_test
from pymtl.passes.sverilog.translation.behavioral.SVBehavioralTranslatorL3 import \
    BehavioralRTLIRToSVVisitorL3

def local_do_test( m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )

  visitor = BehavioralRTLIRToSVVisitorL3()
  upblks = m._pass_behavioral_rtlir_gen.rtlir_upblks
  m_all_upblks = m.get_update_blocks()
  for blk in m_all_upblks:
    upblk_src = visitor.enter( blk, upblks[blk] )
    upblk_src = "\n".join( upblk_src )
    assert upblk_src == m._ref_upblk_srcs[blk.__name__]

def test_struct( do_test ):
  class B( object ):
    def __init__( s, foo=42 ):
      s.foo = Bits32(42)
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_.foo
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = in_.foo;
end\
""" }
  do_test( a )

def test_packed_array( do_test ):
  class B( object ):
    def __init__( s, foo=42, bar=1 ):
      s.foo = Bits32(foo)
      s.bar = [ Bits32(bar) for _ in xrange(2) ]
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits96 )
      @s.update
      def upblk():
        s.out = concat( s.in_.bar[0], s.in_.bar[1], s.in_.foo )
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = { in_.bar[0], in_.bar[1], in_.foo };
end\
""" }
  do_test( a )

def test_nested_struct( do_test ):
  class C( object ):
    def __init__( s, woof=2 ):
      s.woof = Bits32(woof)
  class B( object ):
    def __init__( s, foo=42, bar=1 ):
      s.foo = Bits32(foo)
      s.bar = [ Bits32(bar) for _ in xrange(2) ]
      s.c = C()
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( B )
      s.out = OutPort( Bits96 )
      @s.update
      def upblk():
        s.out = concat( s.in_.bar[0], s.in_.c.woof, s.in_.foo )
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = { in_.bar[0], in_.c.woof, in_.foo };
end\
""" }
  do_test( a )
