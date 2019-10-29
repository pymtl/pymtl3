#=========================================================================
# SVBehavioralTranslatorL3_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 28, 2019
"""Test the SystemVerilog translator implementation."""

from pymtl3.datatypes import Bits32, Bits96, bitstruct, concat
from pymtl3.dsl import Component, InPort, OutPort
from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.behavioral.SVBehavioralTranslatorL3 import (
    BehavioralRTLIRToSVVisitorL3,
)

from .SVBehavioralTranslatorL1_test import is_sverilog_reserved


def local_do_test( m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )

  visitor = BehavioralRTLIRToSVVisitorL3(is_sverilog_reserved)
  upblks = m._pass_behavioral_rtlir_gen.rtlir_upblks
  m_all_upblks = m.get_update_blocks()
  for blk in m_all_upblks:
    upblk_src = visitor.enter( blk, upblks[blk] )
    upblk_src = "\n".join( upblk_src )
    assert upblk_src == m._ref_upblk_srcs[blk.__name__]

def test_struct( do_test ):
  @bitstruct
  class B:
    foo: Bits32
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = tv[0]
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[1])
  a._test_vectors = [
    [     B(),   0 ],
    [    B(0),   0 ],
    [   B(-1),  -1 ],
    [   B(42),  42 ],
    [   B(-2),  -2 ],
    [   B(10),  10 ],
    [  B(256), 256 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = { 'upblk' : \
"""\
always_comb begin : upblk
  out = in___foo;
end\
""" }
  do_test( a )

def test_struct_const( do_test ):
  @bitstruct
  class B:
    foo: Bits32
  class A( Component ):
    def construct( s ):
      s.in_ = B()
      s.out = OutPort( Bits32 )
      s.out_b = OutPort( B )
      @s.update
      def upblk():
        s.out = s.in_.foo
        s.out_b = s.in_
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = in_.foo;
  out_b = in_;
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    pass
  def tv_out( m, tv ):
    assert m.out_b == tv[0]
    assert m.out == Bits32(tv[1])
  a._test_vectors = [
    [       B(),   0 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = { 'upblk' : \
"""\
always_comb begin : upblk
  out = 32'd42;
  out_b = 32'd42;
end\
""" }
  do_test( a )

def test_packed_array_behavioral( do_test ):
  @bitstruct
  class B:
    foo: Bits32
    bar: [ Bits32 ] * 2
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = tv[0]
  def tv_out( m, tv ):
    assert m.out == Bits96(tv[1])
  a._test_vectors = [
    [   B(),                              concat(  Bits32(0),   Bits32(0),   Bits32(0) ) ],
    [   B(0, [ Bits32(0) ,Bits32(0)  ] ), concat(  Bits32(0),   Bits32(0),   Bits32(0) ) ],
    [  B(-1, [ Bits32(-1),Bits32(-1) ] ), concat( Bits32(-1),  Bits32(-1),  Bits32(-1) ) ],
    [  B(-1, [ Bits32(42),Bits32(42) ] ), concat( Bits32(42),  Bits32(42),  Bits32(-1) ) ],
    [  B(42, [ Bits32(42),Bits32(42) ] ), concat( Bits32(42),  Bits32(42),  Bits32(42) ) ],
    [  B(42, [ Bits32(-1),Bits32(-1) ] ), concat( Bits32(-1),  Bits32(-1),  Bits32(42) ) ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = { 'upblk' : \
"""\
always_comb begin : upblk
  out = { in___bar[0], in___bar[1], in___foo };
end\
""" }
  do_test( a )

def test_nested_struct( do_test ):
  @bitstruct
  class C:
    woof: Bits32
  @bitstruct
  class B:
    foo: Bits32
    bar: [Bits32]*2
    c: C
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = tv[0]
  def tv_out( m, tv ):
    assert m.out == Bits96(tv[1])
  a._test_vectors = [
    [   B(),                                     concat(   Bits32(0), Bits32(0),   Bits32(0) ) ],
    [   B(0, [ Bits32(0) , Bits32(0)  ], C(5) ), concat(   Bits32(0), Bits32(5),   Bits32(0) ) ],
    [  B(-1, [ Bits32(-1), Bits32(-2) ], C(6) ), concat(  Bits32(-1), Bits32(6),  Bits32(-1) ) ],
    [  B(-1, [ Bits32(42), Bits32(43) ], C(7) ), concat(  Bits32(42), Bits32(7),  Bits32(-1) ) ],
    [  B(42, [ Bits32(42), Bits32(43) ], C(8) ), concat(  Bits32(42), Bits32(8),  Bits32(42) ) ],
    [  B(42, [ Bits32(-1), Bits32(-2) ], C(9) ), concat(  Bits32(-1), Bits32(9),  Bits32(42) ) ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = { 'upblk' : \
"""\
always_comb begin : upblk
  out = { in___bar[0], in___c__woof, in___foo };
end\
""" }
  do_test( a )
