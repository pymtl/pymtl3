from pymtl import *
from pclib.update import RegEn, Reg, Mux, ZeroComp, LTComp, Subtractor

from pclib.test   import TestSourceValRdy, TestSinkValRdy
from pclib.ifcs   import ValRdyBundle
from pclib.valrdy import valrdy_to_str

A_MUX_SEL_IN    = 0
A_MUX_SEL_SUB   = 1
A_MUX_SEL_B     = 2
A_MUX_SEL_X     = 0

B_MUX_SEL_A     = 0
B_MUX_SEL_IN    = 1
B_MUX_SEL_X     = 0

class GcdUnitCS( PortBundle ):

  def __init__( s ):
    s.a_mux_sel = ValuePort(Bits2)
    s.a_reg_en  = ValuePort(Bits1)
    s.b_mux_sel = ValuePort(Bits1)
    s.b_reg_en  = ValuePort(Bits1)
    s.is_b_zero = ValuePort(Bits1)
    s.is_a_lt_b = ValuePort(Bits1)

class GcdUnitDpath( UpdatesImpl ):

  def __init__( s ):

    s.req_msg_a = ValuePort(Bits32)
    s.req_msg_b = ValuePort(Bits32)
    s.resp_msg  = ValuePort(Bits32)
    s.cs        = GcdUnitCS()

    s.sub_out   = Wire(Bits32)

    s.a_reg = RegEn( Bits32 )
    s.a_reg.en |= s.cs.a_reg_en

    s.b_reg = RegEn( Bits32 )
    s.b_reg.en |= s.cs.b_reg_en

    s.a_mux = Mux( Bits32, 3 )
    s.a_reg.in_                |= s.a_mux.out
    s.a_mux.in_[A_MUX_SEL_IN]  |= s.req_msg_a
    s.a_mux.in_[A_MUX_SEL_SUB] |= s.sub_out
    s.a_mux.in_[A_MUX_SEL_B]   |= s.b_reg.out
    s.a_mux.sel                |= s.cs.a_mux_sel

    s.b_mux = Mux( Bits32, 2 )
    s.b_reg.in_               |= s.b_mux.out
    s.b_mux.in_[B_MUX_SEL_A]  |= s.a_reg.out
    s.b_mux.in_[B_MUX_SEL_IN] |= s.req_msg_b
    s.b_mux.sel               |= s.cs.b_mux_sel

    s.b_zcp = ZeroComp( Bits32 )
    s.b_zcp.in_    |= s.b_reg.out
    s.cs.is_b_zero |= s.b_zcp.out

    s.b_ltc = LTComp( Bits32 )
    s.b_ltc.in0    |= s.a_reg.out
    s.b_ltc.in1    |= s.b_reg.out
    s.cs.is_a_lt_b |= s.b_ltc.out

    s.b_sub = Subtractor( Bits32 )
    s.b_sub.in0 |= s.a_reg.out
    s.b_sub.in1 |= s.b_reg.out
    s.resp_msg  |= s.b_sub.out
    s.sub_out   |= s.b_sub.out

class GcdUnitCtrl( UpdatesImpl ):

  def __init__( s ):

    s.req_val  = ValuePort(Bits1)
    s.req_rdy  = ValuePort(Bits1)
    s.resp_val = ValuePort(Bits1)
    s.resp_rdy = ValuePort(Bits1)

    s.state = Reg( Bits2 )

    s.STATE_IDLE = Bits2( 0 )
    s.STATE_CALC = Bits2( 1 )
    s.STATE_DONE = Bits2( 2 )

    s.cs = GcdUnitCS()

    @s.update
    def state_transitions():

      curr_state = s.state.out

      if   curr_state == s.STATE_IDLE:
        if s.req_val and s.req_rdy:
          s.state.in_ = s.STATE_CALC

      elif curr_state == s.STATE_CALC:
        if not s.cs.is_a_lt_b and s.cs.is_b_zero:
          s.state.in_ = s.STATE_DONE

      elif curr_state == s.STATE_DONE:
        if s.resp_val and s.resp_rdy:
          s.state.in_ = s.STATE_IDLE

    @s.update
    def state_outputs():

      curr_state = s.state.out

      s.req_rdy   = Bits1( 0 )
      s.resp_val  = Bits1( 0 )
      s.cs.a_mux_sel = Bits2( 0 )
      s.cs.a_reg_en  = Bits1( 0 )
      s.cs.b_mux_sel = Bits1( 0 )
      s.cs.b_reg_en  = Bits1( 0 )

      # In IDLE state we simply wait for inputs to arrive and latch them

      if curr_state == s.STATE_IDLE:
        s.req_rdy  = Bits1( 1 )
        s.resp_val = Bits1( 0 )

        s.cs.a_mux_sel = Bits2( A_MUX_SEL_IN )
        s.cs.b_mux_sel = Bits1( B_MUX_SEL_IN )
        s.cs.a_reg_en  = Bits1( 1 )
        s.cs.b_reg_en  = Bits1( 1 )

      # In CALC state we iteratively swap/sub to calculate GCD

      elif curr_state == s.STATE_CALC:

        s.req_rdy  = Bits1( 0 )
        s.resp_val = Bits1( 0 )
        s.cs.a_mux_sel = Bits2( A_MUX_SEL_B ) if s.cs.is_a_lt_b else Bits2( A_MUX_SEL_SUB )
        s.cs.a_reg_en  = Bits1( 1 )
        s.cs.b_mux_sel = Bits1( B_MUX_SEL_A )
        s.cs.b_reg_en  = s.cs.is_a_lt_b

      # In DONE state we simply wait for output transaction to occur

      elif curr_state == s.STATE_DONE:
        s.req_rdy   = Bits1( 0 )
        s.resp_val  = Bits1( 1 )
        s.cs.a_mux_sel = Bits2( A_MUX_SEL_X )
        s.cs.b_mux_sel = Bits1( B_MUX_SEL_X )
        s.cs.a_reg_en  = Bits1( 0 )
        s.cs.b_reg_en  = Bits1( 0 )

class GcdUnit( UpdatesImpl ):

  def __init__( s ):

    s.req  = ValRdyBundle( Bits64 )
    s.resp = ValRdyBundle( Bits32 )

    s.dpath = GcdUnitDpath()
    s.ctrl  = GcdUnitCtrl()

    s.ctrl.req_val    |= s.req.val
    s.req.rdy         |= s.ctrl.req_rdy
    s.dpath.req_msg_a |= s.req.msg[32:64]
    s.dpath.req_msg_b |= s.req.msg[0:32]

    s.resp.val        |= s.ctrl.resp_val
    s.ctrl.resp_rdy   |= s.resp.rdy
    s.resp.msg        |= s.dpath.resp_msg

    s.dpath.cs |= s.ctrl.cs

  def line_trace( s ):
    return s.dpath.a_reg.line_trace() + s.dpath.b_reg.line_trace()

class TestHarness( UpdatesImpl ):

  def __init__( s ):

    s.src  = TestSourceValRdy( Bits64, [ Bits64(0x3c00000023),
                                         Bits64(0x1200000018),
                                         Bits64(0xc30000002b) ])
    s.gcd  = GcdUnit()
    s.sink = TestSinkValRdy( Bits32, [ Bits32(5), Bits32(6), Bits32(1) ] )

    s.gcd.req  |= s.src.out
    s.sink.in_ |= s.gcd.resp

  def done( s ):
    return s.src.done() and s.sink.done()

  def line_trace( s ):
    return s.src.line_trace()+" >>> "+s.gcd.line_trace()+" >>> "+s.sink.line_trace()

if __name__ == "__main__":
  A = TestHarness()
  A.elaborate()
  A.print_schedule()

  while not A.done():
    A.cycle()
    print A.line_trace()
