#=========================================================================
# SVBehavioralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 28, 2019
"""Test the SystemVerilog translator implementation."""

from pymtl3.datatypes import Bits1, Bits32, reduce_and, reduce_or, reduce_xor
from pymtl3.dsl import Component, InPort, OutPort
from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.behavioral.SVBehavioralTranslatorL2 import (
    BehavioralRTLIRToSVVisitorL2,
)

from .SVBehavioralTranslatorL1_test import is_sverilog_reserved


def local_do_test( m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )

  visitor = BehavioralRTLIRToSVVisitorL2(is_sverilog_reserved)
  upblks = m._pass_behavioral_rtlir_gen.rtlir_upblks
  m_all_upblks = m.get_update_blocks()
  for blk in m_all_upblks:
    upblk_src = visitor.enter( blk, upblks[blk] )
    upblk_src = "\n".join( upblk_src )
    assert upblk_src == m._ref_upblk_srcs[blk.__name__]

def test_reduce( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.in_3 = InPort( Bits32 )
      s.out = OutPort( Bits1 )
      @s.update
      def upblk():
        s.out = reduce_and( s.in_1 ) & reduce_or( s.in_2 ) | reduce_xor( s.in_3 )
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  out = ( ( & in_1 ) & ( | in_2 ) ) | ( ^ in_3 );
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_1 = Bits32(tv[0])
    m.in_2 = Bits32(tv[1])
    m.in_3 = Bits32(tv[2])
  def tv_out( m, tv ):
    assert m.out == Bits1(tv[3])
  a._test_vectors = [
    [  0,   1,    2,  1   ],
    [ -1,   1,   -1,  1   ],
    [  9,   8,    7,  1   ],
    [  9,   8,    0,  0   ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
  do_test( a )

def test_if( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        if Bits1(1):
          s.out = s.in_1
        else:
          s.out = s.in_2
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  if ( 1'd1 ) begin
    out = in_1;
  end
  else
    out = in_2;
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_1 = Bits32(tv[0])
    m.in_2 = Bits32(tv[1])
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[2])
  a._test_vectors = [
    [    0,    -1,   0 ],
    [   42,     0,  42 ],
    [   24,    42,  24 ],
    [   -2,    24,  -2 ],
    [   -1,    -2,  -1 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
  do_test( a )

def test_if_dangling_else_inner( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        if Bits1(1):
          if Bits1(0):
            s.out = s.in_1
          else:
            s.out = s.in_2
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  if ( 1'd1 ) begin
    if ( 1'd0 ) begin
      out = in_1;
    end
    else
      out = in_2;
  end
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_1 = Bits32(tv[0])
    m.in_2 = Bits32(tv[1])
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[2])
  a._test_vectors = [
    [    0,    -1,  -1 ],
    [   42,     0,   0 ],
    [   24,    42,  42 ],
    [   -2,    24,  24 ],
    [   -1,    -2,  -2 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
  do_test( a )

def test_if_dangling_else_outter( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        if Bits1(1):
          if Bits1(0):
            s.out = s.in_1
        else:
          s.out = s.in_2
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  if ( 1'd1 ) begin
    if ( 1'd0 ) begin
      out = in_1;
    end
  end
  else
    out = in_2;
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_1 = Bits32(tv[0])
    m.in_2 = Bits32(tv[1])
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[2])
  a._test_vectors = [
    [    0,    -1,   0 ],
    [   42,     0,   0 ],
    [   24,    42,   0 ],
    [   -2,    24,   0 ],
    [   -1,    -2,   0 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
  do_test( a )

def test_if_branches( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.in_3 = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        if Bits1(1):
          s.out = s.in_1
        elif Bits1(0):
          s.out = s.in_2
        else:
          s.out = s.in_3
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  if ( 1'd1 ) begin
    out = in_1;
  end
  else if ( 1'd0 ) begin
    out = in_2;
  end
  else
    out = in_3;
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_1 = Bits32(tv[0])
    m.in_2 = Bits32(tv[1])
    m.in_3 = Bits32(tv[2])
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[3])
  a._test_vectors = [
    [    0,    -1,   0,  0 ],
    [   42,     0,  42, 42 ],
    [   24,    42,  24, 24 ],
    [   -2,    24,  -2, -2 ],
    [   -1,    -2,  -1, -1 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
  do_test( a )

def test_nested_if( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_1 = InPort( Bits32 )
      s.in_2 = InPort( Bits32 )
      s.in_3 = InPort( Bits32 )
      s.out = OutPort( Bits32 )
      @s.update
      def upblk():
        if Bits1(1):
          if Bits1(0):
            s.out = s.in_1
          else:
            s.out = s.in_2
        elif Bits1(0):
          if Bits1(1):
            s.out = s.in_2
          else:
            s.out = s.in_3
        else:
          if Bits1(1):
            s.out = s.in_3
          else:
            s.out = s.in_1
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  if ( 1'd1 ) begin
    if ( 1'd0 ) begin
      out = in_1;
    end
    else
      out = in_2;
  end
  else if ( 1'd0 ) begin
    if ( 1'd1 ) begin
      out = in_2;
    end
    else
      out = in_3;
  end
  else if ( 1'd1 ) begin
    out = in_3;
  end
  else
    out = in_1;
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_1 = Bits32(tv[0])
    m.in_2 = Bits32(tv[1])
    m.in_3 = Bits32(tv[2])
  def tv_out( m, tv ):
    assert m.out == Bits32(tv[3])
  a._test_vectors = [
    [    0,    -1,   0,  -1 ],
    [   42,     0,  42,   0 ],
    [   24,    42,  24,  42 ],
    [   -2,    24,  -2,  24 ],
    [   -1,    -2,  -1,  -2 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = a._ref_upblk_srcs
  do_test( a )

def test_for_range_upper( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(2) ]
      s.out = [ OutPort( Bits32 ) for _ in range(2) ]
      @s.update
      def upblk():
        for i in range(2):
          s.out[i] = s.in_[i]
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  for ( int i = 0; i < 2; i += 1 )
    out[i] = in_[i];
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_[0] = Bits32(tv[0])
    m.in_[1] = Bits32(tv[1])
  def tv_out( m, tv ):
    assert m.out[0] == Bits32(tv[2])
    assert m.out[1] == Bits32(tv[3])
  a._test_vectors = [
    [    0,    -1,   0,  -1 ],
    [   42,     0,  42,   0 ],
    [   24,    42,  24,  42 ],
    [   -2,    24,  -2,  24 ],
    [   -1,    -2,  -1,  -2 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = { 'upblk' : \
"""\
integer __loopvar__upblk_i;

always_comb begin : upblk
  for ( __loopvar__upblk_i = 0; __loopvar__upblk_i < 2; __loopvar__upblk_i = __loopvar__upblk_i + 1 )
    out[__loopvar__upblk_i] = in_[__loopvar__upblk_i];
end\
""" }
  do_test( a )

def test_for_range_lower_upper( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(2) ]
      s.out = [ OutPort( Bits32 ) for _ in range(2) ]
      @s.update
      def upblk():
        for i in range(1, 2):
          s.out[i] = s.in_[i]
        s.out[0] = s.in_[0]
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  for ( int i = 1; i < 2; i += 1 )
    out[i] = in_[i];
  out[0] = in_[0];
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_[0] = Bits32(tv[0])
    m.in_[1] = Bits32(tv[1])
  def tv_out( m, tv ):
    assert m.out[0] == Bits32(tv[2])
    assert m.out[1] == Bits32(tv[3])
  a._test_vectors = [
    [    0,    -1,   0,  -1 ],
    [   42,     0,  42,   0 ],
    [   24,    42,  24,  42 ],
    [   -2,    24,  -2,  24 ],
    [   -1,    -2,  -1,  -2 ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = { 'upblk' : \
"""\
integer __loopvar__upblk_i;

always_comb begin : upblk
  for ( __loopvar__upblk_i = 1; __loopvar__upblk_i < 2; __loopvar__upblk_i = __loopvar__upblk_i + 1 )
    out[__loopvar__upblk_i] = in_[__loopvar__upblk_i];
  out[0] = in_[0];
end\
""" }
  do_test( a )

def test_for_range_lower_upper_step( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @s.update
      def upblk():
        for i in range(0, 5, 2):
          s.out[i] = s.in_[i]
        for i in range(1, 5, 2):
          s.out[i] = s.in_[i]
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  for ( int i = 0; i < 5; i += 2 )
    out[i] = in_[i];
  for ( int i = 1; i < 5; i += 2 )
    out[i] = in_[i];
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_[0] = Bits32(tv[0])
    m.in_[1] = Bits32(tv[1])
    m.in_[2] = Bits32(tv[2])
    m.in_[3] = Bits32(tv[3])
    m.in_[4] = Bits32(tv[4])
  def tv_out( m, tv ):
    assert m.out[0] == Bits32(tv[5])
    assert m.out[1] == Bits32(tv[6])
    assert m.out[2] == Bits32(tv[7])
    assert m.out[3] == Bits32(tv[8])
    assert m.out[4] == Bits32(tv[9])
  a._test_vectors = [
    [    0,    -1,   0,  -1,   0,    0,    -1,   0,  -1,   0, ],
    [   42,     0,  42,   0,  42,   42,     0,  42,   0,  42, ],
    [   24,    42,  24,  42,  24,   24,    42,  24,  42,  24, ],
    [   -2,    24,  -2,  24,  -2,   -2,    24,  -2,  24,  -2, ],
    [   -1,    -2,  -1,  -2,  -1,   -1,    -2,  -1,  -2,  -1, ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = { 'upblk' : \
"""\
integer __loopvar__upblk_i;

always_comb begin : upblk
  for ( __loopvar__upblk_i = 0; __loopvar__upblk_i < 5; __loopvar__upblk_i = __loopvar__upblk_i + 2 )
    out[__loopvar__upblk_i] = in_[__loopvar__upblk_i];
  for ( __loopvar__upblk_i = 1; __loopvar__upblk_i < 5; __loopvar__upblk_i = __loopvar__upblk_i + 2 )
    out[__loopvar__upblk_i] = in_[__loopvar__upblk_i];
end\
""" }
  do_test( a )

def test_if_exp_for( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @s.update
      def upblk():
        for i in range(5):
          s.out[i] = s.in_[i] if i == 1 else s.in_[0]
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  for ( int i = 0; i < 5; i += 1 )
    out[i] = ( i == 1 ) ? in_[i] : in_[0];
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_[0] = Bits32(tv[0])
    m.in_[1] = Bits32(tv[1])
    m.in_[2] = Bits32(tv[2])
    m.in_[3] = Bits32(tv[3])
    m.in_[4] = Bits32(tv[4])
  def tv_out( m, tv ):
    assert m.out[0] == Bits32(tv[5])
    assert m.out[1] == Bits32(tv[6])
    assert m.out[2] == Bits32(tv[7])
    assert m.out[3] == Bits32(tv[8])
    assert m.out[4] == Bits32(tv[9])
  a._test_vectors = [
    [    0,    -1,   0,  -1,   0,    0,    -1,   0,   0,   0, ],
    [   42,     0,  42,   0,  42,   42,     0,  42,  42,  42, ],
    [   24,    42,  24,  42,  24,   24,    42,  24,  24,  24, ],
    [   -2,    24,  -2,  24,  -2,   -2,    24,  -2,  -2,  -2, ],
    [   -1,    -2,  -1,  -2,  -1,   -1,    -2,  -1,  -1,  -1, ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = { 'upblk' : \
"""\
integer __loopvar__upblk_i;

always_comb begin : upblk
  for ( __loopvar__upblk_i = 0; __loopvar__upblk_i < 5; __loopvar__upblk_i = __loopvar__upblk_i + 1 )
    out[__loopvar__upblk_i] = ( __loopvar__upblk_i == 1 ) ? in_[__loopvar__upblk_i] : in_[0];
end\
""" }
  do_test( a )

def test_if_exp_unary_op( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @s.update
      def upblk():
        for i in range(5):
          s.out[i] = (~s.in_[i]) if i == 1 else s.in_[0]
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  for ( int i = 0; i < 5; i += 1 )
    out[i] = ( i == 1 ) ? ~in_[i] : in_[0];
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_[0] = Bits32(tv[0])
    m.in_[1] = Bits32(tv[1])
    m.in_[2] = Bits32(tv[2])
    m.in_[3] = Bits32(tv[3])
    m.in_[4] = Bits32(tv[4])
  def tv_out( m, tv ):
    assert m.out[0] == Bits32(tv[5])
    assert m.out[1] == Bits32(tv[6])
    assert m.out[2] == Bits32(tv[7])
    assert m.out[3] == Bits32(tv[8])
    assert m.out[4] == Bits32(tv[9])
  a._test_vectors = [
    [    0,    -1,   0,  -1,   0,    0,    ~-1,   0,   0,   0, ],
    [   42,     0,  42,   0,  42,   42,     ~0,  42,  42,  42, ],
    [   24,    42,  24,  42,  24,   24,    ~42,  24,  24,  24, ],
    [   -2,    24,  -2,  24,  -2,   -2,    ~24,  -2,  -2,  -2, ],
    [   -1,    -2,  -1,  -2,  -1,   -1,    ~-2,  -1,  -1,  -1, ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = { 'upblk' : \
"""\
integer __loopvar__upblk_i;

always_comb begin : upblk
  for ( __loopvar__upblk_i = 0; __loopvar__upblk_i < 5; __loopvar__upblk_i = __loopvar__upblk_i + 1 )
    out[__loopvar__upblk_i] = ( __loopvar__upblk_i == 1 ) ? ~in_[__loopvar__upblk_i] : in_[0];
end\
""" }
  do_test( a )

def test_if_bool_op( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @s.update
      def upblk():
        for i in range(5):
          if ( s.in_[i] != Bits32(0) ) and ( ( s.in_[i+1] != Bits32(0) ) if i<4 else ( s.in_[4] != Bits32(0) )):
            s.out[i] = s.in_[i]
          else:
            s.out[i] = Bits32(0)
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  for ( int i = 0; i < 5; i += 1 )
    if ( ( in_[i] != 32'd0 ) && ( ( i < 4 ) ? in_[i + 1] != 32'd0 : in_[4] != 32'd0 ) ) begin
      out[i] = in_[i];
    end
    else
      out[i] = 32'd0;
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_[0] = Bits32(tv[0])
    m.in_[1] = Bits32(tv[1])
    m.in_[2] = Bits32(tv[2])
    m.in_[3] = Bits32(tv[3])
    m.in_[4] = Bits32(tv[4])
  def tv_out( m, tv ):
    assert m.out[0] == Bits32(tv[5])
    assert m.out[1] == Bits32(tv[6])
    assert m.out[2] == Bits32(tv[7])
    assert m.out[3] == Bits32(tv[8])
    assert m.out[4] == Bits32(tv[9])
  a._test_vectors = [
    [    0,    -1,   0,  -1,   0,     0,     0,    0,    0,    0, ],
    [   42,     0,  42,   0,  42,     0,     0,    0,    0,   42, ],
    [   24,    42,  24,  42,  24,    24,    42,   24,   42,   24, ],
    [   -2,    24,  -2,  24,  -2,    -2,    24,   -2,   24,   -2, ],
    [   -1,    -2,  -1,  -2,  -1,    -1,    -2,   -1,   -2,   -1, ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = { 'upblk' : \
"""\
integer __loopvar__upblk_i;

always_comb begin : upblk
  for ( __loopvar__upblk_i = 0; __loopvar__upblk_i < 5; __loopvar__upblk_i = __loopvar__upblk_i + 1 )
    if ( ( in_[__loopvar__upblk_i] != 32'd0 ) && ( ( __loopvar__upblk_i < 4 ) ? in_[__loopvar__upblk_i + 1] != 32'd0 : in_[4] != 32'd0 ) ) begin
      out[__loopvar__upblk_i] = in_[__loopvar__upblk_i];
    end
    else
      out[__loopvar__upblk_i] = 32'd0;
end\
""" }
  do_test( a )

def test_tmpvar( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in range(5) ]
      s.out = [ OutPort( Bits32 ) for _ in range(5) ]
      @s.update
      def upblk():
        for i in range(5):
          if ( s.in_[i]  != Bits32(0) ) and ( ( s.in_[i+1] != Bits32(0) ) if i<4 else ( s.in_[4] != Bits32(0) ) ):
            tmpvar = s.in_[i]
          else:
            tmpvar = Bits32(0)
          s.out[i] = tmpvar
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  for ( int i = 0; i < 5; i += 1 ) begin
    if ( ( in_[i] != 32'd0 ) && ( ( i < 4 ) ? in_[i + 1] != 32'd0 : in_[4] != 32'd0 ) ) begin
      __tmpvar__upblk_tmpvar = in_[i];
    end
    else
      __tmpvar__upblk_tmpvar = 32'd0;
    out[i] = __tmpvar__upblk_tmpvar;
  end
end\
""" }
  # TestVectorSimulator properties
  def tv_in( m, tv ):
    m.in_[0] = Bits32(tv[0])
    m.in_[1] = Bits32(tv[1])
    m.in_[2] = Bits32(tv[2])
    m.in_[3] = Bits32(tv[3])
    m.in_[4] = Bits32(tv[4])
  def tv_out( m, tv ):
    assert m.out[0] == Bits32(tv[5])
    assert m.out[1] == Bits32(tv[6])
    assert m.out[2] == Bits32(tv[7])
    assert m.out[3] == Bits32(tv[8])
    assert m.out[4] == Bits32(tv[9])
  a._test_vectors = [
    [    0,    -1,   0,  -1,   0,     0,     0,    0,    0,    0, ],
    [   42,     0,  42,   0,  42,     0,     0,    0,    0,   42, ],
    [   24,    42,  24,  42,  24,    24,    42,   24,   42,   24, ],
    [   -2,    24,  -2,  24,  -2,    -2,    24,   -2,   24,   -2, ],
    [   -1,    -2,  -1,  -2,  -1,    -1,    -2,   -1,   -2,   -1, ],
  ]
  a._tv_in, a._tv_out = tv_in, tv_out
  a._ref_upblk_srcs_yosys = { 'upblk' : \
"""\
integer __loopvar__upblk_i;

always_comb begin : upblk
  for ( __loopvar__upblk_i = 0; __loopvar__upblk_i < 5; __loopvar__upblk_i = __loopvar__upblk_i + 1 ) begin
    if ( ( in_[__loopvar__upblk_i] != 32'd0 ) && ( ( __loopvar__upblk_i < 4 ) ? in_[__loopvar__upblk_i + 1] != 32'd0 : in_[4] != 32'd0 ) ) begin
      __tmpvar__upblk_tmpvar = in_[__loopvar__upblk_i];
    end
    else
      __tmpvar__upblk_tmpvar = 32'd0;
    out[__loopvar__upblk_i] = __tmpvar__upblk_tmpvar;
  end
end\
""" }
  do_test( a )
