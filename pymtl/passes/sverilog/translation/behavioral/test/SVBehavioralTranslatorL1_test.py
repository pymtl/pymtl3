#=========================================================================
# SVBehavioralTranslatorL1_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 28, 2019
"""Test the SystemVerilog translator implementation."""

from pymtl import Component, InPort, OutPort, Bits1, Bits32, Bits64, \
                  concat, sext, zext
from pymtl.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl.passes.rtlir.test.test_utility import do_test, expected_failure
from pymtl.passes.sverilog.translation.behavioral.SVBehavioralTranslatorL1 import \
    BehavioralRTLIRToSVVisitorL1
from pymtl.passes.sverilog.errors import SVerilogTranslationError

def local_do_test( m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )

  visitor = BehavioralRTLIRToSVVisitorL1()
  upblks = m._pass_behavioral_rtlir_gen.rtlir_upblks
  m_all_upblks = m.get_update_blocks()
  for blk in m_all_upblks:
    upblk_src = visitor.enter( blk, upblks[blk] )
    upblk_src = "\n".join( upblk_src )
    assert upblk_src == m._ref_upblk_srcs[blk.__name__]

def test_comb_assign( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = in_;
end\
""" }
  do_test( a )

def test_seq_assign( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update_on_edge
      def upblk():
        s.out = s.in_
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_ff @(posedge clk) begin : upblk
  out <= in_;
end\
""" }
  do_test( a )

def test_concat( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = concat( s.in_1, s.in_2 )
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = { in_1, in_2 };
end\
""" }
  do_test( a )

def test_concat_constants( do_test ):
  class A( Component ):
    def construct( s ):
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = concat( Bits32(42), Bits32(0) )
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = { 32'd42, 32'd0 };
end\
""" }
  do_test( a )

def test_concat_mixed( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = concat( s.in_, Bits32(0) )
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = { in_, 32'd0 };
end\
""" }
  do_test( a )

def test_sext( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = sext( s.in_, 64 )
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = { { 32 { in_[31] } }, in_ };
end\
""" }
  do_test( a )

def test_zext( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = zext( s.in_, 64 )
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = { { 32 { 1'b0 } }, in_ };
end\
""" }
  do_test( a )

def test_sub_component_attr( do_test ):
  class B( Component ):
    def construct( s ):
      s.out_b = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out_b = Bit32(0)
  class A( Component ):
    def construct( s ):
      s.b = B()
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = zext( s.b.out_b, 64 )
  with expected_failure( SVerilogTranslationError, "sub-components" ):
    do_test( A() )

def test_freevar( do_test ):
  class A( Component ):
    def construct( s ):
      STATE_IDLE = Bits32(42)
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = concat( s.in_, STATE_IDLE )
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = { in_, _fvar_STATE_IDLE };
end\
""" }
  do_test( a )

def test_unpacked_signal_index( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange(2) ]
      s.out = OutPort( Bits64 )
      @s.update
      def upblk():
        s.out = concat( s.in_[0], s.in_[1] )
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = { in_[0], in_[1] };
end\
""" }
  do_test( a )

def test_bit_selection( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = s.in_[1]
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = in_[1];
end\
""" }
  do_test( a )

def test_part_selection( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits64 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.in_[4:36]
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = in_[35:4];
end\
""" }
  do_test( a )
