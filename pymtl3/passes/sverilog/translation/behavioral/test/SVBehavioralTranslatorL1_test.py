#=========================================================================
# SVBehavioralTranslatorL1_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 28, 2019
"""Test the SystemVerilog translator implementation."""

from pymtl3.datatypes import Bits1, Bits32, Bits64, concat, sext, zext
from pymtl3.dsl import Component, InPort, OutPort
from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl3.passes.rtlir.util.test_utility import do_test, expected_failure
from pymtl3.passes.sverilog.errors import SVerilogTranslationError
from pymtl3.passes.sverilog.translation.behavioral.SVBehavioralTranslatorL1 import (
    BehavioralRTLIRToSVVisitorL1,
)
from pymtl3.passes.sverilog.translation.SVTranslator import sverilog_reserved


def is_sverilog_reserved( name ):
  return name in sverilog_reserved

def local_do_test( m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )

  visitor = BehavioralRTLIRToSVVisitorL1(is_sverilog_reserved)
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = Bits32(tv[0])
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[1])
  a._test_vectors = [
    [    0,   0 ],
    [   42,   42 ],
    [   24,   24 ],
    [   -2,   -2 ],
    [   -1,   -1 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
  do_test( a )

def test_seq_assign( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update_ff
      def upblk():
        s.out <<= s.in_
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_ff @(posedge clk) begin : upblk
  out <= in_;
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = Bits32(tv[0])
  def tv_out( m, tv ):
    if tv[1] != '*':
      assert m.out == Bits32(tv[1])
  a._test_vectors = [
    [    0,   '*' ],
    [   42,    0 ],
    [   24,    42 ],
    [   -2,    24 ],
    [   -1,    -2 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_1 = Bits32(tv[0])
    m.in_2 = Bits32(tv[1])
  def tv_out( m, tv ):
    assert m.out == Bits64(tv[2])
  a._test_vectors = [
    [    0,    0,     concat(    Bits32(0),    Bits32(0) ) ],
    [   42,    0,     concat(   Bits32(42),    Bits32(0) ) ],
    [   42,   42,     concat(   Bits32(42),    Bits32(42) ) ],
    [   -1,   42,     concat(   Bits32(-1),    Bits32(42) ) ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    pass
  def tv_out( m, tv ):
    assert m.out == Bits64(tv[0])
  a._test_vectors = [
    [    concat(    Bits32(42),    Bits32(0) ) ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = Bits32(tv[0])
  def tv_out( m, tv ):
    assert m.out == Bits64(tv[1])
  a._test_vectors = [
    [  42,  concat(    Bits32(42),    Bits32(0) ) ],
    [  -1,  concat(    Bits32(-1),    Bits32(0) ) ],
    [  -2,  concat(    Bits32(-2),    Bits32(0) ) ],
    [   2,  concat(     Bits32(2),    Bits32(0) ) ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = Bits32(tv[0])
  def tv_out( m, tv ):
    assert m.out == Bits64(tv[0])
  a._test_vectors = [
    [  42,   sext(    Bits32(42),    64 ) ],
    [  -2,   sext(    Bits32(-2),    64 ) ],
    [  -1,   sext(    Bits32(-1),    64 ) ],
    [   2,   sext(     Bits32(2),    64 ) ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = Bits32(tv[0])
  def tv_out( m, tv ):
    assert m.out == Bits64(tv[1])
  a._test_vectors = [
    [  42,  zext(    Bits32(42),    64 ) ],
    [  -1,  zext(    Bits32(-1),    64 ) ],
    [  -2,  zext(    Bits32(-2),    64 ) ],
    [   2,  zext(     Bits32(2),    64 ) ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
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
  out = { in_, __const__STATE_IDLE };
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = Bits32(tv[0])
  def tv_out( m, tv ):
    assert m.out == Bits64(tv[1])
  a._test_vectors = [
    [  42,  concat(    Bits32(42),    Bits32(42) ) ],
    [  -1,  concat(    Bits32(-1),    Bits32(42) ) ],
    [  -2,  concat(    Bits32(-2),    Bits32(42) ) ],
    [   2,  concat(     Bits32(2),    Bits32(42) ) ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = { 'upblk' : \
"""\
always_comb begin : upblk
  out = { in_, 32'd42 };
end\
"""
}
  do_test( a )

def test_unpacked_signal_index( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(2) ]
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_[0] = Bits32(tv[0])
    m.in_[1] = Bits32(tv[1])
  def tv_out( m, tv ):
    assert m.out == Bits64(tv[2])
  a._test_vectors = [
    [  42,   2,  concat(    Bits32(42),     Bits32(2) ) ],
    [  -1,  42,  concat(    Bits32(-1),    Bits32(42) ) ],
    [  -2,  -1,  concat(    Bits32(-2),    Bits32(-1) ) ],
    [   2,  -2,  concat(     Bits32(2),    Bits32(-2) ) ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = Bits32(tv[0])
  def tv_out( m, tv ):
    assert m.out == Bits1(tv[1])
  a._test_vectors = [
    [   0,   0 ],
    [  -1,   1 ],
    [  -2,   1 ],
    [   2,   1 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
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
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_ = Bits64(tv[0])
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[1])
  a._test_vectors = [
    [   -1,   -1 ],
    [   -2,   -1 ],
    [   -4,   -1 ],
    [   -8,   -1 ],
    [  -16,   -1 ],
    [  -32,   -2 ],
    [  -64,   -4 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
  do_test( a )

def test_sverilog_reserved_keyword( do_test ):
  class A( Component ):
    def construct( s ):
      s.buf = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        s.out = s.buf
  with expected_failure( SVerilogTranslationError, "reserved keyword" ):
    do_test( A() )
