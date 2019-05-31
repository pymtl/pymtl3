#=========================================================================
# SVBehavioralTranslatorL2_test.py
#=========================================================================
# Author : Peitian Pan
# Date   : May 28, 2019
"""Test the SystemVerilog translator implementation."""

from __future__ import absolute_import, division, print_function

from pymtl3.datatypes import Bits1, Bits32
from pymtl3.dsl import Component, InPort, OutPort
from pymtl3.passes.rtlir import BehavioralRTLIRGenPass, BehavioralRTLIRTypeCheckPass
from pymtl3.passes.rtlir.util.test_utility import do_test
from pymtl3.passes.sverilog.translation.behavioral.SVBehavioralTranslatorL2 import (
    BehavioralRTLIRToSVVisitorL2,
)


def local_do_test( m ):
  m.elaborate()
  m.apply( BehavioralRTLIRGenPass() )
  m.apply( BehavioralRTLIRTypeCheckPass() )

  visitor = BehavioralRTLIRToSVVisitorL2()
  upblks = m._pass_behavioral_rtlir_gen.rtlir_upblks
  m_all_upblks = m.get_update_blocks()
  for blk in m_all_upblks:
    upblk_src = visitor.enter( blk, upblks[blk] )
    upblk_src = "\n".join( upblk_src )
    assert upblk_src == m._ref_upblk_srcs[blk.__name__]

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
  do_test( a )

def test_for_xrange_upper( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange(2) ]
      s.out = [ OutPort( Bits32 ) for _ in xrange(2) ]
      @s.update
      def upblk():
        for i in xrange(2):
          s.out[i] = s.in_[i]
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  for ( int i = 0; i < 2; i += 1 )
    out[i] = in_[i];
end\
""" }
  do_test( a )

def test_for_range_upper( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange(2) ]
      s.out = [ OutPort( Bits32 ) for _ in xrange(2) ]
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
  do_test( a )

def test_for_xrange_lower_upper( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange(2) ]
      s.out = [ OutPort( Bits32 ) for _ in xrange(2) ]
      @s.update
      def upblk():
        for i in xrange(1, 2):
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
  do_test( a )

def test_for_range_lower_upper( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange(2) ]
      s.out = [ OutPort( Bits32 ) for _ in xrange(2) ]
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
  do_test( a )

def test_for_xrange_lower_upper_step( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange(5) ]
      s.out = [ OutPort( Bits32 ) for _ in xrange(5) ]
      @s.update
      def upblk():
        for i in xrange(0, 5, 2):
          s.out[i] = s.in_[i]
        for i in xrange(1, 5, 2):
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
  do_test( a )

def test_for_range_lower_upper_step( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange(5) ]
      s.out = [ OutPort( Bits32 ) for _ in xrange(5) ]
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
  do_test( a )

def test_if_exp_for( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange(5) ]
      s.out = [ OutPort( Bits32 ) for _ in xrange(5) ]
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
  do_test( a )

def test_if_exp_unary_op( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange(5) ]
      s.out = [ OutPort( Bits32 ) for _ in xrange(5) ]
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
  do_test( a )

def test_if_bool_op( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange(5) ]
      s.out = [ OutPort( Bits32 ) for _ in xrange(5) ]
      @s.update
      def upblk():
        for i in range(5):
          if s.in_[i] and (s.in_[i+1] if i<5 else s.in_[4]):
            s.out[i] = s.in_[i]
          else:
            s.out[i] = Bits32(0)
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  for ( int i = 0; i < 5; i += 1 )
    if ( in_[i] && ( ( i < 5 ) ? in_[i + 1] : in_[4] ) ) begin
      out[i] = in_[i];
    end
    else
      out[i] = 32'd0;
end\
""" }
  do_test( a )

def test_tmpvar( do_test ):
  class A( Component ):
    def construct( s ):
      s.in_ = [ InPort( Bits32 ) for _ in xrange(5) ]
      s.out = [ OutPort( Bits32 ) for _ in xrange(5) ]
      @s.update
      def upblk():
        for i in range(5):
          if s.in_[i] and (s.in_[i+1] if i<5 else s.in_[4]):
            tmpvar = s.in_[i]
          else:
            tmpvar = Bits32(0)
          s.out[i] = tmpvar
  a = A()
  a._ref_upblk_srcs = { 'upblk' : \
"""\
always_comb begin : upblk
  for ( int i = 0; i < 5; i += 1 ) begin
    if ( in_[i] && ( ( i < 5 ) ? in_[i + 1] : in_[4] ) ) begin
      upblk_tmpvar = in_[i];
    end
    else
      upblk_tmpvar = 32'd0;
    out[i] = upblk_tmpvar;
  end
end\
""" }
  do_test( a )
