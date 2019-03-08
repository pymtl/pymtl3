#=========================================================================
# design_test.py
#=========================================================================
# This file includes directed tests cases for the translation pass. Test
# cases are mainly simple PRTL designs.
# 
# Author : Peitian Pan
# Date   : Feb 21, 2019

import pytest

from pymtl                             import *
from pymtl.passes.SystemVerilog        import TranslationPass, SimpleImportPass
from pymtl.passes.utility.test_utility import do_test, run_translation_test

def local_do_test( m ):

  def run_sv_translation_test( m, test_vector ):
    run_translation_test( m, test_vector, TranslationPass, SimpleImportPass )

  run_sv_translation_test( m, m._test_vector )

#-------------------------------------------------------------------------
# test_adder
#-------------------------------------------------------------------------

def test_adder( do_test ):
  from pclib.rtl import Adder

  m = Adder( Bits32 )
  m._test_vector = [
              'in0              in1                   *out',
    [      Bits32,          Bits32,                Bits32 ],

    [           0,               1,                     1 ],
    [           2,               3,                     5 ],
    [  Bits32(-1),               0,            Bits32(-1) ],
    [  Bits32(-1),      Bits32(-2),            Bits32(-3) ],
    [  2147483647,               1,   Bits32(-2147483648) ],
  ]
  do_test( m )

#-------------------------------------------------------------------------
# test_mux
#-------------------------------------------------------------------------

def test_mux( do_test ):
  from pclib.rtl import Mux

  m = Mux( Bits32, 3 )
  m._test_vector = [
       'in_[0]  in_[1]  in_[2]   sel     *out', 
    [ Bits32,  Bits32, Bits32, Bits2, Bits32 ],

    [      0,       1,      2,   0,       0  ],
    [      1,       2,      3,   1,       2  ],
    [      7,       8,      9,   2,       9  ],
  ]
  do_test( m )

#-------------------------------------------------------------------------
# test_bypass_queue
#-------------------------------------------------------------------------

@pytest.mark.xfail( reason = 'Needs Interface support' )
def test_bypass_queue( do_test ):
  from pclib.rtl.valrdy_queues import BypassQueue1RTL

  m = BypassQueue1RTL( Bits32 )
  m._test_vector = [
  ]
  do_test( m )

#-------------------------------------------------------------------------
# test_regincr
#-------------------------------------------------------------------------

def test_regincr( do_test ):
  class RegIncr( RTLComponent ):
    def construct( s, width ):
      s.in_     = InVPort   ( width )
      s.out     = OutVPort  ( width )
      s.reg_out = Wire      ( width )

      @s.update_on_edge
      def update_reg():
        if s.reset:
          # FIXME: assignment like this should be okay...
          # s.reg_out = 0
          s.reg_out = width( 0 )
        else:
          s.reg_out = s.in_

      @s.update
      def update_inc():
        s.out = s.reg_out + width( 1 )

  m = RegIncr( Bits8 )
  m._test_vector = [
              'in_              *out',
    [        Bits8,           Bits8 ],

    [            4,             '*' ], # 1
    [            3,               5 ],
    [            9,               4 ],
    [    Bits8(-1),              10 ],
    [            0,        Bits8(0) ],
  ]
  do_test( m )

#-------------------------------------------------------------------------
# test_regincr_2stage
#-------------------------------------------------------------------------

def test_regincr_2stage( do_test ):
  class RegIncr( RTLComponent ):
    def construct( s, width ):
      s.in_     = InVPort   ( width )
      s.out     = OutVPort  ( width )
      s.reg_out = Wire      ( width )

      @s.update_on_edge
      def update_reg():
        if s.reset:
          s.reg_out = 0
        else:
          s.reg_out = s.in_

      @s.update
      def update_inc():
        s.out = s.reg_out + width( 1 )

  class RegIncr2( RTLComponent ):
    def construct( s, width ):
      s.in_     = InVPort   ( width )
      s.out     = OutVPort  ( width )

      s.reg1_out = Wire     ( width ) 

      s.reg_incr0 = RegIncr( width )( in_ = s.in_, out = s.reg1_out )
      s.reg_incr1 = RegIncr( width )( in_ = s.reg1_out, out = s.out )

  m = RegIncr2( Bits32 )
  m._test_vector = [
              'in_              *out',
    [        Bits32,           Bits32 ],

    [            4,             '*' ], # 2
    [            3,             '*' ], # 2
    [            3,               6 ],
    [            9,               5 ],
    [    Bits8(-1),               5 ],
    [            0,              11 ],
    [            0,     Bits32(257) ],
    [            0,               2 ],
    [            0,               2 ],
  ]
  do_test( m )

#-------------------------------------------------------------------------
# test_regincr_nstage
#-------------------------------------------------------------------------

def test_regincr_n_stage( do_test ):
  class RegIncr( RTLComponent ):
    def construct( s, width ):
      s.in_     = InVPort   ( width )
      s.out     = OutVPort  ( width )
      s.reg_out = Wire      ( width )

      @s.update_on_edge
      def update_reg():
        if s.reset:
          s.reg_out = 0
        else:
          s.reg_out = s.in_

      @s.update
      def update_inc():
        s.out = s.reg_out + width( 1 )

  class RegIncrN( RTLComponent ):
    def construct( s, width, nstages ):
      s.in_     = InVPort   ( width )
      s.out     = OutVPort  ( width )

      s.reg_out = [ Wire( width ) for x in xrange(nstages+1)]

      s.reg_incrs = [ RegIncr( width )( in_ = s.reg_out[x], out = s.reg_out[x+1]) 
        for x in xrange( nstages ) ]

      @s.update
      def in_update(): 
        s.reg_out[0] = s.in_

      @s.update
      def out_update():
        # FIXME: the error message here does not appear complete...
        # s.out = s.reg_incrs[ nstages ]
        s.out = s.reg_out[ nstages ]

  m = RegIncrN( Bits32, 5 )
  m._test_vector = [
              'in_              *out',
    [        Bits32,           Bits32 ],

    [            4,             '*' ], # 2
    [            3,             '*' ], # 3
    [            3,             '*' ], # 4
    [            9,             '*' ], # 5
    [    Bits8(-1),             '*' ], # 5
    [            0,               9 ],
    [            0,               8 ],
    [            0,               8 ],
    [            0,              14 ],
    [            0,             260 ],
    [            0,               5 ],
    [            0,               5 ],
  ]
  do_test( m )

#-------------------------------------------------------------------------
# test_sort
#-------------------------------------------------------------------------

def test_sort( do_test ):
  from pclib.rtl.registers import Reg, RegRst 

  class MinMaxUnit( RTLComponent ):
    def construct( s, width ):
      s.in0       = InVPort   ( width )
      s.in1       = InVPort   ( width )
      s.out_min   = OutVPort  ( width )
      s.out_max   = OutVPort  ( width )

      @s.update
      def output_update():
        if s.in0 < s.in1:
          s.out_min = s.in0
          s.out_max = s.in1
        else:
          s.out_min = s.in1
          s.out_max = s.in0

  class Sort( RTLComponent ):
    def construct( s, width ):
      s.in_val    = InVPort   ( Bits1 )
      s.out_val   = OutVPort  ( Bits1 )
      s.in_       = [ InVPort( width ) for x in xrange(4) ]
      s.out       = [ OutVPort( width ) for x in xrange(4) ]

      #-------------------------------------------------------------------
      # Stage S0 -> S1 pipeline registers
      #-------------------------------------------------------------------

      s.val_S0S1 = Wire( Bits1 )
      s.in_S0S1 = [ Wire( width ) for _ in xrange(4) ]

      @s.update_on_edge
      def pipe_reg_in_val_S0S1():
        if s.reset:
          s.val_S0S1 = Bits1( 0 )
        else:
          s.val_S0S1 = s.in_val

      @s.update_on_edge
      def pipe_reg_in_S0S1():
        for i in xrange(4):
          s.in_S0S1[i] = s.in_[i]

      #-------------------------------------------------------------------
      # Stage S1 combinational
      #-------------------------------------------------------------------

      s.mmu_up_S1 = MinMaxUnit( width )
      s.mmu_down_S1 = MinMaxUnit( width )

      s.connect( s.mmu_up_S1.in0, s.in_S0S1[0] )
      s.connect( s.mmu_up_S1.in1, s.in_S0S1[1] )
      s.connect( s.mmu_down_S1.in0, s.in_S0S1[2] )
      s.connect( s.mmu_down_S1.in1, s.in_S0S1[3] )

      #-------------------------------------------------------------------
      # Stage S1 -> S2 pipeline registers
      #-------------------------------------------------------------------

      s.val_S1S2 = Wire( Bits1 )
      s.in_S1S2 = [ Wire( width ) for _ in xrange(4) ]

      @s.update_on_edge
      def pipe_reg_in_val_S1S2():
        if s.reset:
          s.val_S1S2 = Bits1( 0 )
        else:
          s.val_S1S2 = s.val_S0S1

      @s.update_on_edge
      def pipe_reg_in_S1S2():
        s.in_S1S2[0] = s.mmu_up_S1.out_min
        s.in_S1S2[1] = s.mmu_up_S1.out_max
        s.in_S1S2[2] = s.mmu_down_S1.out_min
        s.in_S1S2[3] = s.mmu_down_S1.out_max

      #-------------------------------------------------------------------
      # Stage S2 combinational
      #-------------------------------------------------------------------

      s.mmu_up_S2 = MinMaxUnit( width )
      s.mmu_down_S2 = MinMaxUnit( width )

      s.connect( s.mmu_up_S2.in0, s.in_S1S2[0] )
      s.connect( s.mmu_up_S2.in1, s.in_S1S2[2] )
      s.connect( s.mmu_down_S2.in0, s.in_S1S2[1] )
      s.connect( s.mmu_down_S2.in1, s.in_S1S2[3] )

      #-------------------------------------------------------------------
      # Stage S2 -> S3 pipeline registers
      #-------------------------------------------------------------------

      s.val_S2S3 = Wire( Bits1 )
      s.in_S2S3 = [ Wire( width ) for _ in xrange(4) ]

      @s.update_on_edge
      def pipe_reg_in_val_S2S3():
        if s.reset:
          s.val_S2S3 = Bits1( 0 )
        else:
          s.val_S2S3 = s.val_S1S2

      @s.update_on_edge
      def pipe_reg_in_S2S3():
        s.in_S2S3[0] = s.mmu_up_S2.out_min
        s.in_S2S3[1] = s.mmu_up_S2.out_max
        s.in_S2S3[2] = s.mmu_down_S2.out_min
        s.in_S2S3[3] = s.mmu_down_S2.out_max

      #-------------------------------------------------------------------
      # Stage S3 combinational
      #-------------------------------------------------------------------

      s.mmu_S3 = MinMaxUnit( width )

      s.connect( s.mmu_S3.in0, s.in_S2S3[1] )
      s.connect( s.mmu_S3.in1, s.in_S2S3[2] )

      #-------------------------------------------------------------------
      # Output connections
      #-------------------------------------------------------------------

      s.connect( s.out_val, s.val_S2S3 )
      s.connect( s.in_S2S3[0], s.out[0] )
      s.connect( s.mmu_S3.out_min, s.out[1] )
      s.connect( s.mmu_S3.out_max, s.out[2] )
      s.connect( s.in_S2S3[3], s.out[3] )

  m = Sort( Bits32 )
  m._test_vector = [
    'in_val in_[0] in_[1] in_[2] in_[3] *out_val *out[0] *out[1] *out[2] *out[3]',
    [ Bits1 ] + [ Bits32 ] * 4 + [ Bits1 ] + [ Bits32 ] * 4,

    [ Bits1(1), Bits32(4), Bits32(3), Bits32(2), Bits32(1) ] +\
      [ '*' ] * 5,
    [ Bits1(1), Bits32(4), Bits32(3), Bits32(2), Bits32(1) ] +\
      [ '*' ] * 5,
    [ Bits1(1), Bits32(4), Bits32(3), Bits32(2), Bits32(1) ] +\
      [ '*' ] * 5,
    [ Bits1(1), Bits32(4), Bits32(3), Bits32(2), Bits32(1) ] +\
      [ Bits1(1), Bits32(1), Bits32(2), Bits32(3), Bits32(4) ],
    [ Bits1(1), Bits32(4), Bits32(3), Bits32(2), Bits32(1) ] +\
      [ Bits1(1), Bits32(1), Bits32(2), Bits32(3), Bits32(4) ],
  ]
  do_test( m )

#-------------------------------------------------------------------------
# test_gcd
#-------------------------------------------------------------------------
# Code from pymtl-v3-design repo

@pytest.mark.xfail( reason = 'Needs interface translation support' )
def test_gcd( do_test ):
  from pclib.rtl import RegEn, Reg, Mux, ZeroComp, LTComp, Subtractor

  A_MUX_SEL_IN  = 0
  A_MUX_SEL_SUB = 1
  A_MUX_SEL_B   = 2
  A_MUX_SEL_X   = 0
  B_MUX_SEL_A   = 0
  B_MUX_SEL_IN  = 1
  B_MUX_SEL_X   = 0

  class GcdUnitDpath( RTLComponent ):
    def construct( s ):
      s.req_msg_a = InVPort( Bits16 )
      s.req_msg_b = InVPort( Bits16 )
      s.resp_msg  = OutVPort( Bits16 )
      s.a_mux_sel = InVPort( Bits2 )
      s.a_reg_en  = InVPort( Bits1 )
      s.b_mux_sel = InVPort( Bits1 )
      s.b_reg_en  = InVPort( Bits1 )
      s.is_b_zero = OutVPort( Bits1 )
      s.is_a_lt_b = OutVPort( Bits1 )

      s.sub_out = Wire( Bits16 )

      s.a_reg = RegEn( Bits16 )( en = s.a_reg_en )
      s.b_reg = RegEn( Bits16 )( en = s.b_reg_en )

      s.a_mux = Mux( Bits16, 3 )(
        out = s.a_reg.in_,
        in_ = {
          A_MUX_SEL_IN  : s.req_msg_a,
          A_MUX_SEL_SUB : s.sub_out,
          A_MUX_SEL_B   : s.b_reg.out
        },
        sel = s.a_mux_sel,
      )

      s.b_mux = Mux( Bits16, 2 )(
        out = s.b_reg.in_,
        in_ = {
          B_MUX_SEL_A   : s.a_reg.out,
          B_MUX_SEL_IN  : s.req_msg_b,
        },
        sel = s.b_mux_sel,
      )

      s.b_zcp = ZeroComp( Bits16 )( in_ = s.b_reg.out, out = s.is_b_zero )
      s.b_ltc = LTComp( Bits16 )(
        in0 = s.a_reg.out,
        in1 = s.b_reg.out,
        out = s.is_a_lt_b,
      )
      s.b_sub = Subtractor( Bits16 )(
        in0 = s.a_reg.out,
        in1 = s.b_reg.out,
        out = ( s.resp_msg, s.sub_out ),
      )

  class GcdUnitCtrl( RTLComponent ):
    def construct( s ):
      s.req_val  = InVPort( Bits1 )
      s.req_rdy  = OutVPort( Bits1 )
      s.resp_val = OutVPort( Bits1 )
      s.resp_rdy = InVPort( Bits1 )

      s.state = Reg( Bits2 )

      s.a_mux_sel = OutVPort( Bits2 )
      s.a_reg_en  = OutVPort( Bits1 )
      s.b_mux_sel = OutVPort( Bits1 )
      s.b_reg_en  = OutVPort( Bits1 )
      s.is_b_zero = InVPort( Bits1 )
      s.is_a_lt_b = InVPort( Bits1 )

      s.IDLE = Bits2( 0 )
      s.CALC = Bits2( 1 )
      s.DONE = Bits2( 2 )

      @s.update
      def state_transitions():
        s.state.in_ = s.state.out
        if s.state.out == s.IDLE:
          if s.req_val and s.req_rdy:
            s.state.in_ = s.CALC
        elif s.state.out == s.CALC:
          if not s.is_a_lt_b and s.is_b_zero:
            s.state.in_ = s.DONE
        elif s.state.out == s.DONE:
          if s.resp_val and s.resp_rdy:
            s.state.in_ = s.IDLE

      @s.update
      def state_outputs():

        s.req_rdy   = Bits1( 0 )
        s.resp_val  = Bits1( 0 )
        s.a_mux_sel = Bits2( 0 )
        s.a_reg_en  = Bits1( 0 )
        s.b_mux_sel = Bits1( 0 )
        s.b_reg_en  = Bits1( 0 )

        # In IDLE state we simply wait for inputs to arrive and latch them

        if s.state.out == s.IDLE:
          s.req_rdy  = Bits1( 1 )
          s.resp_val = Bits1( 0 )

          s.a_mux_sel = Bits2( A_MUX_SEL_IN )
          s.b_mux_sel = Bits1( B_MUX_SEL_IN )
          s.a_reg_en  = Bits1( 1 )
          s.b_reg_en  = Bits1( 1 )

        # In CALC state we iteratively swap/sub to calculate GCD

        elif s.state.out == s.CALC:

          s.req_rdy  = Bits1( 0 )
          s.resp_val = Bits1( 0 )
          s.a_mux_sel = Bits2( A_MUX_SEL_B ) if s.is_a_lt_b else Bits2( A_MUX_SEL_SUB )
          s.a_reg_en  = Bits1( 1 )
          s.b_mux_sel = Bits1( B_MUX_SEL_A )
          s.b_reg_en  = s.is_a_lt_b

        # In DONE state we simply wait for output transaction to occur

        elif s.state.out == s.DONE:
          s.req_rdy   = Bits1( 0 )
          s.resp_val  = Bits1( 1 )
          s.a_mux_sel = Bits2( A_MUX_SEL_X )
          s.b_mux_sel = Bits1( B_MUX_SEL_X )
          s.a_reg_en  = Bits1( 0 )
          s.b_reg_en  = Bits1( 0 )

  class GcdUnit( RTLComponent ):

    def construct( s ):

      s.req  = InValRdyIfc ( Bits32 )
      s.resp = OutValRdyIfc( Bits16 )

      s.dpath = GcdUnitDpath()(
        req_msg_a = s.req.msg[16:32],
        req_msg_b = s.req.msg[0:16],
        resp_msg  = s.resp.msg,
      )

      s.ctrl  = GcdUnitCtrl()(
        req_val  = s.req.val,
        req_rdy  = s.req.rdy,
        resp_val = s.resp.val,
        resp_rdy = s.resp.rdy,
        a_mux_sel = s.dpath.a_mux_sel,
        a_reg_en  = s.dpath.a_reg_en,
        b_mux_sel = s.dpath.b_mux_sel,
        b_reg_en  = s.dpath.b_reg_en,
        is_b_zero = s.dpath.is_b_zero,
        is_a_lt_b = s.dpath.is_a_lt_b,
      )

    def line_trace( s ):
      return "{} >>> {}{} >>> {}".format( s.req.line_trace(),
              s.dpath.a_reg.line_trace(), s.dpath.b_reg.line_trace(),
              s.resp.line_trace() )

  m = GcdUnit()
  m._test_vector = [
  ]
  do_test( m )
