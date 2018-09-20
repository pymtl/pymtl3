from pymtl import *
from pclib.rtl import Adder, Subtractor, Mux, BypassQueue1RTL, ZeroComp
from pymtl.passes.SystemVerilogUpblkTranslationPass import SystemVerilogTranslationPass

def test_adder():
  m = Adder( Bits32 )
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_wrapped_noconnect_adder():

  class Adder_wrap_noc( RTLComponent ):

    def construct( s ):
      s.in_  = InVPort( Bits32 )
      s.out  = OutVPort( Bits32 )

      s.adder = Adder( Bits32 )

      @s.update
      def up_in():
        s.adder.in0 = s.adder.in1 = s.in_

      @s.update
      def up_out():
        s.out = s.adder.out

  m = Adder_wrap_noc()
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_wrapped_noconnect_wire_adder():

  class Adder_wrap_wire( RTLComponent ):

    def construct( s ):
      s.in_  = InVPort( Bits32 )
      s.out  = OutVPort( Bits32 )

      s.wire = Wire( Bits32 )

      s.adder = Adder( Bits32 )

      @s.update
      def up_in():
        s.wire = s.in_

      @s.update
      def up_wire():
        s.adder.in0 = s.adder.in1 = s.wire

      @s.update
      def up_out():
        s.out = s.adder.out

  m = Adder_wrap_wire()
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_wrapped_noconnect_slice_adder():

  class Adder_wrap_noc_slice( RTLComponent ):

    def construct( s ):
      s.in_  = InVPort( Bits31 )
      s.out  = OutVPort( Bits32 )

      s.adder = Adder( Bits32 )

      @s.update
      def up_in():
        s.adder.in0[0:31] = s.in_
        s.adder.in1[0:31] = s.in_

      @s.update
      def up_out():
        s.out = s.adder.out

  m = Adder_wrap_noc_slice()
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_wrapped_connect_adder():

  class Adder_wrap_con( RTLComponent ):

    def construct( s ):
      s.in_  = InVPort( Bits32 )
      s.out  = OutVPort( Bits32 )

      s.adder = Adder( Bits32 )( in0 = s.in_, in1 = s.in_, out = s.out )

  m = Adder_wrap_con()
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_wrapped_connect_wire_adder():

  class Adder_wrap_con_wire( RTLComponent ):

    def construct( s ):
      s.in_  = InVPort( Bits32 )
      s.out  = OutVPort( Bits32 )

      s.wire = Wire( Bits32 )

      s.adder = Adder( Bits32 )( in0 = s.in_, in1 = s.in_, out = s.wire )

      s.connect( s.wire, s.out )

  m = Adder_wrap_con_wire()
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_wrapped_connect_two_child_modules_wire():

  class Adder_wrap_child_wire( RTLComponent ):

    def construct( s ):
      s.in0  = InVPort( Bits32 )
      s.in1  = InVPort( Bits32 )
      s.in2  = InVPort( Bits32 )
      s.out  = OutVPort( Bits32 )

      s.tmp_in0 = Wire( Bits32 )
      s.tmp_out = Wire( Bits32 )

      s.connect( s.tmp_in0, s.in0 )
      s.connect( s.tmp_out, s.out )

      s.add = Adder( Bits32 )( in0 = s.tmp_in0, in1 = s.in1 )
      s.sub = Subtractor( Bits32 )( in0 = s.add.out, in1 = s.in2, out = s.tmp_out )

  m = Adder_wrap_child_wire()
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_mux():
  m = Mux( Bits32, 3 )
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_bypass_queue():
  m = BypassQueue1RTL( Bits32 )
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_multiple_if():

  class Foo_mul_if( RTLComponent ):
    def construct( s ):
      s.in_  = InVPort( Bits2 )
      s.out  = OutVPort( Bits2 )

      @s.update
      def up_if():
        if   s.in_ == ~s.in_:         s.out = s.in_
        elif s.in_ == s.in_ & s.in_:  s.out = ~s.in_
        elif s.in_ == s.in_ | s.in_:
          s.out = s.in_
          s.out = s.in_
          s.out = s.in_
        else:                         s.out = s.in_ + s.in_

  m = Foo_mul_if()
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_multiple_if_two_level():

  class Foo( RTLComponent ):
    def construct( s ):
      s.in_  = InVPort( Bits2 )
      s.out  = OutVPort( Bits2 )

      @s.update
      def up_if():
        if   s.in_ == ~s.in_:         s.out = s.in_
        elif s.in_ == s.in_ & s.in_:  s.out = ~s.in_
        elif s.in_ == s.in_ | s.in_:
          s.out = s.in_
          s.out = s.in_
          s.out = s.in_
        else:                         s.out = s.in_ + s.in_

  class Bar_if_2( RTLComponent ):
    def construct( s ):
      s.x = Foo()
      s.y = Wire( Bits2 )
      s.z = Wire( Bits2 )

      @s.update
      def up_y():
        s.y = s.x.out

      @s.update
      def up_z():
        s.x.in_ = s.z

  m = Bar_if_2()
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_bits_type():

  class Foo_bits( RTLComponent ):
    def construct( s ):
      s.in_  = InVPort( Bits2 )
      s.out  = OutVPort( Bits4 )

      @s.update
      def up_if():
        if   s.in_ == Bits2( 0 ):
          s.out = Bits4( 1 ) | Bits4( 2 )
          s.out = Bits4( 8 )
        else:
          s.out = Bits1( 0 )
          s.out = Bits4( 1 )

  m = Foo_bits()
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_bits_type_in_self():

  class Foo_bits_s( RTLComponent ):
    def construct( s ):
      nbits = 2

      s.Tin  = mk_bits( nbits )
      s.in_  = InVPort( s.Tin )
      s.Tout = mk_bits( 1<<nbits )
      s.out  = OutVPort( s.Tout )

      @s.update
      def up_if():
        if   s.in_ == Bits123( 0 ):
          s.out = s.Tout( 1 ) | s.Tout( 1 )
          s.out = s.Tout( 8 )
        else:
          s.out = s.Tout( 0 )

  m = Foo_bits_s()
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_bits_closure():

  class Foo_bits_closure( RTLComponent ):
    def construct( s ):
      nbits = 2

      Tin   = mk_bits( nbits )
      s.in_ = InVPort( Tin )
      Tout  = mk_bits( 1<<nbits )
      s.out = OutVPort( Tout )

      @s.update
      def up_if():
        if   s.in_ == Bits123( 0 ):
          s.out = Tout( 1 ) | Tout( 1 )
          s.out = Tout( 8 )
        else:
          s.out = Tout( 0 )

  m = Foo_bits_closure()
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_bits_value_closure():

  class Foo_bits_value_closure( RTLComponent ):
    def construct( s ):
      nbits = 2

      s.Tin  = mk_bits( nbits )
      s.in_  = InVPort( s.Tin )
      s.Tout = mk_bits( 1<<nbits )
      s.out  = OutVPort( s.Tout )

      s.one = 1
      eight = 8

      @s.update
      def up_if():
        if   s.in_ == Bits123( 0 ):
          s.out = s.Tout( s.one ) | s.Tout( s.one )
          s.out = s.Tout( eight )
        else:
          s.out = s.Tout( 0 )

  m = Foo_bits_value_closure()
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_bits_val_and_call():

  class Foo_bits_val_call( RTLComponent ):
    def construct( s ):
      nbits = 2

      s.Tin  = mk_bits( nbits )
      s.in_  = InVPort( s.Tin )
      s.Tout = mk_bits( 1<<nbits )
      s.out  = OutVPort( s.Tout )

      @s.func
      def qnm( x ):
        s.out = x

      @s.update
      def up_if():

        if   s.in_ == s.Tin( 0 ):
          s.out = s.Tout( 1 ) | s.Tout( 1 )

        elif s.in_ == s.Tin( 1 ):
          s.out = s.Tout( 2 ) & s.Tout( 2 )
          s.out = ~s.Tout( 2 )

        elif s.in_ == s.Tin( 2 ):
          s.out = s.Tout( 4 ) < s.Tout( 3 )
          s.out = s.Tout( 4 ) if s.in_ == s.Tin( 2 ) else s.Tout( 5 )

        elif s.in_ == s.Tin( 3 ):
          s.out = s.Tout( 8 )

        else:
          s.out = s.Tout( 0 )
          qnm( s.Tout( 0 ) )

  m = Foo_bits_val_call()
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_regincr():

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

  m = RegIncr( Bits8 )
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_regincr2():

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
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_regincr_n():

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
        s.out = s.reg_incrs[ nstages ]

  m = RegIncrN( Bits32, 5 )
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_sort():

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

  class Reg( RTLComponent ):
    def construct( s, width ):
      s.in_       = InVPort     ( width )
      s.out       = OutVPort    ( width )

      @s.update_on_edge
      def output_update():
        s.out = s.in_

  class RegRst( RTLComponent ):
    def construct( s, width ):
      s.in_       = InVPort     ( width )
      s.out       = OutVPort    ( width )

      s.reset     = InVPort     ( Bits1 )

      @s.update_on_edge
      def output_update():
        if s.reset:
          s.out = 0
        else:
          s.out = s.in_

  class Sort( RTLComponent ):
    def construct( s, width ):
      s.in_val    = InVPort   ( Bits1 )
      s.out_val   = OutVPort  ( Bits1 )
      s.in_       = [ InVPort( width ) for x in xrange(4) ]
      s.out       = [ OutVPort( width ) for x in xrange(4) ]

      s.val_S0S1_out = Wire( Bits1 )
      s.val_S1S2_out = Wire( Bits1 )

      s.val_S0S1 = RegRst( Bits1 )( in_ = s.in_val, out = s.val_S0S1_out )
      s.elm_S0S1 = [ Reg( width )( in_ = s.in_[x] ) for x in xrange(4) ]

      s.minmax0_S1 = MinMaxUnit( width )(in0 = s.elm_S0S1[0].out, in1 = s.elm_S0S1[1].out)
      s.minmax1_S1 = MinMaxUnit( width )(in0 = s.elm_S0S1[2].out, in1 = s.elm_S0S1[3].out)

#      s.minmax_S1_tmp = [ s.minmax0_S1.out_min, s.minmax0_S1.out_max, 
#                          s.minmax1_S1.out_min, s.minmax1_S1.out_max ]
#      s.elm_S1S2 = [ Reg( width )( in_ = s.minmax_S1_tmp[x] ) for x in xrange(4) ]

      s.val_S1S2 = RegRst( Bits1 )( in_ = s.val_S0S1_out, out = s.val_S1S2_out )
      s.elm_S1S2 = [ Reg(width)(in_ = s.minmax0_S1.out_min), Reg(width)(in_ = s.minmax0_S1.out_max), 
                     Reg(width)(in_ = s.minmax1_S1.out_min), Reg(width)(in_ = s.minmax1_S1.out_max)]

      s.minmax0_S2 = MinMaxUnit( width )(in0 = s.elm_S1S2[0].out, in1 = s.elm_S1S2[2].out)
      s.minmax1_S2 = MinMaxUnit( width )(in0 = s.elm_S1S2[1].out, in1 = s.elm_S1S2[3].out)

#      s.minmax_S2_tmp = [ s.minmax0_S2.out_min, s.minmax0_S2.out_max, 
#                          s.minmax1_S2.out_min, s.minmax1_S2.out_max ]
#      s.elm_S2S3 = [ Reg( width )( in_ = s.minmax_S2_tmp[x] ) for x in xrange(4) ]

      s.val_S2S3 = RegRst( Bits1 )( in_ = s.val_S1S2_out, out = s.out_val )
      s.elm_S2S3 = [Reg(width)(in_ = s.minmax0_S2.out_min, out = s.out[0]), 
                    Reg(width)(in_ = s.minmax0_S2.out_max), 
                    Reg(width)(in_ = s.minmax1_S2.out_min), 
                    Reg(width)(in_ = s.minmax1_S2.out_max, out = s.out[3])]

      s.minmax_S3 = MinMaxUnit( width )(in0 = s.elm_S2S3[1].out, in1 = s.elm_S2S3[2].out, 
                                        out_min = s.out[1], out_max = s.out[2] )

#      @s.update
#      def output_update():
#        s.out[0] = s.elm_S2S3[0].out
#        s.out[3] = s.elm_S2S3[3].out

  m = Sort( Bits32 )
  m.elaborate()
  SystemVerilogTranslationPass()( m )

def test_gcd():

  #=========================================================================
  # Constants
  #=========================================================================

  A_MUX_SEL_NBITS = Bits1
  A_MUX_SEL_IN    = 0
  A_MUX_SEL_SUB   = 1
  A_MUX_SEL_X     = 0

  B_MUX_SEL_NBITS = Bits1
  B_MUX_SEL_IN    = 0
  B_MUX_SEL_SUB   = 1
  B_MUX_SEL_X     = 0

  O_MUX_SEL_NBITS = Bits1
  O_MUX_SEL_A     = 0
  O_MUX_SEL_B     = 1
  O_MUX_SEL_X     = 0

  S_MUX_SEL_NBITS = Bits1
  S_MUX_SEL_AB    = 0
  S_MUX_SEL_BA    = 1
  S_MUX_SEL_X     = 0

  #=========================================================================
  # GCD Unit RTL Datapath
  #=========================================================================

  class GcdUnitDpathRTL( RTLComponent ):
    def construct( s ):
      #---------------------------------------------------------------------
      # Interface
      #---------------------------------------------------------------------

      s.req_msg_a  = InVPort  ( Bits16 )
      s.req_msg_b  = InVPort  ( Bits16 )
      s.resp_msg   = OutVPort ( Bits16 )

      # Control signals (ctrl -> dpath)

      s.a_mux_sel = InVPort  ( A_MUX_SEL_NBITS )
      s.a_reg_en  = InVPort  ( Bits1 )
      s.b_mux_sel = InVPort  ( B_MUX_SEL_NBITS )
      s.b_reg_en  = InVPort  ( Bits1 )
      s.o_mux_sel = InVPort  ( O_MUX_SEL_NBITS )
      s.s_mux_sel = InVPort  ( S_MUX_SEL_NBITS )

      # Status signals (dpath -> ctrl)

      s.is_a_zero = OutVPort ( Bits1 )
      s.is_b_zero = OutVPort ( Bits1 )
      s.is_a_lt_b = OutVPort ( Bits1 )

      #---------------------------------------------------------------------
      # Structural composition
      #---------------------------------------------------------------------

      # A mux

      s.sub_out   = Wire( Bits16 )

      con_helper_a_mux = {}

      con_helper_a_mux[ A_MUX_SEL_IN ] = s.req_msg_a
      con_helper_a_mux[ A_MUX_SEL_SUB ] = s.sub_out

      s.a_mux = Mux( Bits16, 2 )( sel = s.a_mux_sel, 
                                  # in_ = [ s.req_msg_a, s.sub_out ]
                                  # in_ = con_helper_a_mux.values()
                                  # in_[ A_MUX_SEL_IN ]   = s.req_msg_a, 
                                  # in_[ A_MUX_SEL_SUB ]  = s.sub_out     
                                  in_[ Bits1(0) ]   = s.req_msg_a, 
                                  in_[ Bits1(1) ]  = s.sub_out     
                                )
      # s.connect_pairs(
      #   m.sel,                  s.a_mux_sel,
      #   m.in_[ A_MUX_SEL_IN  ], s.req_msg_a,
      #   m.in_[ A_MUX_SEL_SUB ], s.sub_out,
      # )

      # A register

      s.a_reg = RegEn( Bits16 )( en = s.a_reg_en, in_ = s.a_mux.out )

      # s.a_reg = m = RegEn(16)
      # s.connect_pairs(
      #   m.en,  s.a_reg_en,
      #   m.in_, s.a_mux.out,
      # )

      # B mux

      con_helper_b_mux = {}

      con_helper_b_mux[ B_MUX_SEL_IN ] = s.req_msg_b
      con_helper_b_mux[ B_MUX_SEL_SUB ] = s.sub_out

      s.b_mux = Mux( Bits16, 2 )( sel = s.b_mux_sel,
                                  in_ = [ s.req_msg_b, s.sub_out ]
                                  # in_ = con_helper_b_mux.values()
                                  # in_[ B_MUX_SEL_IN ]   = s.req_msg_b,
                                  # in_[ B_MUX_SEL_SUB ]  = s.sub_out
                                )
      # s.connect_pairs(
      #   m.sel,                  s.b_mux_sel,
      #   m.in_[ B_MUX_SEL_IN  ], s.req_msg_b,
      #   m.in_[ B_MUX_SEL_SUB ], s.sub_out,
      # )

      # B register

      s.b_reg = RegEn( Bits16 )( en = s.b_reg_en, in_ = s.b_mux.out )

      # s.connect_pairs(
      #   m.en,  s.b_reg_en,
      #   m.in_, s.b_mux.out,
      #   m.out, s.b_reg_out,
      # )

      # O mux

      con_helper_o_mux = {}

      con_helper_o_mux[ O_MUX_SEL_A ] = s.a_reg.out
      con_helper_o_mux[ O_MUX_SEL_B ] = s.b_reg.out

      s.o_mux = Mux( Bits16, 2 )( sel = s.o_mux_sel, 
                                  in_ = [ s.a_reg.out, s.b_reg.out ]
                                  # in_ = con_helper_o_mux.values()
                                  # in_[ O_MUX_SEL_A ] = s.a_reg.out, 
                                  # in_[ O_MUX_SEL_B ] = s.b_reg.out
                                )

      # s.connect_pairs(
      #   m.sel,                 s.o_mux_sel,
      #   m.in_[ O_MUX_SEL_A  ], s.a_reg.out,
      #   m.in_[ O_MUX_SEL_B  ], s.b_reg.out,
      # )

      # S mux (minuend)

      con_helper_min_mux = {}

      con_helper_min_mux[ S_MUX_SEL_AB ] = s.a_reg.out
      con_helper_min_mux[ S_MUX_SEL_BA ] = s.b_reg.out

      s.minuend_mux = Mux( Bits16, 2 )( sel = s.s_mux_sel, 
                                        in_ = [ s.a_reg.out, s.b_reg.out ]
                                        # in_ = con_helper_min_mux.values()
                                        # in_[ S_MUX_SEL_AB ] = s.a_reg.out, 
                                        # in_[ S_MUX_SEL_BA ] = s.b_reg.out
                                      )

      # s.connect_pairs(
      #   m.sel,                  s.s_mux_sel,
      #   m.in_[ S_MUX_SEL_AB  ], s.a_reg.out,
      #   m.in_[ S_MUX_SEL_BA  ], s.b_reg.out,
      # )

      # S mux (subtrahend)

      con_helper_sub_mux = {}

      con_helper_sub_mux[ S_MUX_SEL_AB ] = s.b_reg.out
      con_helper_sub_mux[ S_MUX_SEL_BA ] = s.a_reg.out

      s.subtrahend_mux = Mux( Bits16, 2 )( sel = s.s_mux_sel, 
                                           in_ = [ s.b_reg.out, s.a_reg.out ]
                                           # in_ = con_helper_sub_mux.values()
                                           # in_[ S_MUX_SEL_AB ] = s.b_reg.out,
                                           # in_[ S_MUX_SEL_BA ] = s.a_reg.out
                                         )

      # s.connect_pairs(
      #   m.sel,                  s.s_mux_sel,
      #   m.in_[ S_MUX_SEL_AB  ], s.b_reg.out,
      #   m.in_[ S_MUX_SEL_BA  ], s.a_reg.out,
      # )

      # A zero compare

      s.a_zero = ZeroComp( Bits16 )( in_ = s.a_reg.out, out = s.is_a_zero )

      # s.connect_pairs(
      #   m.in_, s.a_reg.out,
      #   m.out, s.is_a_zero,
      # )

      # B zero compare

      s.b_zero = ZeroComp( Bits16 )( in_ = s.b_reg.out, out = s.is_b_zero )

      # s.connect_pairs(
      #   m.in_, s.b_reg.out,
      #   m.out, s.is_b_zero,
      # )

      # Less-than comparator

      s.a_lt_b = LTComp( Bits16 )( in0 = s.a_reg.out, in1 = s.b_reg.out, out = s.is_a_lt_b )

      # s.connect_pairs(
      #   m.in0, s.a_reg.out,
      #   m.in1, s.b_reg.out,
      #   m.out, s.is_a_lt_b
      # )

      # Subtractor

      s.sub = Subtractor( Bits16 )( in0 = s.minuend_mux.out, in1 = s.subtrahend_mux.out, 
                                    out = s.sub_out
                                  )

      # s.connect_pairs(
      #   m.in0, s.minuend_mux.out, 
      #   m.in1, s.subtrahend_mux.out,
      #   m.out, s.sub_out,
      # )

      # connect to output port

      @s.update
      def output_update():
        s.resp_msg = s.o_mux.out

      # s.connect( s.o_mux.out, s.resp_msg )

  #=========================================================================
  # GCD Unit RTL Control
  #=========================================================================

  class GcdUnitCtrlRTL( RTLComponent ):
    def construct( s ):
      #---------------------------------------------------------------------
      # Interface
      #---------------------------------------------------------------------

      s.req_val    = InVPort  ( Bits1 )
      s.req_rdy    = OutVPort ( Bits1 )

      s.resp_val   = OutVPort ( Bits1 )
      s.resp_rdy   = InVPort  ( Bits1 )

      # Control signals (ctrl -> dpath)

      s.a_mux_sel = OutVPort ( A_MUX_SEL_NBITS )
      s.a_reg_en  = OutVPort ( Bits1 )
      s.b_mux_sel = OutVPort ( B_MUX_SEL_NBITS )
      s.b_reg_en  = OutVPort ( Bits1 )
      # select the output: is it reg_a or reg_b?
      s.o_mux_sel = OutVPort ( O_MUX_SEL_NBITS )
      # select minuend and subtrahend
      s.s_mux_sel = OutVPort ( S_MUX_SEL_NBITS )

      # Status signals (dpath -> ctrl)

      s.is_a_zero = InVPort  ( Bits1 )
      s.is_b_zero = InVPort  ( Bits1 )
      s.is_a_lt_b = InVPort  ( Bits1 )

      # State element

      s.STATE_IDLE = Bits2( 0 )
      s.STATE_CALC = Bits2( 1 )
      s.STATE_DONE = Bits2( 2 )

      s.state = RegRst( Bits2, reset_value = s.STATE_IDLE )

      #---------------------------------------------------------------------
      # State Transition Logic
      #---------------------------------------------------------------------

      # flag indicating whether the computation is done
      s.is_finished   = Wire( Bits1 )

      @s.update
      def assign_is_finished():
        s.is_finished = s.is_a_zero or s.is_b_zero

      @s.update
      def state_transitions():

        curr_state = s.state.out
        next_state = s.state.out

        # Transistions out of IDLE state

        if ( curr_state == s.STATE_IDLE ):
          if ( s.req_val and s.req_rdy ):
            next_state = s.STATE_CALC

        # Transistions out of CALC state

        if ( curr_state == s.STATE_CALC ):
          if ( s.is_finished and s.resp_rdy and not s.req_val ): 
            next_state = s.STATE_IDLE
          elif ( s.is_finished and not ( s.resp_rdy and s.req_val ) ):
            next_state = s.STATE_DONE

        # Transistions out of DONE state

        if ( curr_state == s.STATE_DONE ):
          if ( s.resp_val and s.resp_rdy ):
            next_state = s.STATE_IDLE

        s.state.in_ = next_state

      #---------------------------------------------------------------------
      # State Output Logic
      #---------------------------------------------------------------------

      s.do_swap   =   Wire( Bits1 )
      s.do_sub    =   Wire( Bits1 )

      # compute sel of A_MUX
      s.a_mux_sel_value   =   Wire( A_MUX_SEL_NBITS )

      @s.update
      def a_mux_set_val_gen():
        if ( ~s.is_finished ):
          # do_swap
          if ( s.is_a_lt_b ): 
            s.a_mux_sel_value = A_MUX_SEL_X
          # do_sub
          else: 
            s.a_mux_sel_value = A_MUX_SEL_SUB
        else:
          # be ready to accept next input
          if ( s.resp_rdy ): 
            s.a_mux_sel_value = A_MUX_SEL_IN
          # req_rdy will be 0, so dont care 
          else:
            s.a_mux_sel_value = A_MUX_SEL_X

      # compute sel of B_MUX
      s.b_mux_sel_value   =   Wire( B_MUX_SEL_NBITS )

      @s.update
      def b_mux_set_val_gen():
        if ( ~s.is_finished ):
          # do_swap
          if ( s.is_a_lt_b ): 
            s.b_mux_sel_value = B_MUX_SEL_SUB
          # do_sub
          else: 
            # dont-care since reg_b will be disabled 
            s.b_mux_sel_value = B_MUX_SEL_X
        else:
          # be ready to accept next input
          if ( s.resp_rdy ): 
            s.b_mux_sel_value = B_MUX_SEL_IN
          # req_rdy will be 0, so dont care 
          else:
            s.b_mux_sel_value = B_MUX_SEL_X

      @s.update
      def state_outputs():

        current_state = s.state.out

        # In IDLE state we simply wait for inputs to arrive and latch them

        if current_state == s.STATE_IDLE:
          s.req_rdy   = 1
          s.resp_val  = 0
          s.a_mux_sel = A_MUX_SEL_IN
          s.a_reg_en  = 1
          s.b_mux_sel = B_MUX_SEL_IN
          s.b_reg_en  = 1
          # s.resp_val = 0 so the output of O_MUX will be ignored
          s.o_mux_sel = O_MUX_SEL_X
          # a.en = 0 and b.en = 0 so the output of S_MUX will be ignored
          s.s_mux_sel = S_MUX_SEL_X

        # In CALC state we iteratively swap/sub to calculate GCD

        elif current_state == s.STATE_CALC:

          s.do_swap   = s.is_a_lt_b
          s.do_sub    = ~s.is_b_zero

          s.req_rdy   = s.is_finished and s.resp_rdy
          s.resp_val  = s.is_finished

          # see combinational block for cases where we need enable signal
          s.a_mux_sel = s.a_mux_sel_value
          s.a_reg_en  = ( ~s.is_finished and ~s.do_swap ) or \
                              ( s.is_finished and s.resp_rdy )

          s.b_mux_sel = s.b_mux_sel_value
          s.b_reg_en  = ( ~s.is_finished and s.do_swap ) or \
                              ( s.is_finished and s.resp_rdy )

          # choose whichever is not zero as output
          s.o_mux_sel = O_MUX_SEL_A if s.is_b_zero else O_MUX_SEL_B
          # if a < b then perform b - a
          s.s_mux_sel = S_MUX_SEL_BA if s.do_swap else S_MUX_SEL_AB

        # In DONE state we simply wait for output transaction to occur

        elif current_state == s.STATE_DONE:
          s.req_rdy   = 0
          s.resp_val  = 1
          s.a_mux_sel = A_MUX_SEL_X
          s.a_reg_en  = 0
          s.b_mux_sel = B_MUX_SEL_X
          s.b_reg_en  = 0
          # choose whichever is not zero as output
          s.o_mux_sel = O_MUX_SEL_A if s.is_b_zero else O_MUX_SEL_B
          # a.en = 0 and b.en = 0 so the output of S_MUX will be ignored
          s.s_mux_sel = S_MUX_SEL_X

  #=========================================================================
  # GCD Unit RTL Model
  #=========================================================================

  class GcdUnitRTL( RTLComponent ):

    # Constructor

    def construct( s ):

      # Interface

      s.req_msg_a = InVPort     ( Bits16 )
      s.req_msg_b = InVPort     ( Bits16 )
      s.req_val   = InVPort     ( Bits1 )
      s.req_rdy   = InVPort     ( Bits1 )
      s.gcd_out   = OutVPort    ( Bits16 )
      s.resp_val  = OutVPort    ( Bits1 )
      s.resp_rdy  = InVPort     ( Bits1 )

      s.dpath = GcdUnitDpathRTL()( req_msg_a = s.req_msg_a, req_msg_b = s.req_msg_b, 
                                 resp_msg  = s.gcd_out
                               )
      s.ctrl  = GcdUnitCtrlRTL()(  req_val = s.req_val, req_rdy = s.req_rdy,
                                 resp_val = s.resp_val, resp_rdy = s.resp_rdy, 
                                 a_mux_sel = s.dpath.a_mux_sel, a_reg_en = s.dpath.a_reg_en, 
                                 b_mux_sel = s.dpath.b_mux_sel, b_reg_en = s.dpath.b_reg_en, 
                                 o_mux_sel = s.dpath.o_mux_sel, s_mux_sel = s.dapth.s_mux_sel,
                                 is_a_zero = s.dpath.is_a_zero, is_b_zero = s.dpath.is_b_zero,
                                 is_a_lt_b = s.dapth.is_a_lt_b
                              )
      
  m = GcdUnitRTL()
  m.elaborate()
  SystemVerilogTranslationPass()( m )
